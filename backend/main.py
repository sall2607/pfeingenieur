# main.py
"""
Backend Vision-RAG Recommande
Architecture : YOLO-World + ByteTrack + Gemini 2.5 Flash + Qdrant RAG
Auteur : Oulimata SALL - PFE ENICarthage 2026
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager   # ← AJOUTER CET IMPORT
from typing import List, Optional
import uvicorn
from loguru import logger
import time
from pathlib import Path
from pydantic import BaseModel

# Services
from services.video_processor import VideoProcessor
from services.yolo_service import YOLOService
from services.tracking_service import TrackingService
from services.gemini_service import GeminiService
from services.rag_service import RAGService
from services.validation_service import ValidationService

# Models
from models.equipment import Equipment, EquipmentResponse
from config import settings

import httpx
from uuid import UUID
from fastapi import HTTPException
import asyncio

class LoginRequest(BaseModel):
    email:    str
    password: str

class UserInfo(BaseModel):
    id:    str
    email: str
    name:  str
    role:  str

# ── Initialisation des services ─────────────────────────
video_processor    = VideoProcessor()
yolo_service       = YOLOService()
tracking_service   = TrackingService()
gemini_service     = GeminiService()
rag_service        = RAGService()
validation_service = ValidationService()

# Créer répertoires
Path("uploads").mkdir(exist_ok=True)
Path("outputs").mkdir(exist_ok=True)
Path("crops").mkdir(exist_ok=True)

N8N_WEBHOOK = "http://localhost:5678/webhook/sfm-analysis"

# ── Configuration Supabase ───────────────────────
SUPABASE_URL = "https://emjhbnszqikoxfydqnqz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVtamhibnN6cWlrb3hmeWRxbnF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ3MTk1MjksImV4cCI6MjEwMDI5NTUyOX0.ycJQZU46zrQhkvyMPS_lEacDvVOnqHpPtpuBAlK-WTI"

SUPABASE_HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
}

MAX_DAILY_ANALYSES = 3  # Quota journalier



# ── Lifespan (remplace @app.on_event) ───────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ─────────────────────────────────────────
    logger.info("Starting Vision-RAG API v2.0")
    rag_service._create_collections()

    # Charger le RAG automatiquement au démarrage
    try:
        logger.info("Auto-loading RAG index...")
        result = rag_service.build_index_from_scraping()
        logger.info(
            f"RAG ready: {result.get('count_text', 0)} entries"
        )
    except Exception as e:
        logger.warning(f"RAG auto-load failed (non-bloquant): {e}")

    logger.info("API demarree avec succes")

    yield  # ← L'application tourne ici

    # ── SHUTDOWN ─────────────────────────────────────────
    logger.info("API arretee")


async def send_to_n8n(data: dict):
    """Envoi asynchrone vers n8n — non bloquant"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                N8N_WEBHOOK,
                json=data,
                timeout=5.0
            )
        logger.info("✅ Résultats envoyés à n8n")
    except Exception as e:
        logger.warning(
            f"⚠️ n8n notification failed (non-bloquant): {e}"
        )

# ── Création de l'application avec lifespan ─────────────
app = FastAPI(
    title="Vision-RAG Equipment Detection API",
    description="Architecture recommandee : YOLO-World + ByteTrack + Gemini",
    version="2.0.0",
    lifespan=lifespan    # ← PASSER LE LIFESPAN ICI
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ───────────────────────────────────────────────

# ── Endpoint Login ───────────────────────────────
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Authentification utilisateur"""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{SUPABASE_URL}/rest/v1/users"
            f"?email=eq.{request.email}"
            f"&password=eq.{request.password}"
            f"&is_active=eq.true",
            headers=SUPABASE_HEADERS
        )

    users = r.json()
    if not users:
        raise HTTPException(
            status_code=401,
            detail="Email ou mot de passe incorrect"
        )

    user = users[0]
    logger.info(
        f"✅ Login: {user['email']} ({user['role']})"
    )
    return {
        "success": True,
        "user": {
            "id":    user["id"],
            "email": user["email"],
            "name":  user["name"],
            "role":  user["role"],
        }
    }

# ── Endpoint Quota ───────────────────────────────
@app.get("/api/quota/{user_id}")
async def get_quota(user_id: str):
    """Récupérer le quota journalier d'un utilisateur"""
    from datetime import date
    today = date.today().isoformat()

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{SUPABASE_URL}/rest/v1/daily_quotas"
            f"?user_id=eq.{user_id}"
            f"&date=eq.{today}",
            headers=SUPABASE_HEADERS
        )

    quotas = r.json()
    count  = quotas[0]["count"] if quotas else 0

    return {
        "user_id":   user_id,
        "date":      today,
        "count":     count,
        "max":       MAX_DAILY_ANALYSES,
        "remaining": max(0, MAX_DAILY_ANALYSES - count),
        "can_analyze": count < MAX_DAILY_ANALYSES
    }

# ── Incrémenter quota ────────────────────────────
async def increment_quota(user_id: str) -> int:
    if not user_id or user_id == "None":
        raise HTTPException(
            status_code=401,
            detail="Authentification requise pour gérer le quota"
        )

    try:
        UUID(str(user_id))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Identifiant utilisateur invalide"
        )
    """Incrémente et retourne le compteur journalier."""
    from datetime import date

    today = date.today().isoformat()
    endpoint = f"{SUPABASE_URL}/rest/v1/daily_quotas"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            endpoint,
            headers=SUPABASE_HEADERS,
            params={
                "user_id": f"eq.{user_id}",
                "date": f"eq.{today}",
                "select": "id,count",
                "limit": "1",
            },
        )

        if response.is_error:
            logger.error(
                f"Erreur lecture quota Supabase "
                f"({response.status_code}): {response.text}"
            )
            response.raise_for_status()

        existing = response.json()

        if not isinstance(existing, list):
            raise RuntimeError(
                f"Réponse Supabase inattendue : {existing}"
            )

        if existing:
            quota = existing[0]
            quota_id = quota["id"]
            new_count = int(quota.get("count") or 0) + 1

            response = await client.patch(
                endpoint,
                headers={
                    **SUPABASE_HEADERS,
                    "Prefer": "return=minimal",
                },
                params={"id": f"eq.{quota_id}"},
                json={"count": new_count},
            )
        else:
            new_count = 1

            response = await client.post(
                endpoint,
                headers={
                    **SUPABASE_HEADERS,
                    "Prefer": "return=minimal",
                },
                json={
                    "user_id": user_id,
                    "date": today,
                    "count": new_count,
                },
            )

        if response.is_error:
            logger.error(
                f"Erreur écriture quota Supabase "
                f"({response.status_code}): {response.text}"
            )
            response.raise_for_status()

    logger.info(
        f"📊 Quota incrémenté pour {user_id}: {new_count}/3"
    )
    return new_count

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "architecture": "YOLO-World + ByteTrack + Gemini 2.5 Flash",
        "author": "Oulimata SALL"
    }


@app.get("/api/health")
async def health_check():
    health_status = {
        "api":       "healthy",
        "yolo":      yolo_service.is_ready(),
        "gemini":    gemini_service.is_ready(),
        "qdrant":    rag_service.is_ready(),
        "timestamp": time.time()
    }

    all_healthy = all([
        health_status["yolo"],
        health_status["gemini"],
        health_status["qdrant"]
    ])

    status_code = 200 if all_healthy else 503
    return JSONResponse(content=health_status, status_code=status_code)


@app.post("/api/analyze-video", response_model=EquipmentResponse)
async def analyze_video(
    file: UploadFile = File(...),
    location: str = Form(...),
    max_keyframes: int = Form(20),
    user_id:       Optional[str] = Form(None)  # ← optionnel
):

    # Vérification quota seulement si user_id fourni
    if user_id:
        logger.info(f"🔍 Vérification quota pour {user_id}")
        from datetime import date
        today = date.today().isoformat()

        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{SUPABASE_URL}/rest/v1/daily_quotas"
                f"?user_id=eq.{user_id}"
                f"&date=eq.{today}",
                headers=SUPABASE_HEADERS
            )
        quotas = r.json()
        count  = quotas[0]["count"] if quotas else 0
        logger.info(f"📊 Quota actuel : {count}/{MAX_DAILY_ANALYSES}")


        if count >= MAX_DAILY_ANALYSES:
            raise HTTPException(
                status_code=429,
                detail=f"Quota journalier atteint "
                       f"({MAX_DAILY_ANALYSES} analyses/jour). "
                       f"Réessayez demain."
            )
    
    """
    Analyse une video et detecte les equipements

    Pipeline :
    1. Keyframe Selector (OpenCV)
    2. YOLO-World (zero-shot)
    3. ByteTrack (deduplication)
    4. RAG Qdrant (contexte AVANT Gemini)
    5. Gemini 2.5 Flash (analyse visuelle + JSON)
    6. Validation Pydantic V2
    """

    video_id   = f"video_{int(time.time() * 1000)}"
    start_time = time.time()
    video_path = f"uploads/{video_id}.mp4"

    logger.info(f"Starting video analysis: {video_id}")
    logger.info(f"   Location: {location}")
    logger.info(f"   Max keyframes: {max_keyframes}")

    try:
        # 1. Sauvegarder vidéo
        with open(video_path, "wb") as f:
            content = await file.read()
            f.write(content)
        logger.info(f"Video saved: {video_path} ({len(content)} bytes)")

        # 2. Extraction keyframes
        logger.info("Step 1/5: Extracting keyframes...")
        t0 = time.time()
        keyframes = video_processor.extract_keyframes(
            video_path, max_keyframes=max_keyframes
        )
        t1 = time.time()
        logger.info(f"Extracted {len(keyframes)} keyframes"
                    f" | ⏱️ Keyframes: {t1 - t0:.2f}s")

        # 3. YOLO-World detection
        logger.info("Step 2/5: YOLO-World detection...")
        detections     = yolo_service.detect_equipments(keyframes)
        t2 = time.time()
        total_detections = sum(len(d.boxes) for d in detections if d is not None)
        logger.info(f"YOLO detected {total_detections} objects across {len(keyframes)} frames"
                    f"| ⏱️ YOLO: {t2-t1:.2f}s")

        # 4. ByteTrack deduplication
        logger.info("Step 3/5: ByteTrack tracking + deduplication...")
        unique_crops = tracking_service.track_and_get_best_shots(
            keyframes, detections
        )
        t3 = time.time()
        logger.info(f"ByteTrack produced {len(unique_crops)} unique crops"
                    f" | ⏱️ ByteTrack: {t3-t2:.2f}s")

        # 5. Gemini (avec RAG intégré AVANT)
        logger.info("Step 4/5: Gemini 2.5 Flash (RAG + visual analysis)...")
        raw_equipments = gemini_service.analyze_crops_batch(
            unique_crops,
            location=location,
            rag_service=rag_service    # ← RAG avant Gemini
        )
        t4 = time.time()
        logger.info(f"Gemini generated {len(raw_equipments)} equipment candidates"
                    f" | ⏱️ RAG + Gemini: {t4-t3:.2f}s")

        # 6. Validation
        logger.info("Step 5/5: Validation + quality control...")
        validated_equipments = validation_service.validate_and_retry(
            raw_equipments,
            gemini_service=gemini_service,
            unique_crops=unique_crops
        )
        t5 = time.time()
        logger.info(
            f"⏱️ Validation: {t5-t4:.2f}s"
        )
        valid_count  = len([e for e in validated_equipments if not e.get("needsReview", False)])
        review_count = len([e for e in validated_equipments if e.get("needsReview", False)])
        logger.info(f"Validation complete: {valid_count} valid, {review_count} need review")


        logger.info(f"⏱️ TOTAL: {t5-t0:.2f}s")
        # Nettoyage fichiers temporaires
        Path(video_path).unlink(missing_ok=True)
        for crop in unique_crops:
            Path(crop["path"]).unlink(missing_ok=True)

        processing_time = time.time() - start_time
        logger.info(f"Analysis complete in {processing_time:.2f}s")
        logger.info(f"   Total: {len(validated_equipments)} | Valid: {valid_count} | Review: {review_count}")

        # Convertir en objets Pydantic
        equipment_objects = []
        for eq_data in validated_equipments:
            try:
                equipment_objects.append(Equipment(**eq_data))
            except Exception as e:
                logger.warning(f"Skipping invalid equipment: {e}")

 # BF9 + BF10 — Archivage et notification via n8n
        # APRÈS — utiliser model_dump avec mode json
        await send_to_n8n({
            "video_id":         video_id,
            "location":         location,
            "equipments_count": len(equipment_objects),
            "equipments": [
                eq.model_dump(mode='json')  # ← convertit datetime en string
                for eq in equipment_objects
            ],
            "processing_time":  processing_time,
            "metadata": {
                "keyframes_extracted": len(keyframes),
                "detections_total":    total_detections,
                "unique_crops":        len(unique_crops),
                "valid_equipments":    valid_count,
                "needs_review":        review_count,
            }
        })   

        # ── Incrémenter quota APRÈS succès ──────────
        await increment_quota(user_id)

        return EquipmentResponse(
            success=True,
            video_id=video_id,
            location=location,
            equipments_count=len(equipment_objects),
            equipments=equipment_objects,
            processing_time=processing_time,
            metadata={
                "keyframes_extracted": len(keyframes),
                "detections_total":    total_detections,
                "unique_crops":        len(unique_crops),
                "valid_equipments":    valid_count,
                "needs_review":        review_count
            }
        )

    except Exception as e:
        Path(video_path).unlink(missing_ok=True)
        logger.error(f"Error processing video: {e}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-no-rag")
async def analyze_no_rag(
    file: UploadFile = File(...),
    location: str = Form(...)
):
    """Analyse sans RAG — pour comparaison"""
    video_id   = f"norag_{int(time.time())}"
    video_path = f"uploads/{video_id}.mp4"

    with open(video_path, "wb") as f:
        content = await file.read()
        f.write(content)

    keyframes    = video_processor.extract_keyframes(
        video_path, max_keyframes=15)
    detections   = yolo_service.detect_equipments(keyframes)
    unique_crops = tracking_service.track_and_get_best_shots(
        keyframes, detections)

    # Gemini SANS contexte RAG
    raw = gemini_service.analyze_crops_batch(
        unique_crops,
        location=location,
        rag_service=None   # ← pas de RAG
    )

    Path(video_path).unlink(missing_ok=True)
    return {"equipments": raw, "rag_used": False}


@app.post("/api/build-rag-index")
async def build_rag_index():
    """Lance le web scraping + indexation Qdrant manuellement"""
    logger.info("Building RAG index from web scraping...")
    try:
        result = rag_service.build_index_from_scraping()

        text_count  = result.get("count_text",  result.get("count", 0))
        image_count = result.get("count_image", 0)
        time_taken  = result.get("time",        0)

        return {
            "success":      True,
            "text_indexed": text_count,
            "image_indexed": image_count,
            "time_seconds": time_taken,
            "message": (
                f"RAG index built. "
                f"{text_count} text entries, "
                f"{image_count} images."
            )
        }
    except Exception as e:
        logger.error(f"Build RAG index failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Statistiques de l'index RAG"""
    stats = rag_service.get_collection_stats()
    return {
        "qdrant_collection":  stats.get("collection_name"),
        "text_entries":       stats.get("text_entries",  0),
        "image_entries":      stats.get("image_entries", 0),
    }






if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
# services/rag_service.py
"""
RAG Service avec embeddings multimodaux (texte + images)
RAG précède Gemini dans le pipeline

CORRECTIONS APPORTÉES :
1. Qdrant persistant (path=...) au lieu de ":memory:" -> l'index ne
   disparaît plus au redémarrage du backend.
2. search_text enrichi avec les caractéristiques techniques pour un
   meilleur matching sémantique.
3. Vocabulaire CLIP zero-shot élargi (téléviseur, écran, four, etc.).
4. Vérification explicite au démarrage que l'index n'est pas vide,
   avec log d'alerte si c'est le cas (cause la plus probable de RAG
   "silencieux").
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct, SparseVectorParams
)
from sentence_transformers import SentenceTransformer
import torch
import clip  # OpenAI CLIP pour les images
from PIL import Image
import numpy as np
from typing import List, Dict, Optional, Tuple
from loguru import logger
import uuid
import json
from pathlib import Path
from config import settings
from services.scraping_service import ScrapingService


class RAGService:
    """
    Base RAG multimodale (texte + images) avec Qdrant
    Précède Gemini dans le pipeline pour lui fournir un contexte
    """

    TEXT_COLLECTION  = "equipment_text"
    IMAGE_COLLECTION = "equipment_images"
    TEXT_DIM  = 384   # all-MiniLM-L6-v2
    IMAGE_DIM = 512   # CLIP ViT-B/32

    # CORRECTION 3 : vocabulaire élargi pour le fallback zero-shot CLIP
    CANDIDATE_LABELS = [
        "air conditioner", "laptop computer", "desktop computer",
        "printer", "server", "refrigerator", "network switch",
        "light fixture", "television", "computer monitor",
        "microwave oven", "electric oven", "water heater",
        "electric fan", "router", "scanner", "photocopier",
        "coffee machine", "water dispenser", "electric kettle",
    ]

    def __init__(self):
        # CORRECTION 1 : stockage persistant sur disque au lieu de
        # ":memory:", qui effaçait tout l'index à chaque redémarrage.
        # Si tu utilises un vrai serveur Qdrant en prod, remplace par
        # QdrantClient(url=settings.QDRANT_URL).
        qdrant_path = getattr(settings, "QDRANT_PATH", "data/qdrant")
        self.client = QdrantClient(url=getattr(settings, "QDRANT_URL", "http://localhost:6333"))

        # Modèle texte
        self.text_embedder = SentenceTransformer(
            settings.EMBEDDING_MODEL
        )

        # Modèle image (CLIP)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.clip_model, self.clip_preprocess = clip.load(
            "ViT-B/32", device=self.device
        )

        logger.info("RAG Service initialized (text + image embeddings)")

        # Créer les collections
        self._create_collections()

        # CORRECTION 4 : vérifier immédiatement que l'index n'est pas
        # vide. Un RAG "sans effet" est très souvent un RAG qui
        # interroge une base vide.
        stats = self.get_collection_stats()
        if stats["text_entries"] == 0 and stats["image_entries"] == 0:
            logger.warning(
                "L'index RAG est VIDE (0 texte, 0 image). "
                "Le RAG ne pourra retourner aucun contexte tant que "
                "build_index_from_scraping() n'aura pas été appelé."
            )
        else:
            logger.info(f"Index RAG chargé : {stats}")

    def _create_collections(self):
        """Crée les deux collections Qdrant"""
        existing = [
            c.name for c in
            self.client.get_collections().collections
        ]

        if self.TEXT_COLLECTION not in existing:
            self.client.create_collection(
                collection_name=self.TEXT_COLLECTION,
                vectors_config=VectorParams(
                    size=self.TEXT_DIM,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Collection created: {self.TEXT_COLLECTION}")

        if self.IMAGE_COLLECTION not in existing:
            self.client.create_collection(
                collection_name=self.IMAGE_COLLECTION,
                vectors_config=VectorParams(
                    size=self.IMAGE_DIM,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Collection created: {self.IMAGE_COLLECTION}")

    # ─────────────────────────────────────────────────────
    # INDEXATION
    # ─────────────────────────────────────────────────────

    def build_index_from_scraping(self) -> Dict:
        """
        Lance le scraping puis indexe tout dans Qdrant
        """
        logger.info("Building RAG index from scraping...")
        start = __import__("time").time()

        scraper  = ScrapingService()
        all_data = scraper.run_full_scraping()

        indexed_text  = 0
        indexed_image = 0

        for item in all_data:
            if self._index_text(item):
                indexed_text += 1

            for img_path in item.get("images", []):
                if Path(img_path).exists():
                    if self._index_image(img_path, item):
                        indexed_image += 1

        elapsed = __import__("time").time() - start

        result = {
            "count_text":  indexed_text,
            "count_image": indexed_image,
            "time":        elapsed
        }

        logger.info(
            f"Index built: {indexed_text} text entries, "
            f"{indexed_image} images in {elapsed:.1f}s"
        )
        return result

    def _index_text(self, item: Dict) -> bool:
        """Indexe une fiche texte dans Qdrant"""
        try:
            # CORRECTION 2 : texte d'embedding enrichi avec les
            # caractéristiques techniques -> améliore le matching
            # sémantique quand la recherche part d'une requête
            # textuelle (fallback CLIP zero-shot notamment).
            parts = [
                item.get("brand", ""),
                item.get("model", ""),
                item.get("designation", ""),
                item.get("name", ""),
            ]
            if item.get("power"):
                parts.append(f"puissance {item['power']} W")
            if item.get("voltage"):
                parts.append(f"tension {item['voltage']} V")
            if item.get("cooling_capacity"):
                parts.append(f"capacité {item['cooling_capacity']} BTU")

            search_text = " ".join(p for p in parts if p).strip()

            vector = self.text_embedder.encode(
                search_text
            ).tolist()

            self.client.upsert(
                collection_name=self.TEXT_COLLECTION,
                points=[PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "name":             item.get("name"),
                        "brand":            item.get("brand"),
                        "model":            item.get("model"),
                        "designation":      item.get("designation"),
                        "power":            item.get("power"),
                        "voltage":          item.get("voltage"),
                        "cooling_capacity": item.get("cooling_capacity"),
                        "source_url":       item.get("source_url"),
                    }
                )]
            )
            return True

        except Exception as e:
            logger.warning(f"Text indexing failed: {e}")
            return False

    def _index_image(self, img_path: str, item: Dict) -> bool:
        """Indexe une image avec CLIP dans Qdrant"""
        try:
            image = self.clip_preprocess(
                Image.open(img_path).convert("RGB")
            ).unsqueeze(0).to(self.device)

            with torch.no_grad():
                features = self.clip_model.encode_image(image)
                features = features / features.norm(
                    dim=-1, keepdim=True
                )

            vector = features.cpu().numpy()[0].tolist()

            self.client.upsert(
                collection_name=self.IMAGE_COLLECTION,
                points=[PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "img_path":    img_path,
                        "brand":       item.get("brand"),
                        "model":       item.get("model"),
                        "designation": item.get("designation"),
                        "name":        item.get("name"),
                        "power":       item.get("power"),
                        "voltage":     item.get("voltage"),
                    }
                )]
            )
            return True

        except Exception as e:
            logger.warning(f"Image indexing failed for {img_path}: {e}")
            return False

    # ─────────────────────────────────────────────────────
    # RECHERCHE (utilisée AVANT Gemini)
    # ─────────────────────────────────────────────────────

    def search_by_image(
        self, crop_path: str, top_k: int = 3
    ) -> Tuple[List[Dict], List[str]]:
        """
        Recherche d'abord par image (CLIP),
        puis fallback sur recherche texte si rien trouvé
        """
        text_results = []
        image_paths  = []

        try:
            image = self.clip_preprocess(
                Image.open(crop_path).convert("RGB")
            ).unsqueeze(0).to(self.device)

            with torch.no_grad():
                features = self.clip_model.encode_image(image)
                features = features / features.norm(dim=-1, keepdim=True)

            vector = features.cpu().numpy()[0].tolist()

            image_hits = self.client.query_points(
                collection_name=self.IMAGE_COLLECTION,
                query=vector,
                limit=top_k
            ).points

            for hit in image_hits:
                if hit.score > 0.6:
                    text_results.append(hit.payload)
                    if hit.payload.get("img_path"):
                        image_paths.append(hit.payload["img_path"])

            if not text_results:
                logger.info("No image match — fallback to text search")
                text_results = self._search_by_clip_text(
                    crop_path, top_k
                )

        except Exception as e:
            logger.warning(f"RAG search failed: {e}")
            text_results = self._search_all_text(top_k)

        logger.info(
            f"RAG found {len(text_results)} matches "
            f"({len(image_paths)} images)"
        )
        return text_results, image_paths

    def _search_by_clip_text(
        self, crop_path: str, top_k: int = 3
    ) -> List[Dict]:
        """
        Utilise CLIP pour générer une description textuelle
        du crop, puis cherche dans la collection texte
        """
        try:
            image = self.clip_preprocess(
                Image.open(crop_path).convert("RGB")
            ).unsqueeze(0).to(self.device)

            # CORRECTION 3 : liste de labels centralisée et élargie
            candidate_labels = self.CANDIDATE_LABELS

            text_tokens = clip.tokenize(candidate_labels).to(self.device)

            with torch.no_grad():
                image_features = self.clip_model.encode_image(image)
                text_features  = self.clip_model.encode_text(text_tokens)

                image_features = image_features / image_features.norm(
                    dim=-1, keepdim=True
                )
                text_features = text_features / text_features.norm(
                    dim=-1, keepdim=True
                )

                similarities = (
                    100.0 * image_features @ text_features.T
                ).softmax(dim=-1)

                best_idx   = similarities[0].argmax().item()
                best_label = candidate_labels[best_idx]
                best_score = similarities[0][best_idx].item()

            logger.info(
                f"CLIP identified: '{best_label}' "
                f"(score: {best_score:.2f})"
            )

            query_vector = self.text_embedder.encode(best_label).tolist()

            hits = self.client.query_points(
                collection_name=self.TEXT_COLLECTION,
                query=query_vector,
                limit=3
            ).points

            return [
                hit.payload for hit in hits
                if hit.score > 0.1
            ]

        except Exception as e:
            logger.warning(f"CLIP text search failed: {e}")
            return []

    def _search_all_text(self, top_k: int = 3) -> List[Dict]:
        """Retourne les premières entrées si tout échoue"""
        try:
            vector = [0.0] * self.TEXT_DIM
            hits = self.client.query_points(
                collection_name=self.TEXT_COLLECTION,
                query=vector,
                limit=top_k
            ).points
            return [hit.payload for hit in hits]
        except Exception:
            return []

    def _search_text(
        self, brand: str, model: str, top_k: int = 1
    ) -> Optional[Dict]:
        """Recherche textuelle complémentaire"""
        try:
            query = f"{brand} {model}".strip()
            vector = self.text_embedder.encode(query).tolist()

            hits = self.client.query_points(
                collection_name=self.TEXT_COLLECTION,
                query=vector,
                limit=top_k
            ).points

            if hits and hits[0].score > 0.7:
                return hits[0].payload

        except Exception as e:
            logger.warning(f"Text search failed: {e}")

        return None

    def format_context_for_gemini(
        self,
        rag_results: List[Dict],
        similar_images: List[str]
    ) -> str:
        """
        Formate le contexte RAG pour l'injection dans le prompt Gemini.
        Ne mentionne plus les images similaires comme si elles allaient
        être envoyées (voir CORRECTION dans gemini_service.py : elles
        ne sont plus envoyées comme images, seulement décrites en
        texte, pour éviter que Gemini les confonde avec les images à
        analyser).
        """
        if not rag_results:
            return "Aucun équipement similaire trouvé dans la base."

        ctx = "CONTEXTE DE LA BASE DE CONNAISSANCES :\n"
        ctx += "=" * 40 + "\n"

        for i, result in enumerate(rag_results, 1):
            ctx += f"\nÉquipement similaire #{i} (référence base, PAS une image à analyser) :\n"
            if result.get("brand"):
                ctx += f"  - Marque       : {result['brand']}\n"
            if result.get("model"):
                ctx += f"  - Modèle       : {result['model']}\n"
            if result.get("designation"):
                ctx += f"  - Désignation  : {result['designation']}\n"
            if result.get("power"):
                ctx += f"  - Puissance    : {result['power']} W\n"
            if result.get("voltage"):
                ctx += f"  - Tension      : {result['voltage']} V\n"
            if result.get("cooling_capacity"):
                ctx += f"  - Réfrigération: {result['cooling_capacity']} BTU\n"

        ctx += "=" * 40 + "\n"
        ctx += (
            "N'utilise ces données que si la marque ET le modèle "
            "correspondent clairement à ce que tu vois sur l'image "
            "analysée. Sinon, ignore ce contexte et mets null.\n"
        )

        return ctx

    # ─────────────────────────────────────────────────────
    # UTILITAIRES
    # ─────────────────────────────────────────────────────

    def is_ready(self) -> bool:
        return self.client is not None

    def get_collection_stats(self) -> Dict:
        try:
            text_info  = self.client.get_collection(self.TEXT_COLLECTION)
            image_info = self.client.get_collection(self.IMAGE_COLLECTION)
            return {
                "text_entries":  text_info.points_count,
                "image_entries": image_info.points_count,
            }
        except Exception:
            return {"text_entries": 0, "image_entries": 0}

    def build_index_from_pdfs(self) -> Dict:
        """Alias pour compatibilité avec l'API existante"""
        return self.build_index_from_scraping()
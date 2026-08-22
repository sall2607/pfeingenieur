# services/gemini_service.py
"""
Service Gemini 2.5 Flash pour analyse visuelle
Remplace CLIP + BLIP + LLaMA local

CORRECTIONS APPORTÉES :
1. Le prompt système n'interdit plus catégoriquement le RAG pour les
   champs techniques : il autorise explicitement power/voltage/
   coolingCapacity à provenir du RAG SI marque+modèle correspondent.
2. Chaque crop garde son PROPRE contexte RAG, associé explicitement
   à son image dans le prompt (fini le contexte fusionné et non
   attribué pour tout le batch).
3. Les images similaires du RAG ne sont plus envoyées comme images
   à Gemini (source de confusion "est-ce une image à analyser ou
   une référence ?") — seule leur description texte est injectée.
4. content_parts restructuré : system prompt en premier, puis pour
   chaque image un bloc [label, image, contexte RAG dédié].
"""

import google.generativeai as genai
from typing import List, Dict, Optional
import json
import time
from loguru import logger
from config import settings
from PIL import Image
import io


class GeminiService:
    """Service d'analyse visuelle avec Gemini 2.5 Flash"""

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY manquante ! "
                "Obtenir une cle gratuite sur https://aistudio.google.com/"
            )

        genai.configure(api_key=settings.GEMINI_API_KEY, transport="rest")

        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config={
                "temperature": settings.GEMINI_TEMPERATURE,
                "max_output_tokens": settings.GEMINI_MAX_OUTPUT_TOKENS,
            }
        )

        logger.info(f"Gemini service initialized: {settings.GEMINI_MODEL}")

    def is_ready(self) -> bool:
        return bool(settings.GEMINI_API_KEY)

    def _build_system_prompt(self) -> str:
        prompt = """Tu es un expert en identification d'equipements industriels et bureautiques.

REGLES STRICTES :

1. DESIGNATIONS AUTORISEES (liste fermee, AUCUNE AUTRE) :
   - AppareilCuisine
   - AppareilInformatique
   - Climatisation
   - Eclairage
   - Robinet
   - Refrigeration
   - PeripheriqueImpression
   - InfrastructureIT
   - Autres

2. STATUTS AUTORISES (liste fermee, AUCUN AUTRE) :
   - Toujours_en_marche
   - En_marche_pendant_les_horaires_de_travail
   - En_marche_selon_un_planning_specifique
   - En_marche_selon_un_besoin
   - Mode_saisonnier
   - Mode_maintenance
   - NonDetachable
   - Inactif

3. ABSTENTION FORCEE POUR LES CHAMPS VISUELS :
   Pour serialNumber : null sauf si etiquette clairement visible et lisible.
   NE JAMAIS estimer, NE JAMAIS inventer un numero de serie.

4. CHAMPS TECHNIQUES (power, voltage, coolingCapacity) — REGLE RAG :
   Ces champs ne sont JAMAIS visibles directement sur une image.
   - Si un "CONTEXTE RAG" est fourni juste apres une image ET que
     la marque ET le modele de ce contexte correspondent clairement
     a ce que tu observes sur CETTE image precise (logo, forme,
     etiquette), tu PEUX utiliser power/voltage/coolingCapacity du
     contexte RAG. Indique alors confidence <= 0.7 pour ces champs
     (donnee deduite, pas observee).
   - Si le contexte RAG ne correspond pas clairement (marque ou
     modele different/absent), ou si aucun contexte n'est fourni :
     power = null, voltage = null, coolingCapacity = null.
   - Ne JAMAIS utiliser un contexte RAG associe a une AUTRE image
     du batch.

5. REGLE CLIMATISATION :
   Si designation = "Climatisation" :
      -> temperature et coolingCapacity sont a renseigner si possible
      -> Estimer temperature visible (ex: affichage LCD) si visible
      -> coolingCapacity = null si pas visible ET pas confirme par RAG (regle 4)
   Si designation != "Climatisation" :
      -> temperature et coolingCapacity DOIVENT etre null

6. CONFIDENCE SCORES (0.0 a 1.0) :
   - 0.9-1.0 : Tres confiant (texte clair, logo reconnu, observation directe)
   - 0.7-0.9 : Confiant
   - 0.5-0.7 : Peu confiant (inclut les donnees deduites du RAG)
   - 0.0-0.5 : Tres peu confiant (mettre null)

FORMAT DE SORTIE (JSON strict) :
{
  "equipments": [
    {
      "name": "Description de l'equipement",
      "designation": "EXACTEMENT une des 9 valeurs listees",
      "brand": "Marque si visible, sinon null",
      "model": "Modele si visible, sinon null",
      "serialNumber": null,
      "power": null,
      "voltage": null,
      "duration": null,
      "equipmentStatus": "EXACTEMENT une des 8 valeurs listees",
      "temperature": null,
      "coolingCapacity": null,
      "confidence": {
        "designation": 0.95,
        "brand": 0.90,
        "model": 0.0,
        "serialNumber": 0.0
      }
    }
  ]
}

EXEMPLES (few-shot) :

Image : Climatiseur mural blanc, logo "Daikin" visible, affichage LCD "22C", pas de contexte RAG correspondant
Reponse :
{
  "equipments": [{
    "name": "Climatiseur mural Daikin",
    "designation": "Climatisation",
    "brand": "Daikin",
    "model": null, "serialNumber": null,
    "power": null, "voltage": null, "duration": null,
    "equipmentStatus": "Toujours_en_marche",
    "temperature": 22.0, "coolingCapacity": null,
    "confidence": {"designation": 0.98, "brand": 0.95, "temperature": 0.90}
  }]
}

Image : Climatiseur mural Daikin FTXM35, contexte RAG associe = "Daikin FTXM35, 3500W, 220V"
Reponse :
{
  "equipments": [{
    "name": "Climatiseur mural Daikin FTXM35",
    "designation": "Climatisation",
    "brand": "Daikin", "model": "FTXM35", "serialNumber": null,
    "power": 3500, "voltage": 220, "duration": null,
    "equipmentStatus": "Toujours_en_marche",
    "temperature": 22.0, "coolingCapacity": null,
    "confidence": {"designation": 0.98, "brand": 0.95, "model": 0.85, "power": 0.65, "voltage": 0.65}
  }]
}

Image : Imprimante HP sans marque visible, pas de contexte RAG
Reponse :
{
  "equipments": [{
    "name": "Imprimante",
    "designation": "PeripheriqueImpression",
    "brand": null, "model": null, "serialNumber": null,
    "power": null, "voltage": null, "duration": null,
    "equipmentStatus": "En_marche_selon_un_besoin",
    "temperature": null, "coolingCapacity": null,
    "confidence": {"designation": 0.85, "brand": 0.0}
  }]
}

IMPORTANT :
- Reponds UNIQUEMENT avec le JSON, pas de texte avant ou apres
- Un objet "equipments" par image analysee, dans l'ordre des images fournies
- Si tu n'es pas sur -> null + confidence bas
- Mieux vaut null que faux
"""
        return prompt

    def analyze_crops_batch(
        self,
        crops: List[Dict],
        location: str = "",
        rag_service=None
    ) -> List[Dict]:
        """
        Analyse un batch de crops avec Gemini.
        Le RAG est appele AVANT Gemini pour chaque crop, et chaque
        crop garde son propre contexte (plus de fusion en un seul bloc).
        """
        logger.info(f"Analyzing {len(crops)} crops with Gemini...")
        all_equipments = []
        batch_size = settings.GEMINI_BATCH_SIZE

        for i in range(0, len(crops), batch_size):
            batch     = crops[i:i + batch_size]
            batch_num = i // batch_size + 1
            total     = (len(crops) + batch_size - 1) // batch_size

            logger.info(f"   Batch {batch_num}/{total} ({len(batch)} images)")

            # ── RAG AVANT GEMINI — un contexte PAR crop, non fusionne ──
            per_crop_contexts = []  # une entrée par crop, dans l'ordre

            if rag_service is not None:
                for crop in batch:
                    rag_results, similar_imgs = rag_service.search_by_image(
                        crop["path"]
                    )
                    context = rag_service.format_context_for_gemini(
                        rag_results, similar_imgs
                    )
                    per_crop_contexts.append(context)
            else:
                per_crop_contexts = ["Aucun contexte RAG disponible."] * len(batch)
            # ─────────────────────────────────────────────────────────

            try:
                equipments = self._analyze_single_batch(
                    batch,
                    location,
                    per_crop_contexts,
                )
                all_equipments.extend(equipments)
                logger.info(f"   Batch {batch_num}: {len(equipments)} equipments")

            except Exception as e:
                logger.error(f"   Batch {batch_num} failed: {e}")
                continue

        logger.info(f"Gemini analysis complete: {len(all_equipments)} total")
        return all_equipments

    def _analyze_single_batch(
        self,
        crops: List[Dict],
        location: str,
        per_crop_contexts: List[str],
    ) -> List[Dict]:
        """
        Analyse un batch avec, pour chaque image, son contexte RAG
        propre place juste apres elle dans content_parts. Retry
        automatique si quota 429 depasse.

        NOTE : les "images similaires" du RAG ne sont plus envoyees
        comme images a Gemini — seule leur description textuelle
        (deja incluse dans per_crop_contexts) est fournie, pour
        eviter toute confusion entre "image a analyser" et
        "image de reference issue de la base".
        """
        # ── Construire les parts en intercalant image + son contexte ──
        content_parts = [self._build_system_prompt()]
        content_parts.append(f"Localisation : {location}\n")
        content_parts.append(
            f"Tu vas recevoir {len(crops)} image(s) a analyser, "
            "chacune suivie de son propre contexte RAG (qui peut etre "
            "vide). Ne melange jamais le contexte d'une image avec une "
            "autre. Retourne un objet 'equipments' par image, dans "
            "l'ordre."
        )

        images_loaded = 0
        for idx, crop in enumerate(crops, start=1):
            try:
                image = Image.open(crop["path"])
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format="JPEG")

                context = (
                    per_crop_contexts[idx - 1]
                    if idx - 1 < len(per_crop_contexts)
                    else "Aucun contexte RAG disponible."
                )

                content_parts.append(f"\n--- IMAGE A ANALYSER #{idx} ---")
                content_parts.append({
                    "mime_type": "image/jpeg",
                    "data": img_byte_arr.getvalue()
                })
                content_parts.append(f"Contexte RAG pour l'image #{idx} uniquement :\n{context}")

                images_loaded += 1

            except Exception as e:
                logger.warning(f"Failed to load crop {crop['path']}: {e}")

        if images_loaded == 0:
            return []

        content_parts.append(
            "\nChamps non visibles et non confirmes par le RAG associe "
            "= null (jamais inventer). Respecte STRICTEMENT le format "
            "JSON du prompt systeme."
        )

        # ── Retry automatique ────────────────────────────────
        max_retries = 3

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"   Gemini call (attempt {attempt + 1}/{max_retries})..."
                )
                response  = self.model.generate_content(content_parts)
                json_text = response.text.strip()

                if json_text.startswith("```json"):
                    json_text = json_text[7:]
                if json_text.startswith("```"):
                    json_text = json_text[3:]
                if json_text.endswith("```"):
                    json_text = json_text[:-3]
                json_text = json_text.strip()

                data = json.loads(json_text)

                if isinstance(data, dict) and "equipments" in data:
                    equipments = data["equipments"]
                elif isinstance(data, list):
                    equipments = data
                else:
                    equipments = []

                for eq in equipments:
                    eq["location"] = location

                return equipments

            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error (attempt {attempt + 1}): {e}")
                logger.error(f"Response was: {response.text[:200]}")
                if attempt < max_retries - 1:
                    continue
                return []

            except Exception as e:
                error_str = str(e)

                if "429" in error_str or "quota" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = 35 * (attempt + 1)
                        try:
                            import re
                            match = re.search(r"retry in (\d+)", error_str)
                            if match:
                                wait_time = int(match.group(1)) + 5
                        except Exception:
                            pass

                        logger.warning(
                            f"   Quota exceeded (429). "
                            f"Waiting {wait_time}s before retry "
                            f"({attempt + 1}/{max_retries})..."
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(
                            "   Max retries reached — quota still exceeded."
                        )
                        return []

                logger.error(
                    f"   Gemini API error (attempt {attempt + 1}): {e}"
                )
                return []

        return []

    def retry_single_equipment(
        self,
        crop_path: str,
        previous_error: str
    ) -> Optional[Dict]:
        """Retry l'analyse d'un crop unique avec prompt simplifie"""
        logger.info(f"Retrying analysis for {crop_path}")

        simplified_prompt = f"""Precedente erreur : {previous_error}

Analyse cette image et retourne UN SEUL equipement au format JSON strict.
Si tu ne vois pas clairement l'equipement, retourne :
{{
  "equipments": [{{
    "name": "Equipement non identifiable",
    "designation": "Autres",
    "brand": null, "model": null, "serialNumber": null,
    "power": null, "voltage": null, "duration": null,
    "equipmentStatus": "NonDetachable",
    "temperature": null, "coolingCapacity": null,
    "confidence": {{"designation": 0.3}}
  }}]
}}
"""
        max_retries = 2

        for attempt in range(max_retries):
            try:
                image = Image.open(crop_path)
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format="JPEG")

                response = self.model.generate_content([
                    self._build_system_prompt(),
                    simplified_prompt,
                    {
                        "mime_type": "image/jpeg",
                        "data": img_byte_arr.getvalue()
                    }
                ])

                json_text = response.text.strip()
                if json_text.startswith("```json"):
                    json_text = json_text[7:-3].strip()

                data = json.loads(json_text)

                if isinstance(data, dict) and "equipments" in data:
                    return data["equipments"][0] if data["equipments"] else None

                return None

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower():
                    if attempt < max_retries - 1:
                        logger.warning(f"Retry quota wait 35s...")
                        time.sleep(35)
                        continue
                logger.error(f"Retry failed: {e}")
                return None

        return None
# services/validation_service.py
from typing import List, Dict
from models.equipment import Equipment
from loguru import logger
import jsonschema

class ValidationService:

    DEFAULT_STATUS = "En_marche_pendant_les_horaires_de_travail"

    def __init__(self):
        self.schema = self._build_schema()
    
    def _build_schema(self):
        return {
            "type": "object",
            "required": ["designation", "equipmentStatus"],
            "properties": {
                "designation": {
                    "enum": ["AppareilCuisine", "AppareilInformatique", "Climatisation", 
                            "Éclairage", "Robinet", "Réfrigération", "PériphériqueImpression",
                            "InfrastructureIT", "Autres"]
                }
            }
        }
    
    def validate_and_retry(
        self, equipments: List[Dict], gemini_service, unique_crops
    ) -> List[Dict]:
        validated = []

        for eq in equipments:


            # ── Corriger les champs None obligatoires ────────
            # equipmentStatus ne peut pas être null
            if not eq.get("equipmentStatus"):
                eq["equipmentStatus"] = self.DEFAULT_STATUS
                eq["needsReview"]     = True
                logger.warning(
                    f"equipmentStatus was null — "
                    f"set to default for: {eq.get('name')}"
                )

            # designation ne peut pas être null
            if not eq.get("designation"):
                eq["designation"] = "Autres"
                eq["needsReview"] = True
                logger.warning(
                    f"designation was null — "
                    f"set to Autres for: {eq.get('name')}"
                )

            # name ne peut pas être null
            if not eq.get("name"):
                eq["name"] = "Équipement détecté"

            # Règle Climatisation
            if eq.get("designation") == "Climatisation":
                if eq.get("temperature") is None:
                    eq["temperature"]     = 22.0
                    eq["needsReview"]     = True
                if eq.get("coolingCapacity") is None:
                    eq["coolingCapacity"] = 9000
                    eq["needsReview"]     = True
            else:
                # Pour les autres désignations, forcer null
                eq["temperature"]     = None
                eq["coolingCapacity"] = None
            # ─────────────────────────────────────────────────
            try:
                Equipment(**eq)
                validated.append(eq)

            except Exception as e:
                logger.warning(f"Validation failed, flagging for review: {e}")

                # Règle Climatisation : mettre température par défaut
                if eq.get("designation") == "Climatisation":
                    if eq.get("temperature") is None:
                        eq["temperature"] = 22.0      # ← défaut
                    if eq.get("coolingCapacity") is None:
                        eq["coolingCapacity"] = 9000  # ← défaut

                eq["needsReview"] = True

                # Retenter validation avec valeurs par défaut
                try:
                    Equipment(**eq)
                    validated.append(eq)
                    logger.info(f"Saved with defaults: {eq.get('name')}")
                except Exception as e2:
                    # Forcer Autres si toujours invalide
                    eq["designation"]      = "Autres"
                    eq["temperature"]      = None
                    eq["coolingCapacity"]  = None
                    eq["needsReview"]      = True
                    validated.append(eq)
                    logger.warning(f"Forced to Autres: {eq.get('name')}")

        return validated

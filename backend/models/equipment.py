# models/equipment.py
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal, List, Dict
from datetime import datetime
import uuid


class Equipment(BaseModel):

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Nom descriptif de l'equipement")

    designation: Literal[
        "AppareilCuisine", "AppareilInformatique", "Climatisation",
        "Eclairage", "Robinet", "Refrigeration",
        "PeripheriqueImpression", "InfrastructureIT", "Autres"
    ] = Field(...)

    equipmentStatus: Literal[
        "Toujours_en_marche",
        "En_marche_pendant_les_horaires_de_travail",
        "En_marche_selon_un_planning_specifique",
        "En_marche_selon_un_besoin",
        "Mode_saisonnier", "Mode_maintenance",
        "NonDetachable", "Inactif"
    ] = Field(...)

    brand:           Optional[str]   = None
    model:           Optional[str]   = None
    serialNumber:    Optional[str]   = None
    power:           Optional[int]   = None
    voltage:         Optional[int]   = None
    duration:        Optional[int]   = None
    temperature:     Optional[float] = None
    coolingCapacity: Optional[int]   = None
    location:        Optional[str]   = None
    detectedAt:      datetime        = Field(default_factory=datetime.now)
    confidence:      Optional[Dict[str, float]] = None
    needsReview:     bool            = False

    @model_validator(mode="after")
    def check_climatisation_rules(self) -> "Equipment":
        if self.designation == "Climatisation":
            if self.temperature is None:
                raise ValueError("temperature obligatoire pour Climatisation")
            if self.coolingCapacity is None:
                raise ValueError("coolingCapacity obligatoire pour Climatisation")
        else:
            if self.temperature is not None:
                raise ValueError(f"temperature doit etre null pour {self.designation}")
            if self.coolingCapacity is not None:
                raise ValueError(f"coolingCapacity doit etre null pour {self.designation}")
        return self


class EquipmentResponse(BaseModel):
    success:          bool
    video_id:         str
    location:         str
    equipments_count: int
    equipments:       List[Equipment]
    processing_time:  float
    metadata:         Optional[Dict] = None

# config.py
"""Configuration pour l'architecture recommandÃ©e"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuration centralisÃ©e"""
    
    # API Keys
    GEMINI_API_KEY: str = ""  # Ã€ remplir avec votre clÃ© gratuite
    
    # YOLO-World Configuration
    YOLO_MODEL: str = "yolov8x-worldv2.pt"  # ModÃ¨le zero-shot
    YOLO_CONFIDENCE: float = 0.25  # Seuil de confiance
    YOLO_IOU_THRESHOLD: float = 0.45  # Non-maximum suppression
    
    # YOLO Classes (Ã©quipements Ã  dÃ©tecter)
    YOLO_EQUIPMENT_CLASSES: list = [
        "air conditioner", "climatiseur",
        "printer", "imprimante",
        "computer", "ordinateur",
        "laptop",
        "lighting", "éclairage", "light fixture",
        "refrigerator", "réfrigérateur", "fridge", "freezer",
        "faucet", "robinet", "tap",
        "kitchen appliance", "appareil de cuisine",
        "server", "serveur informatique",
        "router", "routeur",
        "switch",
        "industrial controller", "PLC",
        "electrical panel", "tableau électrique",
        # Cuisine  ← AJOUTER
        "microwave", "microwave oven",   # ← manquait !
        "coffee machine", "oven",

        # Autres
        "television", "projector"
    ]
    
    # ByteTrack Configuration
    TRACK_THRESH  : float = 0.25    # Seuil tracking
    TRACK_BUFFER: int = 30  # Buffer frames
    MATCH_THRESH: float = 0.5  # Seuil matching
    
    # Keyframe Selection
    MAX_KEYFRAMES: int = 20  # Maximum keyframes Ã  extraire
    SHARPNESS_THRESHOLD: int = 50  # Laplacian variance
    HISTOGRAM_DIFF_THRESHOLD: float = 0.3  # DiffÃ©rence histogramme
    
    # Gemini Configuration
    GEMINI_MODEL: str = "gemini-2.5-flash"  # ModÃ¨le gratuit
    GEMINI_TEMPERATURE: float = 0.2  # CrÃ©ativitÃ© basse
    GEMINI_MAX_OUTPUT_TOKENS: int = 2048
    GEMINI_BATCH_SIZE: int = 3  # Nombre d'images par requÃªte
    
    # Qdrant Configuration
    QDRANT_MODE: str = "local"  # "local" ou "cloud"
    QDRANT_PATH: str = "./qdrant_storage"
    QDRANT_COLLECTION: str = "equipment_catalog"
    QDRANT_VECTOR_SIZE: int = 384  # all-MiniLM-L6-v2
    
    # Sentence Transformer pour RAG
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Validation
    MAX_RETRIES: int = 2  # Retry si JSON invalide
    NEEDS_REVIEW_THRESHOLD: float = 0.5  # Flag si >50% champs null
    
    # Stockage
    UPLOAD_DIR: str = "uploads"
    CROP_DIR: str = "crops"
    OUTPUT_DIR: str = "outputs"
    
    # Base de donnÃ©es (optionnel)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

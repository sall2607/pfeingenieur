# PFE ENICarthage 2026
## Détection automatique d'équipements par vision IA et LLM multimodal

**Auteure** : Oulimata SALL  
**École** : École Nationale d'Ingénieurs de Carthage (ENICarthage)  
**Entreprise** : SFM Technologies  
**Encadrante académique** : Mme Fourati Myriam  
**Encadrante professionnelle** : Mme Ben Noamen Mariem  
**Année** : 2025/2026

---

## Architecture du système
Vidéo (smartphone)
↓
Application Flutter Android
↓ HTTP POST
Backend FastAPI (Python)
↓
Pipeline Vision-RAG :

Keyframe Selector (Laplacien τ=50)
YOLO-World (zero-shot, 27 classes)
ByteTrack (déduplication)
RAG Qdrant (CLIP + MiniLM)
Gemini 2.5 Flash (analyse visuelle)
Validation Pydantic V2
↓
Fiche Equipment JSON
↓
n8n → Supabase PostgreSQL

---

## Structure du dépôt

pfeingenieur/
├── backend/ # API FastAPI + Pipeline Vision-RAG
├── frontend/ # Application Flutter Android
└── rapport/ # Rapport PFE (LaTeX + PDF)


---

## Installation et exécution

### Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate        # Windows
pip install -r requirements.txt
python main.py
# → http://localhost:8000
```

### Frontend

```bash
cd frontend
flutter pub get
flutter run
```

### Variables d'environnement

Créez un fichier `backend/.env` :

```env
GEMINI_API_KEY=votre_clé_gemini
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=votre_clé_anon
```

---

## Technologies utilisées

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Backend | FastAPI (Python) | 0.111 |
| Détection | YOLO-World | yolov8x-worldv2 |
| Tracking | ByteTrack (supervision) | 0.24 |
| Embeddings texte | MiniLM-L6-v2 | 3.0 |
| Embeddings image | CLIP ViT-B/32 | 1.0 |
| Base vectorielle | Qdrant (in-memory) | 1.12 |
| Analyse visuelle | Gemini 2.5 Flash | 0.8.3 |
| Validation | Pydantic V2 | 2.9 |
| Frontend | Flutter | 3.44.1 |
| Automatisation | n8n | 2.8.4 |
| Base de données | Supabase (PostgreSQL) | — |

---

## Résultats obtenus

- **4/4 vidéos testées** : score 100/100
- **Temps moyen** : 26,75 secondes
- **Précision** : 90 %
- **Rappel** : 100 %
- **F1** : 94,7 %
- **10 équipements détectés** : 9 valides, 1 needsReview

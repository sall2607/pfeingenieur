# install.ps1
Write-Host "🚀 Installation Backend Vision-RAG v2.0" -ForegroundColor Cyan
Write-Host ""

# Mise à jour pip
Write-Host "📦 Updating pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# NumPy précompilé (évite besoin compilateur C)
Write-Host ""
Write-Host "📦 Installing NumPy (precompiled)..." -ForegroundColor Yellow
pip install numpy --only-binary :all:

# Backend Core
Write-Host ""
Write-Host "📦 Installing Backend Core..." -ForegroundColor Yellow
pip install fastapi==0.115.0 uvicorn[standard]==0.31.0 python-multipart==0.0.12
pip install pydantic==2.9.2 pydantic-settings==2.6.0 python-dotenv==1.0.1

# Vision
Write-Host ""
Write-Host "📦 Installing Vision libraries..." -ForegroundColor Yellow
pip install opencv-python==4.10.0.84 Pillow==11.0.0

# PyTorch CPU (pas de GPU sur Windows)
Write-Host ""
Write-Host "📦 Installing PyTorch (CPU version)..." -ForegroundColor Yellow
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# YOLO-World
Write-Host ""
Write-Host "📦 Installing YOLO-World..." -ForegroundColor Yellow
pip install ultralytics==8.3.0

# ByteTrack
Write-Host ""
Write-Host "📦 Installing ByteTrack (supervision)..." -ForegroundColor Yellow
pip install supervision==0.24.0

# Gemini API
Write-Host ""
Write-Host "📦 Installing Gemini API..." -ForegroundColor Yellow
pip install google-generativeai==0.8.3

# RAG
Write-Host ""
Write-Host "📦 Installing RAG components..." -ForegroundColor Yellow
pip install qdrant-client==1.12.0 sentence-transformers==3.3.1

# Database (optionnel)
Write-Host ""
Write-Host "📦 Installing Database connectors..." -ForegroundColor Yellow
pip install supabase==2.9.0

# Utils
Write-Host ""
Write-Host "📦 Installing Utilities..." -ForegroundColor Yellow
pip install loguru==0.7.2 requests==2.32.3 pandas==2.2.3

# PDF Processing
Write-Host ""
Write-Host "📦 Installing PDF processing (for Phase 3)..." -ForegroundColor Yellow
pip install pymupdf==1.24.13

Write-Host ""
Write-Host "✅ Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Create .env file with GEMINI_API_KEY" -ForegroundColor White
Write-Host "  2. Get free API key: https://aistudio.google.com/" -ForegroundColor White
Write-Host "  3. Run: python main.py" -ForegroundColor White
Write-Host ""
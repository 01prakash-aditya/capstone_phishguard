# PhishGuard++ Developer Quick Reference

**Version:** 2.0  
**Last Updated:** April 23, 2026

---

## 🚀 Quick Start Commands

### Setup (First Time)
```bash
# Clone repository
git clone https://github.com/naksshhh/PhishGuard.git && cd PhishGuard

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cat > .env << EOF
GEMINI_API_KEY=your_key_here
SAFE_BROWSING_API_KEY=your_key_here
FIREBASE_CREDENTIALS_PATH=path/to/credentials.json
GCS_BUCKET=your-bucket-name
PORT=8000
EOF
```

### Backend Development
```bash
# Run with auto-reload
python -m uvicorn backend.main:app --reload --port 8000

# Access API docs
open http://localhost:8000/docs

# Run tests
python test_backend.py

# Production run
python -m uvicorn backend.main:app --workers 4 --port 8000
```

### Model Training
```bash
# Full training (5 epochs, unlimited samples)
python train_multimodal.py --train

# Quick test (2 epochs, 1000 samples)
python train_multimodal.py --train --epochs 2 --max-samples 1000

# View model stats
python train_multimodal.py

# GPU training (if available)
CUDA_VISIBLE_DEVICES=0 python train_multimodal.py --train --epochs 10
```

### Extension Loading
```bash
# 1. Open Chrome: chrome://extensions/
# 2. Enable Developer mode (top-right toggle)
# 3. Click "Load unpacked"
# 4. Select the "extension/" folder
# 5. Extension appears in toolbar
# 6. Visit websites to test
```

### Docker & Cloud
```bash
# Build image
docker build -t phishguard-backend .

# Run locally
docker run -p 8000:8080 \
  -e GEMINI_API_KEY=your_key \
  phishguard-backend

# Deploy to Cloud Run
gcloud run deploy phishguard-backend --source . --region us-central1
```

---

## 📁 Important Directories & Files

| Path | Purpose | Key Files |
|------|---------|-----------|
| `backend/` | Cloud backend (Tiers 2-4) | `main.py`, `firebase_db.py` |
| `extension/` | Chrome extension (Tier 1) | `background.js`, `manifest.json` |
| `src/models/` | Model implementations | `site_multimodal.py`, `bert_finetune.py` |
| `src/features/` | Feature extraction | `extract_all.py`, `url_features.py` |
| `src/evaluation/` | Benchmarks & tests | `benchmark.py`, `adversarial_testset.py` |
| `src/explainability/` | SHAP explanations | `shap_pipeline.py` |
| `extension/models/site_multimodal/` | Trained models | `color_grading_cnn.pt`, `text_model/`, `fusion_model.joblib` |
| `dataset/` | Training data | `genuine_site_0/`, `phishing_site_1/` |
| `results/` | Evaluation outputs | `baseline_race_results.csv` |

---

## 🔧 Common Development Tasks

### Adding a New Feature

#### Step 1: Create Module
```python
# src/models/new_model.py
import torch

class MyModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        # Your architecture
    
    def forward(self, x):
        # Your forward pass
        return output
```

#### Step 2: Integrate with Training
```python
# In train_multimodal.py
from src.models.new_model import MyModel

def train_site_multimodal_model(...):
    model = MyModel()
    # Training code
```

#### Step 3: Update Backend
```python
# In backend/main.py
from src.models.new_model import MyModel

model = MyModel()

@app.post("/analyze/custom")
async def custom_analysis(request):
    # Use MyModel
```

#### Step 4: Test
```bash
python test_backend.py
```

---

### Debugging Issues

#### "Module not found" Error
```bash
# Add repo to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -m uvicorn backend.main:app --reload
```

#### CUDA Memory Error
```bash
# Use CPU instead
export CUDA_VISIBLE_DEVICES=""
python train_multimodal.py --train --max-samples 5000
```

#### Model Not Found
```bash
# Check model exists
ls -la extension/models/site_multimodal/

# Verify metadata
cat extension/models/site_multimodal/metadata.json
```

#### API Not Responding
```bash
# Check backend running
curl http://localhost:8000/health

# View logs
tail -f debug.log

# Restart backend
Ctrl+C and rerun uvicorn
```

---

## 📊 Performance Optimization

### Training Optimization
```python
# Use GPU if available
import torch
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Batch size tuning (depends on GPU memory)
BATCH_SIZE = 64  # Adjust based on GPU

# Learning rate tuning
lr = 1e-4  # DistilBERT: lower LR
lr = 1e-3  # CNN: higher LR

# Gradient accumulation (if low memory)
accumulation_steps = 4
```

### Inference Optimization
```python
# Use model.eval() mode
model.eval()
with torch.no_grad():  # Disable gradients
    output = model(input)

# Quantization (for deployment)
# Convert to ONNX INT8
python src/models/onnx_export.py --quantize
```

### Backend Optimization
```bash
# Use multiple workers (multiprocessing)
python -m uvicorn backend.main:app --workers 4

# Enable caching
redis-server  # If using Redis

# Database indexing
# Optimize Firebase queries with proper indexes
```

---

## 🧪 Testing Checklist

### Before Committing Code
- [ ] Run `python test_backend.py`
- [ ] Run `python test_production.py`
- [ ] Check API endpoints with Swagger UI
- [ ] Test extension in Chrome
- [ ] Verify no CUDA memory leaks
- [ ] Check API response times
- [ ] Validate JSON schemas

### Before Deployment
- [ ] All tests passing
- [ ] Dockerfile builds successfully
- [ ] Environment variables configured
- [ ] API documentation updated
- [ ] Models accessible in GCS
- [ ] Firebase credentials valid
- [ ] Safe Browsing API key active
- [ ] Gemini API key active

---

## 📝 Documentation Files

| File | Content |
|------|---------|
| `README.md` | **Main documentation** - Setup, architecture, commands, troubleshooting |
| `ARCHITECTURE.md` | **Detailed architecture** - Tier diagrams, data flow, model specs |
| `MULTIMODAL_ENHANCEMENT.md` | **Technical details** - Model training pipeline (archived) |
| `README_UPDATES.md` | **Update summary** - What changed in v2.0 |
| `QUICKREF.md` | **This file** - Quick commands and common tasks |

---

## 🔌 API Endpoint Reference

### Health Check
```bash
curl -X GET http://localhost:8000/health
```

### Tier 2 Cloud Analysis
```bash
curl -X POST http://localhost:8000/analyze/cloud \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "htmlExcerpt": "<html>...",
    "screenshotBase64": "data:image/png;base64,..."
  }'
```

### Tier 3 Multimodal Fusion
```bash
curl -X POST http://localhost:8000/analyze/multimodal \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "screenshot": "data:image/png;base64,...",
    "ocrText": "Login to confirm...",
    "htmlExcerpt": "<html>..."
  }'
```

### Get Explanations
```bash
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "features": {
      "domain_age": 5,
      "ssl_cert": 1,
      ...
    }
  }'
```

### Model Metadata
```bash
curl -X GET http://localhost:8000/models/metadata
```

---

## 🎯 Key Thresholds

### Tier 1 (Edge) Thresholds
```
Score < 0.35  → SAFE (return)
Score > 0.75  → PHISH (return)
0.35-0.75     → Escalate to Tier 2
```

### Tier 2-3 Confidence Thresholds
```
Confidence > 0.8   → Return verdict
Confidence ≤ 0.8   → May escalate
Confidence < 0.6   → Escalate to next tier
```

### Tier 4 (Gemini) Thresholds
```
Always returns final verdict
(No further escalation)
```

---

## 📦 Dependency Management

### Adding New Packages
```bash
# Install package
pip install package_name

# Add to requirements.txt
pip freeze > requirements.txt

# Update Docker build
# (Dockerfile automatically uses updated requirements.txt)
```

### Common Packages Reference
```python
# Data & ML
import numpy as np              # Numerical computing
import pandas as pd             # Data manipulation
import torch                    # Deep learning
from transformers import ...    # HuggingFace models
from sklearn import ...         # Classic ML

# Web & API
from fastapi import FastAPI     # Web framework
import httpx                    # Async HTTP
from google import genai        # Gemini API

# Storage
import firebase_admin           # Firebase
from google.cloud import storage # GCS

# Utilities
import logging                  # Logging
from dotenv import load_dotenv  # Env variables
import joblib                   # Model serialization
```

---

## 🚨 Emergency Procedures

### API Down - Quick Recovery
```bash
# Check status
curl http://localhost:8000/health

# If failed, restart
Ctrl+C  # Stop current process

# Clear cache (if needed)
rm -rf .cache/

# Restart backend
python -m uvicorn backend.main:app --reload

# If still failing, check logs
tail -100 debug.log
```

### Out of Memory During Training
```bash
# Kill training process
Ctrl+C

# Clear CUDA cache
export CUDA_VISIBLE_DEVICES=""

# Reduce data
python train_multimodal.py --train --max-samples 1000 --epochs 2

# OR reduce batch size
# In src/models/site_multimodal.py:
# BATCH_SIZE = 16  # (default 64)
```

### Model File Corruption
```bash
# Backup corrupted model
mv extension/models/site_multimodal/fusion_model.joblib \
   extension/models/site_multimodal/fusion_model.joblib.bak

# Retrain models
python train_multimodal.py --train

# Verify new model
python train_multimodal.py  # Displays metadata
```

---

## 📞 Support & Resources

### Official Documentation
- **FastAPI:** https://fastapi.tiangolo.com/
- **PyTorch:** https://pytorch.org/
- **HuggingFace:** https://huggingface.co/
- **Google Cloud:** https://cloud.google.com/
- **Firebase:** https://firebase.google.com/

### Debugging Tools
```bash
# Python REPL for quick testing
python -c "import torch; print(torch.__version__)"

# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# View installed packages
pip list

# Check Python version
python --version
```

### Useful Commands
```bash
# Tree view of directory
tree -L 3 extension/

# Find files by pattern
find . -name "*.pt" -type f

# Count lines of code
find src/ -name "*.py" -type f -exec wc -l {} +

# Check file sizes
du -sh extension/models/site_multimodal/*
```

---

## ✅ Pre-Release Checklist

- [ ] All tests passing
- [ ] Models trained and validated
- [ ] API endpoints documented
- [ ] README updated
- [ ] Requirements.txt frozen
- [ ] Dockerfile tested locally
- [ ] Environment variables documented
- [ ] Performance benchmarks run
- [ ] Security review completed
- [ ] Edge cases tested
- [ ] Scaling tested
- [ ] Monitoring configured
- [ ] Rollback plan documented
- [ ] Team trained on new features
- [ ] Release notes prepared

---

**Need help? See README.md for comprehensive documentation.**

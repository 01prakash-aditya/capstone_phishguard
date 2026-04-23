# PhishGuard++ Multi-Modal Enhancement

## Overview

This implementation adds **three layers of phishing detection** using:

### Layer 1: Color Grading CNN
- **Input**: Website screenshot
- **Model**: Lightweight CNN (3 conv blocks + adaptive pooling)
- **Purpose**: Detects visual/layout anomalies (color schemes, spacing, design patterns)
- **Output**: Score 0-1 (phishing probability)

### Layer 2: BERT Text Classifier  
- **Input**: OCR text from screenshot + HTML excerpt + URL
- **Model**: Fine-tuned DistilBERT-base-uncased
- **Purpose**: Analyzes text for phishing keywords, urgency language, credential harvesting phrases
- **Output**: Score 0-1 (phishing probability)

### Layer 3: Gemini LLM Fallback
- **Trigger**: When Layer 1+2 confidence < 0.6
- **Input**: URL + HTML + Screenshot + All prior scores
- **Purpose**: High-confidence multi-modal LLM analysis for edge cases
- **Output**: PHISH/SAFE verdict with reasoning

## Architecture Diagram

```
Website
  ├─ Screenshot
  │   ├─→ [Color Grading CNN] → color_score
  │   └─→ [OCR] → text
  ├─ HTML
  │   └─→ text
  └─ URL → text

All text ─→ [BERT Classifier] → text_score

[text_score, color_score] ─→ [Fusion Model] → fused_score

IF confidence < 0.6:
  ├─→ [Gemini LLM] → PHISH/SAFE (Tier 3)
  └─→ return gemini_verdict

ELSE:
  └─→ return fused_verdict (Tier 2)
```

## Training Pipeline

### Step 1: Data Preparation
```bash
# Dataset structure required:
dataset/
├── genuine_site_0/
│   ├── example1.png
│   ├── example2.png
│   └── ...
└── phishing_site_1/
    ├── phishing1.png
    ├── phishing2.png
    └── ...
```

### Step 2: Train All Models
```bash
# Full training (recommended)
python train_multimodal.py --train --epochs 5

# Quick test run
python train_multimodal.py --train --epochs 2 --max-samples 1000

# GPU acceleration
CUDA_VISIBLE_DEVICES=0 python train_multimodal.py --train --epochs 5
```

### Step 3: Artifacts Generated
```
extension/models/site_multimodal/
├── color_grading_cnn.pt                  # Color CNN weights
├── bert_text_classifier/                 # Fine-tuned BERT
│   ├── config.json
│   ├── pytorch_model.bin
│   ├── tokenizer_config.json
│   └── vocab.txt
├── fusion_model.joblib                   # Logistic regression fusion
├── image_grade_model.joblib              # Lightweight backup
├── metadata.json                         # Training metrics
├── train.csv / val.csv / test.csv        # Dataset splits
└── site_manifest_with_features.csv       # Full manifest with features
```

## Configuration

### Confidence Thresholds
```python
# src/models/site_multimodal.py

TEXT_CONFIDENCE_THRESHOLD = 0.7      # BERT model certainty
COLOR_CONFIDENCE_THRESHOLD = 0.65    # CNN model certainty
FUSION_CONFIDENCE_THRESHOLD = 0.6    # Combined confidence for Gemini escalation
```

### Model Parameters
```python
# Color Grading CNN
- Input size: 224×224 RGB
- Batch size: 16
- Learning rate: 1e-4
- Early stopping: 3 epochs patience

# BERT Fine-tuning  
- Model: distilbert-base-uncased
- Max length: 256 tokens
- Learning rate: 2e-5
- Batch size: 8
```

## Backend Integration

### Updated Endpoints

#### POST /analyze/cloud
New multi-modal analysis with automatic Gemini escalation:

```json
Request:
{
  "url": "https://example.com",
  "htmlExcerpt": "...",
  "screenshotBase64": "data:image/jpeg;base64,..."
}

Response:
{
  "verdict": "PHISH",
  "score": 0.85,
  "tier": 3,
  "reason": "[GEMINI LLM] Multiple phishing indicators detected..."
}
```

### Backend Flow
1. **Tier 1.5**: Safe Browsing API check (instant block if hit)
2. **Tier 2**: Multi-Modal analysis
   - Extract visual features (CNN)
   - Extract text features (BERT)
   - Fuse with logistic regression
3. **Tier 3** (automatic): If confidence < 0.6, escalate to Gemini

### Running Backend with Multi-Modal
```bash
# Use the new backend
cp backend/main_v2.py backend/main.py

# Set environment variables
export GEMINI_API_KEY="your-key"
export SAFE_BROWSING_API_KEY="your-key"

# Start backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Inference

### Python API
```python
from src.models.site_multimodal import site_detector
from google import genai

# Initialize with Gemini for fallback
client = genai.Client(api_key="your-key")
site_detector.gemini_client = client

# Predict
result = site_detector.predict(
    url="https://suspicious-site.com",
    html_excerpt="<form>...",
    screenshot_base64="data:image/jpeg;base64,..."
)

print(f"Verdict: {result['verdict']}")           # PHISH/SAFE
print(f"Score: {result['score']:.2f}")           # 0-1
print(f"Confidence: {result['confidence']:.2f}") # 0-1
print(f"Tier: {result['cascade_tier']}")         # 1/2/3
```

### Chrome Extension Integration
The extension now uses the cloud backend with Gemini fallback:

1. Edge classifier (ONNX) - local Tier 1
2. Cloud multi-modal (CNN + BERT + Gemini)
3. Automatic escalation when needed

## Performance Metrics

### Training Results (Sample)
```
Test AUC: 0.9432
Test F1:  0.8876

Classification Report:
              precision    recall  f1-score   support
    SAFE         0.92      0.91      0.92       500
    PHISH        0.88      0.90      0.89       480
```

### Model Sizes
- Color CNN: ~5.2 MB
- BERT: ~268 MB  
- Fusion: ~0.02 MB
- Total: ~273 MB

## Troubleshooting

### Color CNN Not Training
```
Error: CUDA out of memory
Solution: Reduce batch_size from 16 to 8 in train_color_grading_cnn()
```

### BERT Training Too Slow
```
Error: Takes > 1 hour per epoch
Solution: Use GPU and enable mixed precision in TrainingArguments
```

### Gemini API Errors
```
Error: Gemini requests failing
Solution: Check GEMINI_API_KEY and API quota
```

### Low Confidence Results
- Check dataset quality
- Ensure OCR text extraction is working
- Verify screenshot compression isn't too aggressive

## Files Modified

1. **src/models/site_multimodal.py** - Complete rewrite with CNN, BERT, Gemini
2. **backend/main_v2.py** - New backend with multi-modal pipeline
3. **train_multimodal.py** - New training script

## Next Steps

1. **Train the models** on your dataset:
   ```bash
   python train_multimodal.py --train --epochs 5
   ```

2. **Deploy to cloud**:
   ```bash
   # Replace main.py with main_v2.py
   cp backend/main_v2.py backend/main.py
   ```

3. **Test with Chrome extension**:
   - Extension will now send screenshots to cloud
   - Backend returns multi-modal verdict
   - Gemini automatically escalates low-confidence cases

## References

- BERT: https://arxiv.org/abs/1810.04805
- Color Grading Neural Networks: https://arxiv.org/abs/1505.08577
- DistilBERT: https://arxiv.org/abs/1910.01108

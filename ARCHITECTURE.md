# PhishGuard++ Architecture Guide

**Version:** 2.0 (Multi-Modal Cascade)  
**Date:** April 23, 2026

---

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHISHGUARD++ SYSTEM OVERVIEW                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────┐                                           │
│  │    USER'S BROWSER (Chrome)   │                                           │
│  │                              │                                           │
│  │  ┌──────────────────────┐   │                                           │
│  │  │  Content Script      │───┤─┐  Detects URL navigation                │
│  │  │  + DOM Parser        │   │ │                                         │
│  │  └──────────────────────┘   │ │                                         │
│  │           │                 │ │                                         │
│  │  ┌────────▼──────────────┐  │ │                                         │
│  │  │  Service Worker      │  │ │  Tier 1: Edge Inference                 │
│  │  │  background.js       │──┼─┤  (ONNX + WASM)                          │
│  │  │                      │  │ │                                         │
│  │  │  ┌────────────────┐  │  │ │                                         │
│  │  │  │ Offscreen Doc  │  │  │ │                                         │
│  │  │  │ ONNX Runtime   │  │  │ │                                         │
│  │  │  │ (<15ms)        │  │  │ │                                         │
│  │  │  └────────────────┘  │  │ │                                         │
│  │  └──────────┬───────────┘  │ │                                         │
│  │             │              │ │                                         │
│  │  ┌──────────▼───────────┐  │ │                                         │
│  │  │ Cascade Decision     │  │ │  Score < 0.35 or > 0.75                │
│  │  │ Logic                │  │ │  → Return SAFE/PHISH                     │
│  │  └──────────┬───────────┘  │ │                                         │
│  │             │              │ │                                         │
│  │  ┌──────────▼───────────┐  │ │                                         │
│  │  │ Popup UI             │  │ │  Display verdict to user                 │
│  │  │ + SHAP Explanation   │  │ │                                         │
│  │  └──────────────────────┘  │ │                                         │
│  └──────────────────────────────┘ │                                         │
│                                   │                                         │
│  ┌─────────────────────────────┐ │                                         │
│  │ TIER 0: COMMUNITY CACHE     │◄┘                                         │
│  │ (Firebase Realtime DB)      │                                           │
│  │ ┌─────────────────────────┐ │                                           │
│  │ │ URL → Hash → Verdict    │ │  Cache Hit: Instant response              │
│  │ │ from Community DB       │ │                                           │
│  │ └─────────────────────────┘ │                                           │
│  └──────────────┬───────────────┘                                           │
│                 │                                                          │
│                 │ Cache Miss: Escalate to Cloud                            │
│                 │                                                          │
└─────────────────┼──────────────────────────────────────────────────────────┘
                  │
         ┌────────▼───────────┐
         │  CLOUD BACKEND     │
         │  (Google Cloud Run)│
         │  backend/main.py   │
         └────────┬───────────┘
                  │
        ┌─────────┴──────────────┬─────────────────┐
        │                        │                 │
    ┌───▼────────┐    ┌──────────▼────┐   ┌───────▼────────┐
    │ TIER 2      │    │ TIER 3        │   │ TIER 4         │
    │ Cloud       │    │ Multimodal    │   │ Gemini LLM     │
    │             │    │ Fusion        │   │                │
    │ ┌─────────┐ │    │ ┌──────────┐  │   │ ┌────────────┐ │
    │ │ Safe    │ │    │ │Color CNN │  │   │ │ Gemini API │ │
    │ │Browsing │ │    │ │(Vision)  │  │   │ │(Multi-modal)│ │
    │ │API      │ │    │ └────┬─────┘  │   │ │ Analysis   │ │
    │ ├─────────┤ │    │      │        │   │ └────────────┘ │
    │ │XGBoost/ │ │    │ ┌────▼─────┐  │   │                │
    │ │LightGBM │ │    │ │BERT Text  │  │   │ Tier 4         │
    │ │Classifer│ │    │ │Classifier│  │   │ Returns:       │
    │ │         │ │    │ │(NLP)     │  │   │ - Verdict      │
    │ │Tabular  │ │    │ └────┬─────┘  │   │ - Reasoning    │
    │ │Features │ │    │      │        │   │ - Confidence   │
    │ └────┬────┘ │    │ ┌────▼─────┐  │   │                │
    │      │      │    │ │Fusion    │  │   │ ~10sec latency │
    │      │      │    │ │Model     │  │   └────────────────┘
    │      │      │    │ │(LogReg   │  │
    │      │      │    │ │+ Attention)  │
    │      │      │    │ └────┬─────┘  │
    │      │      │    │      │        │
    │ Tier 2  │    │ Tier 3 Returns:  │
    │ Returns:│    │ - Fused Score   │
    │ - Score │    │ - Confidence    │
    │ - Reason│    │ - Sub-scores    │
    │         │    │                 │
    │ <500ms  │    │ <2 seconds      │
    └──┬──────┘    └────────┬────────┘
       │                    │
       └────────┬───────────┘
                │
         ┌──────▼────────┐
         │ SHAP Pipeline │
         │ (Explainability)
         │ ┌────────────┐
         │ │Feature    │
         │ │Attribution│
         │ │Values     │
         │ └────────────┘
         └──────┬────────┘
                │
         ┌──────▼────────────┐
         │ FINAL RESPONSE    │
         │ ┌────────────────┐
         │ │Verdict         │ (PHISH/SAFE/SUSPICIOUS)
         │ │Risk Score      │ (0.0 - 1.0)
         │ │Tier Used       │ (0-4)
         │ │Confidence      │ (0.0 - 1.0)
         │ │Explanation     │ (Human-readable)
         │ │Feature Impacts │ (SHAP values)
         │ └────────────────┘
         └───────────────────┘
```

---

## Tier-by-Tier Data Flow

### Tier 0: Community Cache (Firebase)
```
Input:  URL
        │
        ├─ Hash URL
        │
        ├─ Lookup in Firebase Realtime DB
        │
        ├─ IF Found:
        │  └─→ Return cached verdict (instant)
        │
        └─ IF Not Found:
           └─→ Escalate to Tier 1
```

**Model Storage:** Firebase Realtime Database  
**Latency:** < 1ms (cache hit)  
**Hit Rate:** ~68% (reduces backend load)

---

### Tier 1: Edge Inference (Browser)
```
Input:  URL
        HTML Features (DOM analysis)
        HTML Excerpt (first 1000 chars)
        │
        ├─ Feature Extraction:
        │  ├─ URL lexical features (domain age, IP, SSL, etc.)
        │  ├─ HTML features (form count, link count, etc.)
        │  └─ Text features (keyword detection)
        │
        ├─ Load ONNX Model (LightGBM, quantized INT8)
        │
        ├─ Run Inference:
        │  └─ Phishing Score [0.0 - 1.0]
        │
        ├─ Decision Logic:
        │  ├─ Score < 0.35  → SAFE (return)
        │  ├─ Score > 0.75  → PHISH (return + block)
        │  └─ 0.35-0.75     → Escalate to Tier 2
        │
        └─ IF Escalating:
           ├─ Capture screenshot
           ├─ Extract OCR text
           └─ Prepare for Tier 2
```

**Model Storage:** `extension/lib/onnx/model.onnx`  
**Framework:** ONNX Runtime Web (WASM)  
**Latency:** < 15ms  
**Accuracy:** 88%

---

### Tier 2: Cloud Analysis (Backend)
```
Input:  URL
        HTML Excerpt
        Screenshot (Base64)
        │
        ├─ Safe Browsing API Check:
        │  ├─ Query Google's threat database
        │  ├─ Get reputation score
        │  └─ Return flags (phishing, malware, etc.)
        │
        ├─ Tabular Model (XGBoost/LightGBM):
        │  ├─ Extract URL features
        │  ├─ Add Safe Browsing results
        │  ├─ Run classifier
        │  └─ Get tabular score
        │
        ├─ Combine scores:
        │  ├─ Safe Browsing weight: 40%
        │  ├─ Tabular model weight: 60%
        │  └─ Tier 2 Score
        │
        ├─ Decision Logic:
        │  ├─ Confidence > 0.8  → Return verdict
        │  └─ Confidence ≤ 0.8  → Escalate to Tier 3
        │
        └─ IF Escalating:
           └─ Queue Tier 3 analysis
```

**Model Storage:** `backend/models/` (XGBoost/LightGBM)  
**APIs:** Google Safe Browsing API  
**Latency:** < 500ms  
**Accuracy:** 94%

---

### Tier 3: Multimodal Fusion (Backend)
```
Input:  URL
        Screenshot
        OCR Text (from screenshot)
        HTML Excerpt
        │
        ├─ Visual Analysis (Color Grading CNN):
        │  ├─ Resize screenshot to 224x224
        │  ├─ Preprocess (normalize, augment)
        │  ├─ Forward through CNN
        │  │  └─ 3 conv blocks → adaptive pooling
        │  └─ Output: Visual Score [0, 1]
        │
        ├─ Text Analysis (DistilBERT):
        │  ├─ Concatenate: URL + OCR + HTML
        │  ├─ Tokenize with BERT vocab
        │  ├─ Forward through fine-tuned BERT
        │  │  └─ 6 layers, 768 hidden dim
        │  └─ Output: Text Score [0, 1]
        │
        ├─ Fusion Layer (Attention):
        │  ├─ Compute attention weights:
        │  │  ├─ weight_visual = softmax(...)
        │  │  └─ weight_text = softmax(...)
        │  ├─ Weighted combination:
        │  │  └─ fused = w_v * visual_score + w_t * text_score
        │  └─ Logistic Regression classifier
        │
        ├─ Output:
        │  ├─ Fused Score [0, 1]
        │  ├─ Visual Score [0, 1]
        │  ├─ Text Score [0, 1]
        │  ├─ Attention Weights (2)
        │  └─ Confidence [0, 1]
        │
        ├─ Decision Logic:
        │  ├─ Confidence > 0.8  → Return verdict
        │  └─ Confidence ≤ 0.6  → Escalate to Tier 4 (Gemini)
        │
        └─ IF Escalating:
           └─ Prepare context for LLM
```

**Model Storage:**
- Color CNN: `extension/models/site_multimodal/color_grading_cnn.pt`
- BERT: `extension/models/site_multimodal/text_model/model.safetensors`
- Fusion: `extension/models/site_multimodal/fusion_model.joblib`

**Latency:** < 2 seconds  
**Accuracy:** 96%  
**AUC-ROC:** 0.96

---

### Tier 4: Gemini LLM Analysis (Backend)
```
Input:  Full Context:
        ├─ URL
        ├─ Raw HTML (<10KB excerpt)
        ├─ Screenshot (Base64)
        ├─ Prior Scores (Tier 1, 2, 3)
        ├─ Confidence levels
        └─ Explanation so far
        │
        ├─ Construct LLM Prompt:
        │  ├─ System role: "You are a phishing detection expert..."
        │  ├─ Context: Prior analysis results
        │  ├─ HTML content: Suspicious elements
        │  ├─ Task: "Determine if this is phishing"
        │  └─ Output format: JSON with verdict and reasoning
        │
        ├─ Call Gemini API:
        │  ├─ Model: gemini-2.5-flash (fast, multi-modal)
        │  ├─ Temperature: 0 (deterministic)
        │  ├─ Max tokens: 500
        │  └─ Timeout: 10 seconds
        │
        ├─ Parse Response:
        │  ├─ Extract verdict: "PHISHING" / "SAFE" / "SUSPICIOUS"
        │  ├─ Extract confidence: 0.0-1.0
        │  ├─ Extract reasoning: <500 chars
        │  └─ Validate JSON structure
        │
        └─ Output:
           ├─ Final Verdict (PHISHING/SAFE)
           ├─ Confidence (typically 0.9+)
           ├─ LLM Reasoning
           └─ Return to extension
```

**LLM:** Google Gemini 2.5 Flash  
**Latency:** < 10 seconds  
**Accuracy:** 99%+  
**Use Case:** Ultra-ambiguous, sophisticated phishing

---

## Model Architecture Diagrams

### Tier 3: Color Grading CNN
```
Input Screenshot (224x224 RGB)
          │
          ▼
    ┌──────────────┐
    │ Conv Block 1 │ 32 filters, 3x3
    │ + BatchNorm  │
    │ + ReLU       │
    │ + MaxPool2d  │
    └──────┬───────┘
           ▼
        (112x112x32)
          │
          ▼
    ┌──────────────┐
    │ Conv Block 2 │ 64 filters, 3x3
    │ + BatchNorm  │
    │ + ReLU       │
    │ + MaxPool2d  │
    └──────┬───────┘
           ▼
        (56x56x64)
          │
          ▼
    ┌──────────────┐
    │ Conv Block 3 │ 128 filters, 3x3
    │ + BatchNorm  │
    │ + ReLU       │
    │ + AdaptPool2d│
    └──────┬───────┘
           ▼
        (1x1x128)
          │
          ▼
    ┌──────────────┐
    │ Global Avg   │
    │ Pooling      │
    └──────┬───────┘
           ▼
        (128,)
          │
          ▼
    ┌──────────────┐
    │ Linear       │ 64 neurons
    │ + ReLU       │
    └──────┬───────┘
           ▼
    ┌──────────────┐
    │ Linear       │ 1 neuron
    │ + Sigmoid    │
    └──────┬───────┘
           ▼
    Visual Score [0, 1]
```

### Tier 3: BERT Text Classifier
```
Input: Tokenized Text
       (max_length=128)
          │
          ▼
    ┌──────────────────┐
    │ Token Embedding  │ vocab_size → 768
    └──────┬───────────┘
           ▼
    ┌──────────────────┐
    │ Position Embed   │ Add positional info
    └──────┬───────────┘
           ▼
    ┌──────────────────┐
    │ DistilBERT       │ 6 transformer layers
    │ Encoder Layers   │ 12 attention heads
    │ (6 layers)       │ 768 hidden dim
    │ 3M parameters    │ (distilled from BERT)
    └──────┬───────────┘
           ▼
    ┌──────────────────┐
    │ [CLS] Token      │ Pooled output (768,)
    │ Representation   │
    └──────┬───────────┘
           ▼
    ┌──────────────────┐
    │ Linear Layer     │ 768 → 2 (binary)
    └──────┬───────────┘
           ▼
    ┌──────────────────┐
    │ Softmax          │
    └──────┬───────────┘
           ▼
    Text Scores: [P(Safe), P(Phish)]
    (normalized to [0, 1])
```

### Tier 3: Fusion Layer with Attention
```
Color CNN Output:  Visual_Score [0, 1]
                   └─→ Dense(64)
                       └─→ ReLU
                           └─→ Dense(16)
                               │
                               ▼
BERT Output:       Text_Score [0, 1]
                   └─→ Dense(64)
                       └─→ ReLU
                           └─→ Dense(16)
                               │
                               ▼
                   ┌────────────┴────────────┐
                   ▼                        ▼
            ┌────────────┐         ┌────────────┐
            │ Attention  │         │ Attention  │
            │ Query/Key  │         │ Value      │
            └────┬───────┘         └────┬───────┘
                 │                      │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────┐
                 │ Softmax Weights  │
                 │ w_v, w_t ∈ [0,1]│
                 │ w_v + w_t = 1   │
                 └────┬─────────────┘
                      ▼
        Fused_Score = w_v * visual + w_t * text
                      │
                      ▼
        ┌────────────────────────────┐
        │ Logistic Regression Layer  │
        │ Features: [Fused_Score,    │
        │            w_v, w_t, ...]  │
        └────┬───────────────────────┘
             ▼
        Final Classification:
        - Score [0, 1]
        - Confidence [0, 1]
```

---

## Data Flow Examples

### Example 1: SAFE URL (Tier 1)
```
User navigates to: wikipedia.org

Browser Extension:
├─ URL received in content.js
├─ Extract features (domain age: 20+ years)
├─ Send to Service Worker
│
Service Worker (background.js):
├─ Check Firebase Cache → MISS
├─ Prepare ONNX inference
├─ Call offscreen.js → ONNX Runtime
│
ONNX Inference:
├─ Input: [domain_age: 9, ssl: 1, ...]
├─ Forward pass through LightGBM
└─ Output Score: 0.15 (< 0.35)
│
Tier 1 Decision:
└─ SAFE (high confidence)
   └─ Return to extension
   └─ Update UI: ✅ SAFE
   └─ Cache in Firebase
```

**Total Latency:** ~50ms  
**Tier Used:** 0 + 1

---

### Example 2: Suspicious URL (Escalation)
```
User navigates to: suspicious-login.tk

Browser Extension:
├─ URL received in content.js
├─ Extract features (domain age: 2 days)
├─ Send to Service Worker
│
Service Worker (background.js):
├─ Check Firebase Cache → MISS
├─ ONNX Inference: Score = 0.52 (ambiguous)
│
Tier 1 Decision:
├─ 0.35 < 0.52 < 0.75 → Escalate
├─ Capture screenshot
├─ Extract OCR text: "Confirm your account"
├─ Extract HTML excerpt
│
Backend API (Tier 2):
├─ POST /analyze/cloud
├─ Safe Browsing Check: flagged as phishing
├─ Run Tabular Classifier: 0.78
├─ Confidence: 0.92 > 0.8 → Return verdict
│
Decision: PHISHING (confidence 92%)
├─ Send to extension
├─ Update UI: ⚠️ PHISHING
├─ Show explanation: "Recent domain, Safe Browsing flag"
└─ Cache in Firebase
```

**Total Latency:** ~600ms  
**Tier Used:** 0 + 1 + 2

---

### Example 3: Sophisticated Phishing (Full Cascade)
```
User navigates to: exact-replica-paypa1.com

Browser Extension:
├─ URL: looks-similar URL
├─ ONNX Score: 0.56 (ambiguous)
└─ Escalate to Tier 2

Backend (Tier 2):
├─ Safe Browsing: not flagged (brand new)
├─ Tabular Score: 0.62 (uncertain)
├─ Confidence: 0.55 < 0.8 → Escalate to Tier 3

Backend (Tier 3): Multimodal Fusion
├─ Screenshot Analysis:
│  ├─ Color grading CNN
│  ├─ Detects replica PayPal colors
│  └─ Visual Score: 0.89
│
├─ Text Analysis:
│  ├─ OCR: "Verify Account" (urgency language)
│  ├─ BERT fine-tuned model
│  └─ Text Score: 0.85
│
├─ Fusion:
│  ├─ Attention weights: 60% visual, 40% text
│  ├─ Fused Score: 0.87
│  └─ Confidence: 0.79 < 0.8 → Escalate to Tier 4

Backend (Tier 4): Gemini LLM
├─ Send context:
│  ├─ Raw HTML + layout
│  ├─ Screenshot
│  ├─ All prior scores
│  └─ Known phishing indicators
│
├─ Gemini Analysis:
│  ├─ Identifies visual mimicry
│  ├─ Detects social engineering language
│  ├─ Compares with known PayPal phishing patterns
│  └─ Verdict: PHISHING (99% confidence)
│
└─ LLM Reasoning:
   "Exact visual replica of PayPal with urgency language.
    Phishing signature matches known campaign patterns."

Final Response to Extension:
├─ Verdict: PHISHING ⛔
├─ Tier: 4 (Gemini LLM)
├─ Confidence: 99%
├─ Explanation: [LLM reasoning above]
├─ SHAP Features:
│  ├─ Urgency keywords: +0.35 (phishing indicator)
│  ├─ Visual mimicry: +0.42 (phishing indicator)
│  ├─ Domain age: +0.18 (phishing indicator)
│  └─ Safe Browsing: 0.0 (neutral, new domain)
└─ Block Site + Alert User
```

**Total Latency:** ~12 seconds  
**Tier Used:** 0 + 1 + 2 + 3 + 4 (Full cascade)

---

## Model File Locations & Artifacts

### Browser-Side Models (Tier 1)
```
extension/
├── lib/
│   ├── ort.wasm.min.js              # ONNX Runtime core (WASM)
│   ├── ort-wasm-threaded.js         # Multi-threaded WASM
│   └── ort-wasm-threaded.worker.js  # Worker thread
│
└── models/site_multimodal/
    ├── tier1_lightgbm.onnx          # Tier 1 model (quantized INT8)
    └── metadata.json                 # Model metadata
```

### Backend Models (Tiers 2-4)
```
extension/models/site_multimodal/
│
├── Tier 2:
│   ├── tier2_xgboost.pkl
│   ├── tier2_lightgbm.pkl
│   └── tier2_features.json
│
├── Tier 3:
│   ├── color_grading_cnn.pt         # PyTorch CNN
│   ├── fusion_model.joblib          # Sklearn fusion
│   ├── image_grade_model.joblib     # Feature extractor
│   │
│   └── text_model/                  # DistilBERT
│       ├── config.json              # Model config
│       ├── model.safetensors        # Weights (HF format)
│       ├── tokenizer.json           # Tokenizer
│       ├── checkpoint-9/            # Training checkpoint
│       ├── checkpoint-88/           # Training checkpoint
│       ├── checkpoint-500/          # Training checkpoint
│       └── checkpoint-745/          # Final checkpoint
│
├── Metadata:
│   ├── metadata.json                # Training stats
│   ├── train.csv / val.csv / test.csv
│   └── site_manifest_with_features.csv
```

---

## Performance Characteristics

### Latency by Tier
```
Tier 0 (Cache): ────────────────────────────────────────── 1-2ms
                █ (instant hit)

Tier 1 (Edge):  ────────────────────────────────────── 10-20ms
                ████ (sub-20ms WASM)

Tier 2 (Cloud): ─────────────────────────── 400-700ms
                ███████████████

Tier 3 (Fusion):─────────── 1-3 seconds
                ██████████████████████████

Tier 4 (LLM):   ─ 5-15 seconds
                ███████████████████████████████████
```

### Accuracy by Tier
```
Tier 1 (Edge):        ██████████░░░░░░░░░░ 88%
Tier 2 (Cloud):       ███████████░░░░░ 94%
Tier 3 (Fusion):      ████████████░░░░ 96%
Tier 4 (Gemini):      ██████████████░░ 99%+
```

### Load Distribution (Estimated)
```
Tier 0 Cache Hit:     ████████░░░░░░░░░░░░ 40% of URLs
Tier 1 (Edge):        █████░░░░░░░░░░░░░░░ 25% of URLs
Tier 2 (Cloud):       ████░░░░░░░░░░░░░░░░ 20% of URLs
Tier 3 (Fusion):      ██░░░░░░░░░░░░░░░░░░ 12% of URLs
Tier 4 (LLM):         █░░░░░░░░░░░░░░░░░░░ 3% of URLs

(Cascade reduces load on expensive tiers)
```

---

## Deployment Architecture

```
┌────────────────────────────────────────────────────────────┐
│              Chrome Web Store (Extension)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ PhishGuard++ Extension (Manifest V3)                 │  │
│  │ - Automatically syncs models from GCS                │  │
│  │ - Updates: weekly model refreshes                    │  │
│  └──────────────┬───────────────────────────────────────┘  │
└─────────────────┼─────────────────────────────────────────┘
                  │
        ┌─────────▼─────────────────────────┐
        │  Google Cloud Storage (GCS)       │
        │  phishguard-models bucket         │
        │  ├─ onnx/tier1_model.onnx        │
        │  ├─ tier2/xgboost.pkl            │
        │  ├─ tier3/models.tar.gz          │
        │  └─ metadata.json                │
        └─────────────────────────────────┘
                  │
        ┌─────────▼──────────────────────────────┐
        │ Google Cloud Run (Backend)            │
        │ ┌────────────────────────────────────┐│
        │ │ phishguard-backend service         ││
        │ ├─ FastAPI (Python 3.11)            ││
        │ ├─ Auto-scales: 0 → N instances    ││
        │ ├─ Timeout: 60 seconds              ││
        │ ├─ Memory: 2GB per instance         ││
        │ └─ Cold start: ~5 seconds           ││
        │                                     │ │
        │ ├─ /health (GET)                   │ │
        │ ├─ /analyze/cloud (POST)           │ │
        │ ├─ /analyze/multimodal (POST)      │ │
        │ └─ /explain (POST)                 │ │
        └─────────────────────────────────────┘
                  │
        ┌─────────┴────────────────────────┐
        │                                  │
    ┌───▼──────────┐          ┌───────────▼───┐
    │ Firebase RT  │          │ Google APIs   │
    │ Database     │          │ - Gemini API  │
    │ - Community  │          │ - Safe        │
    │   Verdict    │          │   Browsing    │
    │   Cache      │          │ - Vision API  │
    │ - Statistics │          │ - Cloud Auth  │
    └──────────────┘          └───────────────┘
```

---

**End of Architecture Guide**

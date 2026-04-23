# PhishGuard++ Documentation Index

**Complete Documentation Suite for v2.0**  
**Last Updated:** April 23, 2026

---

## 📚 Documentation Map

```
PhishGuard++
│
├── README.md ⭐ START HERE
│   ├─ Project Overview
│   ├─ Architecture (5-tier cascade with diagrams)
│   ├─ Tech Stack (detailed breakdown)
│   ├─ Project Structure (complete file tree)
│   ├─ Getting Started (setup instructions)
│   ├─ API Endpoints (full documentation)
│   ├─ Model Specifications (technical details)
│   ├─ Performance Metrics (benchmarks)
│   ├─ Troubleshooting (common issues)
│   └─ License & References
│
├── ARCHITECTURE.md 📊 FOR DEEP UNDERSTANDING
│   ├─ Complete System Architecture (ASCII diagrams)
│   ├─ Tier-by-Tier Data Flow (with examples)
│   ├─ Model Architecture Diagrams
│   │  ├─ Tier 3 Color CNN
│   │  ├─ Tier 3 BERT Text Classifier
│   │  └─ Tier 3 Fusion Layer with Attention
│   ├─ Data Flow Examples
│   │  ├─ Example 1: SAFE URL (Tier 1)
│   │  ├─ Example 2: Suspicious URL (Escalation)
│   │  └─ Example 3: Sophisticated Phishing (Full Cascade)
│   ├─ Model File Locations
│   └─ Performance Characteristics (latency, accuracy, load)
│
├── QUICKREF.md ⚡ QUICK COMMANDS
│   ├─ Quick Start Commands
│   ├─ Common Development Tasks
│   ├─ Debugging Guide
│   ├─ Testing Checklist
│   ├─ API Endpoint Reference
│   ├─ Key Thresholds
│   ├─ Dependency Management
│   └─ Emergency Procedures
│
├── README_UPDATES.md 📝 CHANGELOG
│   ├─ Overview of Changes (v1.0 → v2.0)
│   ├─ Major Sections Updated (15 sections)
│   ├─ Statistics (850+ lines, 8 new sections)
│   └─ Quality Improvements
│
├── MULTIMODAL_ENHANCEMENT.md 🏛️ ARCHIVED
│   └─ Original technical specifications
│       (Reference for historical context)
│
└── Source Code Documentation
    ├─ backend/main.py - FastAPI server implementation
    ├─ backend/firebase_db.py - Firebase integration
    ├─ extension/background.js - Extension service worker
    ├─ src/models/site_multimodal.py - Core model
    ├─ src/models/attention_fusion.py - Fusion layer
    ├─ src/explainability/shap_pipeline.py - Explanations
    └─ train_multimodal.py - Training orchestration
```

---

## 🎯 Documentation by Use Case

### 👤 I'm a New Developer
**Read in this order:**
1. [README.md](README.md) - Project overview
2. [QUICKREF.md](QUICKREF.md) - Quick start commands
3. [ARCHITECTURE.md](ARCHITECTURE.md) - Understanding the system
4. Source code files in `src/` directory

### 🔬 I'm a Researcher
**Read in this order:**
1. [README.md](README.md#performance-metrics) - Performance metrics
2. [ARCHITECTURE.md](ARCHITECTURE.md) - Model specifications
3. [MULTIMODAL_ENHANCEMENT.md](MULTIMODAL_ENHANCEMENT.md) - Technical foundation
4. Source code: `src/models/` and `src/evaluation/`

### 🚀 I'm Deploying to Production
**Read in this order:**
1. [README.md](README.md#getting-started) - Getting started
2. [README.md](README.md#docker-deployment) - Docker deployment
3. [QUICKREF.md](QUICKREF.md#emergency-procedures) - Emergency procedures
4. `.env` configuration guide in README

### 🐛 I'm Debugging an Issue
**Check immediately:**
1. [QUICKREF.md](QUICKREF.md#debugging-issues) - Common debugging
2. [README.md](README.md#troubleshooting) - Troubleshooting guide
3. [QUICKREF.md](QUICKREF.md#emergency-procedures) - Emergency procedures

### 📊 I Want to Understand the Architecture
**Read in this order:**
1. [README.md](README.md#architecture) - Architecture overview with Mermaid diagram
2. [ARCHITECTURE.md](ARCHITECTURE.md#complete-system-architecture) - Complete system diagrams
3. [ARCHITECTURE.md](ARCHITECTURE.md#tier-by-tier-data-flow) - Detailed tier information
4. [ARCHITECTURE.md](ARCHITECTURE.md#data-flow-examples) - Real-world examples

### 🎓 I'm Learning About the Models
**Read in this order:**
1. [README.md](README.md#model-specifications) - Overview
2. [ARCHITECTURE.md](ARCHITECTURE.md#model-architecture-diagrams) - Visual diagrams
3. [ARCHITECTURE.md](ARCHITECTURE.md#tier-by-tier-data-flow) - Model usage details
4. Source code: `src/models/site_multimodal.py`

### 🛠️ I'm Contributing Code
**Read in this order:**
1. [QUICKREF.md](QUICKREF.md#common-development-tasks) - Development workflow
2. [README.md](README.md#development-workflow) - Contributing guidelines
3. [README.md](README.md#contributing) - Pull request process
4. `src/` source code for reference

---

## 🔍 Quick Reference Guide

### File Locations

| What I'm Looking For | Where to Find It |
|---------------------|------------------|
| Project overview | [README.md](README.md) |
| Setup instructions | [README.md](README.md#getting-started) |
| API documentation | [README.md](README.md#api-endpoints-backend) |
| Architecture details | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Quick commands | [QUICKREF.md](QUICKREF.md) |
| Troubleshooting | [README.md](README.md#troubleshooting) |
| Model details | [ARCHITECTURE.md](ARCHITECTURE.md#model-architecture-diagrams) |
| Performance metrics | [README.md](README.md#performance-metrics) |
| What changed in v2.0 | [README_UPDATES.md](README_UPDATES.md) |
| Code examples | [QUICKREF.md](QUICKREF.md) |

### Key Sections

#### Architecture Understanding
- 5-tier cascade: [README.md](README.md#architecture-the-5-tier-cascade)
- Tier descriptions: [README.md](README.md#the-tiers-explained)
- Cascade logic: [README.md](README.md#cascade-decision-logic)
- Complete system: [ARCHITECTURE.md](ARCHITECTURE.md#complete-system-architecture)

#### Getting Started
- Prerequisites: [README.md](README.md#prerequisites)
- Backend setup: [README.md](README.md#1-backend-setup-tier-2-3-4-cloud-services)
- Training models: [README.md](README.md#2-training-models-tier-1--3)
- Extension install: [README.md](README.md#3-extension-installation-tier-1-edge-inference)
- Testing: [README.md](README.md#4-testing--evaluation)
- Docker: [README.md](README.md#5-docker-deployment-google-cloud-run)

#### Development
- Quick start: [QUICKREF.md](QUICKREF.md#-quick-start-commands)
- Common tasks: [QUICKREF.md](QUICKREF.md#-common-development-tasks)
- Contributing: [README.md](README.md#contributing)
- Workflow: [README.md](README.md#development-workflow)

#### Troubleshooting
- Backend issues: [README.md](README.md#backend-issues)
- Extension issues: [README.md](README.md#extension-issues)
- Debugging tips: [QUICKREF.md](QUICKREF.md#-debugging-issues)
- Emergency: [QUICKREF.md](QUICKREF.md#-emergency-procedures)

---

## 📖 Section Deep Dives

### Understanding Each Tier

#### Tier 0: Community Cache
- **Where:** Firebase Realtime Database
- **Speed:** < 1ms (cache hit)
- **Location:** [ARCHITECTURE.md#tier-0-community-cache-firebase](ARCHITECTURE.md)

#### Tier 1: Edge Inference
- **Where:** Browser (extension)
- **Technology:** ONNX Runtime (WASM)
- **Speed:** < 15ms
- **Files:** `extension/background.js`, `extension/offscreen.js`
- **Location:** [ARCHITECTURE.md#tier-1-edge-inference-browser](ARCHITECTURE.md)

#### Tier 2: Cloud Analysis
- **Where:** Backend server
- **Technology:** Safe Browsing API + XGBoost/LightGBM
- **Speed:** < 500ms
- **Files:** `backend/main.py`
- **Location:** [ARCHITECTURE.md#tier-2-cloud-analysis-backend](ARCHITECTURE.md)

#### Tier 3: Multimodal Fusion
- **Where:** Backend server
- **Technology:** Color CNN + DistilBERT + Attention
- **Speed:** < 2 seconds
- **Files:** `src/models/site_multimodal.py`
- **Location:** [ARCHITECTURE.md#tier-3-multimodal-fusion-backend](ARCHITECTURE.md)

#### Tier 4: Gemini LLM
- **Where:** Google Cloud (via API)
- **Technology:** Google Gemini 2.5 Flash
- **Speed:** < 10 seconds
- **Files:** `backend/main.py` (LLM integration)
- **Location:** [ARCHITECTURE.md#tier-4-gemini-llm-analysis-backend](ARCHITECTURE.md)

### Understanding Each Component

#### Extension (Tier 1)
- **Purpose:** Runs phishing detection locally in browser
- **Language:** JavaScript
- **Location:** `extension/` directory
- **Documentation:** [README.md](README.md#3-extension-installation-tier-1-edge-inference)
- **Key Files:** `background.js`, `offscreen.js`, `content.js`

#### Backend (Tiers 2-4)
- **Purpose:** Cloud inference and orchestration
- **Language:** Python (FastAPI)
- **Location:** `backend/` directory
- **Documentation:** [README.md](README.md#1-backend-setup-tier-2-3-4-cloud-services)
- **Key Files:** `main.py`, `firebase_db.py`

#### Models (Tier 3)
- **Purpose:** Deep learning classification
- **Languages:** PyTorch (Python)
- **Location:** `src/models/` and `extension/models/site_multimodal/`
- **Documentation:** [ARCHITECTURE.md#model-architecture-diagrams](ARCHITECTURE.md)
- **Key Files:** `site_multimodal.py`, `attention_fusion.py`

#### Feature Extraction
- **Purpose:** Extract features from URLs and HTML
- **Language:** Python
- **Location:** `src/features/` directory
- **Documentation:** [README.md](README.md#project-structure)
- **Key Files:** `extract_all.py`, `url_features.py`, `html_features.py`

#### Explainability
- **Purpose:** Generate human-readable explanations
- **Technology:** SHAP (SHapley Additive exPlanations)
- **Language:** Python
- **Location:** `src/explainability/` directory
- **Documentation:** [README.md](README.md#explainability--interpretability)
- **Key Files:** `shap_pipeline.py`

---

## 📊 Model Training Pipeline

```
Dataset Preparation
    ↓
Feature Extraction (URL + HTML + Screenshot)
    ↓
┌─ Color Grading CNN Training
├─ BERT Text Classifier Fine-tuning
└─ Fusion Model Learning
    ↓
Evaluation (F1, AUC-ROC, Precision, Recall)
    ↓
Model Export (PyTorch .pt + ONNX)
    ↓
Deployment (Chrome Extension + Backend)
```

**Documentation:** [ARCHITECTURE.md#tier-3-multimodal-fusion-backend](ARCHITECTURE.md)

---

## 🚀 Deployment Architecture

```
User's Chrome Browser
    ↓
PhishGuard++ Extension (Manifest V3)
    ↓
    ├─ Cache Hit (Tier 0)
    │  └─ Return from Firebase
    │
    └─ Cache Miss
       ↓
       ONNX Inference (Tier 1)
           ↓
           ├─ High Confidence
           │  └─ Return verdict
           │
           └─ Low Confidence
              ↓
              Backend (Google Cloud Run)
                 ├─ Tier 2: Safe Browsing API + Tabular
                 ├─ Tier 3: Multimodal Fusion
                 └─ Tier 4: Gemini LLM
```

**Documentation:** [ARCHITECTURE.md#deployment-architecture](ARCHITECTURE.md)

---

## 📋 Command Reference by Task

### Training
```bash
python train_multimodal.py --train
python train_multimodal.py --train --epochs 10 --max-samples 50000
```
**Read:** [README.md#2-training-models-tier-1--3](README.md) + [QUICKREF.md#model-training](QUICKREF.md)

### Backend
```bash
python -m uvicorn backend.main:app --reload
python -m uvicorn backend.main:app --workers 4
```
**Read:** [README.md#14-run-backend-server](README.md) + [QUICKREF.md#backend-development](QUICKREF.md)

### Testing
```bash
python test_backend.py
python test_production.py
```
**Read:** [README.md#4-testing--evaluation](README.md) + [QUICKREF.md#-testing-checklist](QUICKREF.md)

### Docker
```bash
docker build -t phishguard-backend .
docker run -p 8000:8080 phishguard-backend
```
**Read:** [README.md#5-docker-deployment-google-cloud-run](README.md) + [QUICKREF.md#docker--cloud](QUICKREF.md)

---

## 🤔 FAQ - Documentation

**Q: Where do I start?**  
A: Read [README.md](README.md) first for overview. Then pick your use case above.

**Q: How do I set up locally?**  
A: Follow [README.md#getting-started](README.md#getting-started)

**Q: I need to understand the architecture quickly**  
A: Check [README.md#architecture](README.md#architecture) then [ARCHITECTURE.md](ARCHITECTURE.md)

**Q: I want to train models**  
A: See [README.md#2-training-models-tier-1--3](README.md#2-training-models-tier-1--3)

**Q: How do I deploy?**  
A: Follow [README.md#5-docker-deployment-google-cloud-run](README.md#5-docker-deployment-google-cloud-run)

**Q: Something broke, help!**  
A: Check [README.md#troubleshooting](README.md#troubleshooting) and [QUICKREF.md#emergency-procedures](QUICKREF.md#emergency-procedures)

**Q: How do I contribute?**  
A: Read [README.md#contributing](README.md#contributing) and [QUICKREF.md#common-development-tasks](QUICKREF.md#common-development-tasks)

**Q: What changed in v2.0?**  
A: See [README_UPDATES.md](README_UPDATES.md)

---

## 📞 Documentation Maintenance

### How to Update Documentation
1. Edit the relevant `.md` file
2. Update [README_UPDATES.md](README_UPDATES.md) with changes
3. Update this index if sections changed
4. Test examples before committing

### Documentation Standards
- Use Markdown formatting
- Include code examples where applicable
- Add links to related sections
- Keep content up-to-date with actual code
- Use clear, concise language

---

## 🔗 External Resources

### Official Frameworks & Libraries
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PyTorch Documentation](https://pytorch.org/)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers/)
- [Google Cloud Documentation](https://cloud.google.com/docs)
- [Firebase Documentation](https://firebase.google.com/docs)

### Related Papers & References
- DistilBERT: Sanh et al., 2019
- SHAP: Lundberg & Lee, 2017
- CTGAN: Xu et al., 2019
- ONNX: Microsoft & Facebook, 2019

---

## ✅ Documentation Checklist

When adding new features, ensure:
- [ ] Updated [README.md](README.md)
- [ ] Updated [ARCHITECTURE.md](ARCHITECTURE.md) if architecture changed
- [ ] Updated [QUICKREF.md](QUICKREF.md) with new commands
- [ ] Updated [README_UPDATES.md](README_UPDATES.md)
- [ ] Added inline code documentation
- [ ] Added examples in docstrings
- [ ] Updated this index if new sections added

---

**Last Updated:** April 23, 2026  
**Documentation Version:** 2.0  
**Status:** Current & Complete

📖 **Happy Reading!**

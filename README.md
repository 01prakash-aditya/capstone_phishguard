# PhishGuard++ 🛡️

**PhishGuard++** is a multi-modal, 3-tier cascade phishing detection system designed for real-time protection across Edge, Cloud, and LLM (Gemini) layers.

## 🚀 Pillars of PhishGuard++
1. **Tier 1 (Edge):** sub-100ms URL lexical analysis using LightGBM quantized to ONNX (INT8).
2. **Tier 2 (Cloud):** Structural HTML analysis using a Variational Autoencoder (VAE) and XGBoost.
3. **Tier 3 (Multi-modal):** Deep semantic analysis using Gemini 1.5 Flash and BERT (PhishBERT/CodeBERT).

## 🛠️ Architecture
- **Frontend:** Chrome Extension (Manifest V3, ONNX Runtime Web/Wasm).
- **Backend:** FastAPI (Python), PyTorch, ONNX, HuggingFace.
- **Data:** 394k sample unified dataset (PhishTank, UCI, PhiUSIIL, Tranco, Mendeley).

## 📂 Project Structure
- `/src`: Core Python source code (Data, Features, Models, API).
- `/extension`: Chrome Extension source (HTML/JS/CSS/Models).
- `/datasets`: Unified phishing data (Ignored in Git).
- `/models`: Trained model artifacts (Ignored in Git, see ONNX export).
- `/papers`: Research foundations.

## 🏁 Getting Started
1. `pip install -r requirements.txt`
2. `python -m src.data.dataset_builder`
3. `python -m src.features.extract_all` (Background process)
4. `python deploy_check.py`

## ⚖️ License
MIT License — Part of the Solutions Challenge 2026.

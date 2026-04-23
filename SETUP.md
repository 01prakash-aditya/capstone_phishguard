# PhishGuard++ Setup & Configuration Guide

## Prerequisites

- Python 3.9+
- pip or conda
- Chrome browser (for extension testing)
- Git

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/01prakash-aditya/capstone_phishguard.git
cd capstone_phishguard
```

### 2. Create Virtual Environment

```bash
# Using venv
python -m venv .venv

# Activate on Windows
.venv\Scripts\activate

# Activate on macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### A. Firebase Setup (Optional for Community Features)

The application can run without Firebase, but community reporting features will be disabled.

**To enable Firebase:**

1. Create a Firebase project at [https://firebase.google.com/](https://firebase.google.com/)
2. Create a Firestore database
3. Generate a service account key:
   - Go to Project Settings → Service Accounts
   - Click "Generate New Private Key"
   - Download the JSON file

4. Copy the template and add your credentials:
   ```bash
   cp firebase_credentials.json.example firebase_credentials.json
   # Edit firebase_credentials.json with your actual Firebase credentials
   ```

5. **DO NOT commit `firebase_credentials.json` to git** (it's in .gitignore)

### B. Environment Variables

1. Create `.env` file from template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```
   FIREBASE_CREDENTIALS_PATH=./firebase_credentials.json
   SAFE_BROWSING_API_KEY=your_google_safe_browsing_key
   GEMINI_API_KEY=your_google_gemini_api_key
   ```

### C. LightGBM Model (Optional for Tier 2 Classification)

The backend can run without the LightGBM model, but Tier 2 classification will return default scores.

**To add the model:**

1. Train or download the LightGBM model
2. Save as: `models/lightgbm_stage1.pkl`
3. The backend will automatically load it on startup

If missing, you'll see:
```
Model not found at .../models/lightgbm_stage1.pkl
```
This is a warning only—the backend will continue with fallback scoring.

## Running the Backend

### Development Mode

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Mode

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Main Analysis Endpoint

```
POST /analyze/cloud
```

**Request:**
```json
{
  "url": "https://example.com",
  "htmlExcerpt": "<html>...</html>",
  "screenshotBase64": "data:image/jpeg;base64,...",
  "features": {
    "domain_length": 15,
    "has_special_chars": 1,
    ...
  }
}
```

**Response:**
```json
{
  "verdict": "SAFE" | "PHISH" | "ERROR",
  "score": 0.0,
  "tier": 1,
  "reason": "Explanation of the verdict"
}
```

### Community Trust Check

```
GET /community/check?url=https://example.com
```

**Response:**
```json
{
  "found": false,
  "report_count": 0,
  "reasons": [],
  "verdict": "PENDING"
}
```

### Report Malicious URL

```
POST /community/report
```

**Request:**
```json
{
  "url": "https://example.com",
  "reason": "Optional reason"
}
```

## Troubleshooting

### Issue: Firebase Credentials not found

```
2026-04-23 23:01:24,441 [ERROR] Firebase Credentials not found
```

**Solution:**
- Copy `firebase_credentials.json.example` to `firebase_credentials.json`
- Add your actual Firebase service account credentials
- Or disable community features (they'll work in fallback mode)

### Issue: Model not found

```
Model not found at .../models/lightgbm_stage1.pkl
```

**Solution:**
- This is a warning, not an error
- The backend will use fallback scoring (0.5)
- To fix: Train/download the model and place at `models/lightgbm_stage1.pkl`

### Issue: API Keys not configured

```
WARNING: Gemini API key not configured - Tier 3 will be unavailable
```

**Solution:**
- Add your API keys to `.env` file
- Or the backend will use fallback Tier 3 scoring

## Testing

### Test Backend Health

```bash
curl http://localhost:8000/docs  # Swagger UI
```

### Test Analysis Endpoint

```bash
curl -X POST http://localhost:8000/analyze/cloud \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "htmlExcerpt": "<html></html>",
    "features": {}
  }'
```

## Architecture

The backend implements a 4-tier cascade:

1. **Tier 1.5**: Google Safe Browsing API (blacklist check)
2. **Tier 2**: LightGBM classifier (URL + HTML features)
3. **Tier 3**: Multimodal fusion (tabular + visual + text)
4. **Tier 4**: Gemini LLM (fallback for ambiguous cases)

Each tier is optional—missing components gracefully degrade to fallback scoring.

## Performance Tips

- Use `--reload` only in development
- In production, use a reverse proxy (nginx) for SSL/compression
- Configure firewall to restrict backend access
- Use environment variables for all secrets

## Documentation

- See [README.md](README.md) for project overview
- See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- See [QUICKREF.md](QUICKREF.md) for command reference

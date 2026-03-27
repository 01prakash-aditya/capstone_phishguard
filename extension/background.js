// PhishGuard++ Background Service Worker
// Orchestrates the 3-tier cascade architecture

import * as ort from './lib/onnxruntime-web.min.js';

// Configuration
const CONFIG = {
  TIER1_THRESHOLD: 0.35, // Score < 0.35 is SAFE
  PHISH_THRESHOLD: 0.75, // Score > 0.75 is PHISH
  BACKEND_URL: 'http://localhost:8000', // Move to .env/config later
};

let session = null;

// Initialize ONNX Runtime
async function initModel() {
  try {
    session = await ort.InferenceSession.create('./models/phishguard_edge.onnx', {
      executionProviders: ['wasm'],
    });
    console.log('✅ PhishGuard++ Tier 1 (ONNX) Loaded Successfully');
  } catch (e) {
    console.error('❌ Failed to load ONNX model:', e);
  }
}

// Extract lexical features from URL (mirroring Python logic)
function extractUrlFeatures(url) {
  const features = new Float32Array(20);
  const parsed = new URL(url.startsWith('http') ? url : `https://${url}`);
  
  // 1. url_length
  features[0] = url.length;
  // 2. domain_length
  features[1] = parsed.hostname.length;
  // ... implement remaining 18 lexical features (simplified for Tier 1)
  
  return features;
}

// ── Cascade Logic ──────────────────────────────────────────────
async function analyzeUrl(url, htmlExcerpt) {
  // Step 1: Tier 1 (Edge - ONNX)
  if (!session) await initModel();
  
  const features = extractUrlFeatures(url);
  const tensor = new ort.Tensor('float32', features, [1, 20]);
  
  let score = 0.5;
  try {
    const outputs = await session.run({ float_input: tensor });
    score = outputs.label.data[0]; // Assuming standard classifier output
  } catch (e) {
    console.warn('Tier 1 failed, escalating to Tier 2:', e);
  }

  // Tier 1 Verdict
  if (score < CONFIG.TIER1_THRESHOLD) return { verdict: 'SAFE', score, tier: 1 };
  if (score > CONFIG.PHISH_THRESHOLD) return { verdict: 'PHISH', score, tier: 1 };

  // Step 2: Escalate to Tier 2 (Cloud - FastAPI)
  return await escalateToTier2(url, htmlExcerpt);
}

async function escalateToTier2(url, htmlExcerpt) {
  try {
    const response = await fetch(`${CONFIG.BACKEND_URL}/analyze/cloud`, {
      method: 'POST',
      body: JSON.stringify({ url, htmlExcerpt }),
      headers: { 'Content-Type': 'application/json' },
    });
    return await response.json();
  } catch (e) {
    return { verdict: 'ERROR', error: 'Cloud offline', tier: 2 };
  }
}

// Initialize on start
initModel();

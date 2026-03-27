// PhishGuard++ Popup Logic

document.addEventListener('DOMContentLoaded', async () => {
  const statusBadge = document.getElementById('status-badge');
  const verdictText = document.getElementById('verdict-text');
  const riskPercent = document.getElementById('risk-percent');
  const gaugeFill = document.getElementById('gauge-fill');
  const activeTier = document.getElementById('active-tier');
  const explanation = document.getElementById('explanation');

  // 1. Get current active tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  if (!tab || !tab.url || tab.url.startsWith('chrome://')) {
    statusBadge.innerText = 'Inactive';
    verdictText.innerText = 'Protected Page';
    explanation.innerText = 'PhishGuard++ is active but does not scan internal browser pages for privacy.';
    return;
  }

  // 2. Request DOM features from content script
  chrome.tabs.sendMessage(tab.id, { action: 'extract_features' }, async (response) => {
    if (chrome.runtime.lastError || !response) {
      statusBadge.innerText = 'Error';
      verdictText.innerText = 'Connection Lost';
      explanation.innerText = 'Please refresh the page to enable real-time protection.';
      return;
    }

    const { url, features, excerpt } = response;

    // 3. Send to background for 3-tier analysis
    chrome.runtime.sendMessage({ action: 'analyze', url, features, excerpt }, (result) => {
      updateUI(result);
    });
  });
});

function updateUI(result) {
  const { verdict, score, tier, reason } = result;
  
  // Update elements
  const verdictText = document.getElementById('verdict-text');
  const riskPercent = document.getElementById('risk-percent');
  const gaugeFill = document.getElementById('gauge-fill');
  const activeTier = document.getElementById('active-tier');
  const explanation = document.getElementById('explanation');
  const statusBadge = document.getElementById('status-badge');

  const percent = Math.round(score * 100);
  riskPercent.innerText = `${percent}%`;
  
  // Simple SVG Gauge logic (126 is approx half circumference)
  const offset = 126 - (percent / 100) * 126;
  gaugeFill.style.strokeDasharray = `${126 - offset}, 126`;

  verdictText.innerText = verdict;
  activeTier.innerText = `Tier ${tier} (${tier === 1 ? 'Edge' : tier === 2 ? 'Cloud' : 'Gemini'})`;
  explanation.innerText = reason || getDefaultReason(verdict, tier);

  // Styling based on risk
  if (score < 0.35) {
    gaugeFill.style.stroke = '#10b981';
    statusBadge.style.borderColor = '#10b981';
    statusBadge.innerText = 'Secure';
    verdictText.className = 'safe';
  } else if (score < 0.75) {
    gaugeFill.style.stroke = '#f59e0b';
    statusBadge.style.borderColor = '#f59e0b';
    statusBadge.innerText = 'Suspicious';
    verdictText.className = 'warn';
  } else {
    gaugeFill.style.stroke = '#ef4444';
    statusBadge.style.borderColor = '#ef4444';
    statusBadge.innerText = 'Danger';
    verdictText.className = 'danger';
  }
}

function getDefaultReason(verdict, tier) {
  if (verdict === 'SAFE') return 'No malicious patterns detected. Tier 1 on-device validation successful.';
  if (verdict === 'PHISH') return 'High-confidence phishing indicators found in URL/HTML structure.';
  return 'Site analysis ongoing or inconclusive. Exercise caution.';
}

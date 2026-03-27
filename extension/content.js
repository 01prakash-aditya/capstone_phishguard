// PhishGuard++ Content Script
// Extracts structural features and DOM signals from the active tab

/**
 * Extracts 20 structural features from the current page.
 * (Syncing with src/features/html_features.py)
 */
function extractHtmlFeatures() {
  const features = {};
  const originDomain = window.location.hostname.toLowerCase();

  const isExternal = (url) => {
    if (!url || url.startsWith('/') || url.startsWith('#') || url.startsWith('?')) return false;
    if (url.startsWith('javascript:') || url.startsWith('mailto:')) return false;
    try {
      const linkDomain = new URL(url).hostname.toLowerCase();
      return !linkDomain.includes(originDomain) && !originDomain.includes(linkDomain);
    } catch (e) {
      return false;
    }
  };

  // 1. form_action_external
  const forms = Array.from(document.forms);
  features.form_action_external = forms.some(f => isExternal(f.action)) ? 1 : 0;

  // 2. iframe_count
  features.iframe_count = document.querySelectorAll('iframe').length;

  // 3. hidden_input_count
  features.hidden_input_count = document.querySelectorAll('input[type="hidden"]').length;

  // 4. external_link_ratio
  const links = Array.from(document.querySelectorAll('a[href]'));
  if (links.length > 0) {
    const externalCount = links.filter(a => isExternal(a.getAttribute('href'))).length;
    features.external_link_ratio = externalCount / links.length;
  } else {
    features.external_link_ratio = 0;
  }

  // 5. script_count
  features.script_count = document.querySelectorAll('script').length;

  // 7. login_form_present
  const passwords = document.querySelectorAll('input[type="password"]');
  features.login_form_present = passwords.length > 0 ? 1 : 0;
  features.password_field_count = passwords.length;

  // 12. copyright_year_present
  const bodyText = document.body.innerText;
  features.copyright_year_present = /(?:©|copyright)\s*\d{4}/i.test(bodyText) ? 1 : 0;

  // 14. page_size_bytes (approx)
  features.page_size_bytes = document.documentElement.innerHTML.length;

  // 18. image_count
  features.image_count = document.querySelectorAll('img').length;

  return features;
}

/**
 * Smart excerpt for CodeBERT/Gemini
 */
function getHtmlExcerpt() {
  const parts = [];
  const head = document.head.innerHTML.substring(0, 500);
  parts.push(head);

  Array.from(document.forms).forEach(f => parts.push(f.outerHTML.substring(0, 500)));
  Array.from(document.querySelectorAll('a')).slice(0, 10).forEach(a => parts.push(a.outerHTML));
  
  return parts.join('\n').substring(0, 2000);
}

// Listen for analysis requests from popup/background
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extract_features') {
    const features = extractHtmlFeatures();
    const excerpt = getHtmlExcerpt();
    sendResponse({ features, excerpt, url: window.location.href });
  }
  return true;
});

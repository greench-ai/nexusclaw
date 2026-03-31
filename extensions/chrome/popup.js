// NexusClaw Chrome Extension — popup.js

const DEFAULT_URL = 'http://localhost:19789';
let ws = null;
let connected = false;

// ── DOM refs ──────────────────────────────────────────────────────────────────
const statusDot       = document.getElementById('statusDot');
const connStatus      = document.getElementById('connStatus');
const gatewayUrl      = document.getElementById('gatewayUrl');
const btnConnect      = document.getElementById('btnConnect');
const btnSend         = document.getElementById('btnSend');
const btnClear        = document.getElementById('btnClear');
const btnSendSelection= document.getElementById('btnSendSelection');
const btnSendPage     = document.getElementById('btnSendPage');
const btnSendScreenshot=document.getElementById('btnSendScreenshot');
const messageInput    = document.getElementById('messageInput');
const toast           = document.getElementById('toast');
const openUI          = document.getElementById('openUI');

// ── Init ──────────────────────────────────────────────────────────────────────
chrome.storage.local.get(['gatewayUrl'], (result) => {
  if (result.gatewayUrl) gatewayUrl.value = result.gatewayUrl;
  else gatewayUrl.value = DEFAULT_URL;
  connect();
});

openUI.addEventListener('click', (e) => {
  e.preventDefault();
  chrome.tabs.create({ url: gatewayUrl.value });
});

// ── WebSocket Connection ──────────────────────────────────────────────────────
function connect() {
  const url = gatewayUrl.value.trim();
  const wsUrl = url.replace(/^http/, 'ws') + '/ws';

  if (ws) { ws.close(); ws = null; }

  setStatus('connecting');

  try {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      connected = true;
      setStatus('connected');
      chrome.storage.local.set({ gatewayUrl: url });
      showToast('Connected to NexusClaw', 'ok');
      enableButtons(true);
    };

    ws.onclose = () => {
      connected = false;
      setStatus('disconnected');
      enableButtons(false);
      ws = null;
    };

    ws.onerror = () => {
      connected = false;
      setStatus('error');
      enableButtons(false);
      showToast('Connection failed', 'err');
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'pong') {
          setStatus('connected');
        }
      } catch (_) {}
    };
  } catch (err) {
    setStatus('error');
    showToast('Invalid gateway URL', 'err');
  }
}

btnConnect.addEventListener('click', connect);

// ── Send Message ──────────────────────────────────────────────────────────────
async function sendMessage(text, prefix = '') {
  if (!connected || !ws) {
    showToast('Not connected to gateway', 'err');
    return;
  }
  const fullText = prefix ? `${prefix}\n\n${text}` : text;
  const payload = {
    type: 'agent.send',
    session: 'main',
    message: fullText,
  };
  ws.send(JSON.stringify(payload));
  showToast('Sent to NexusClaw ✓', 'ok');
}

btnSend.addEventListener('click', () => {
  const text = messageInput.value.trim();
  if (!text) return;
  sendMessage(text);
  messageInput.value = '';
});

btnClear.addEventListener('click', () => {
  messageInput.value = '';
});

messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
    btnSend.click();
  }
});

// ── Send Selection ────────────────────────────────────────────────────────────
btnSendSelection.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => window.getSelection()?.toString() ?? '',
  });
  if (!result || !result.trim()) {
    showToast('No text selected', 'err');
    return;
  }
  await sendMessage(result, `Selected text from ${tab.url}:`);
});

// ── Send Page ─────────────────────────────────────────────────────────────────
btnSendPage.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => ({
      url:   window.location.href,
      title: document.title,
      text:  document.body?.innerText?.slice(0, 8000) ?? '',
    }),
  });
  const content = `Page: ${result.title}\nURL: ${result.url}\n\n${result.text}`;
  await sendMessage(content, 'Current page content:');
});

// ── Send Screenshot ───────────────────────────────────────────────────────────
btnSendScreenshot.addEventListener('click', async () => {
  const dataUrl = await chrome.tabs.captureVisibleTab(null, { format: 'png' });
  // Send as message with URL — agent can fetch/view it
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  await sendMessage(`Screenshot of: ${tab.url}\n[Image captured — see browser]`, 'Screenshot:');
  showToast('Screenshot context sent', 'ok');
});

// ── Helpers ───────────────────────────────────────────────────────────────────
function setStatus(state) {
  statusDot.className = 'status-dot';
  if (state === 'connected') {
    statusDot.classList.add('connected');
    connStatus.textContent = 'Connected';
    btnConnect.textContent = 'Reconnect';
  } else if (state === 'connecting') {
    connStatus.textContent = 'Connecting...';
    btnConnect.textContent = 'Cancel';
  } else if (state === 'error') {
    connStatus.textContent = 'Error';
    btnConnect.textContent = 'Retry';
  } else {
    connStatus.textContent = 'Disconnected';
    btnConnect.textContent = 'Connect';
  }
}

function enableButtons(on) {
  btnSend.disabled = !on;
  btnSendSelection.disabled = !on;
  btnSendPage.disabled = !on;
  btnSendScreenshot.disabled = !on;
}

let toastTimer;
function showToast(msg, type = 'ok') {
  toast.textContent = msg;
  toast.className = `toast ${type} show`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.className = 'toast'; }, 2200);
}

// NexusClaw Chrome Extension — background.js (service worker)

const DEFAULT_URL = 'http://localhost:19789';

// ── Context Menu Setup ────────────────────────────────────────────────────────
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'nexusclaw-send-selection',
    title: 'Send to NexusClaw',
    contexts: ['selection'],
  });
  chrome.contextMenus.create({
    id: 'nexusclaw-send-page',
    title: 'Send page to NexusClaw',
    contexts: ['page'],
  });
  chrome.contextMenus.create({
    id: 'nexusclaw-send-link',
    title: 'Send link to NexusClaw',
    contexts: ['link'],
  });
  chrome.contextMenus.create({
    id: 'nexusclaw-send-image',
    title: 'Send image to NexusClaw',
    contexts: ['image'],
  });
});

// ── Context Menu Click ────────────────────────────────────────────────────────
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const { gatewayUrl } = await chrome.storage.local.get(['gatewayUrl']);
  const url = gatewayUrl || DEFAULT_URL;

  let message = '';

  switch (info.menuItemId) {
    case 'nexusclaw-send-selection':
      message = `Selected text from ${tab.url}:\n\n${info.selectionText}`;
      break;
    case 'nexusclaw-send-page':
      message = `Please read and summarize this page: ${tab.url}\nTitle: ${tab.title}`;
      break;
    case 'nexusclaw-send-link':
      message = `Please check this link: ${info.linkUrl}`;
      break;
    case 'nexusclaw-send-image':
      message = `Image URL: ${info.srcUrl}`;
      break;
  }

  if (message) {
    await sendToGateway(url, message);
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'NexusClaw',
      message: 'Sent to your agent ✓',
    });
  }
});

// ── Keyboard Commands ─────────────────────────────────────────────────────────
chrome.commands.onCommand.addListener(async (command) => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const { gatewayUrl } = await chrome.storage.local.get(['gatewayUrl']);
  const url = gatewayUrl || DEFAULT_URL;

  if (command === 'send-selection') {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => window.getSelection()?.toString() ?? '',
    });
    if (result?.trim()) {
      await sendToGateway(url, `Selected text from ${tab.url}:\n\n${result}`);
      notify('Selection sent to NexusClaw');
    }
  }

  if (command === 'send-page') {
    await sendToGateway(url, `Read this page: ${tab.url}\nTitle: ${tab.title}`);
    notify('Page sent to NexusClaw');
  }
});

// ── Helper: Send to Gateway REST endpoint ─────────────────────────────────────
async function sendToGateway(baseUrl, message) {
  try {
    await fetch(`${baseUrl}/api/agent/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session: 'main', message }),
    });
  } catch (err) {
    console.error('[NexusClaw] Failed to send to gateway:', err);
  }
}

function notify(message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: 'NexusClaw',
    message,
  });
}

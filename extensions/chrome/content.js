// NexusClaw Chrome Extension — content.js
// Injected into all pages. Minimal footprint — only activates when called.

// Listen for messages from popup or background
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === 'GET_SELECTION') {
    sendResponse({ text: window.getSelection()?.toString() ?? '' });
  }
  if (message.type === 'GET_PAGE_TEXT') {
    sendResponse({
      url:   window.location.href,
      title: document.title,
      text:  document.body?.innerText?.slice(0, 8000) ?? '',
    });
  }
  return true;
});

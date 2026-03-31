# web-search — Web Search Skill
> Bundled with NexusClaw.

## What This Skill Does

Enables real-time web search from within the NexusClaw gateway.
Uses Brave Search API (free tier available) or DuckDuckGo as fallback.

## Usage

The agent uses this automatically when it needs current information.
Or trigger explicitly:

```
Search for [query]
Find recent news about [topic]
Look up [thing]
```

## Config

`skills/web-search/config.json`:

```json
{
  "provider": "brave",
  "braveApiKey": "${BRAVE_SEARCH_API_KEY}",
  "fallback": "duckduckgo",
  "maxResults": 5,
  "includeSnippets": true
}
```

Add `BRAVE_SEARCH_API_KEY` to your `.env` for Brave Search.
Without it, falls back to DuckDuckGo (no API key needed).

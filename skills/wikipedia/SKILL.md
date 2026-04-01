---
name: wikipedia
description: Search and read Wikipedia articles for instant factual research. No API key required.
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - curl
---

# Wikipedia

Search Wikipedia and read articles directly. Free, no API key needed.

## Usage

```
Look up quantum computing on Wikipedia
Wikipedia summary of the French Revolution
What does Wikipedia say about cannabis?
Search Wikipedia for Nikola Tesla
```

## How to search

**Search for articles:**
`curl -s "https://en.wikipedia.org/w/api.php?action=opensearch&search={QUERY}&limit=5&format=json"`

**Get article summary:**
`curl -s "https://en.wikipedia.org/api/rest_v1/page/summary/{ARTICLE_TITLE}"`
Returns: title, extract (plain text summary), thumbnail URL, page URL.

**Get full article sections:**
`curl -s "https://en.wikipedia.org/w/api.php?action=parse&page={TITLE}&prop=sections|text&format=json"`

**Search with full text:**
`curl -s "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={QUERY}&format=json"`

## Languages

Replace `en.wikipedia.org` with `fr.wikipedia.org`, `de.wikipedia.org`, `es.wikipedia.org` etc. for other languages.

## Output format

For summaries:
```
📖 **{Title}**
{extract — first 3-4 sentences}

🔗 Read more: {page URL}
```

Always cite Wikipedia as the source.
Keep summaries concise — 3-5 sentences unless the user asks for more detail.
If multiple articles match, list the top 3 and ask which one they want.

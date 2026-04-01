---
name: summarize
description: Summarize any text, document, URL, or conversation. Multiple output formats. No API key needed — uses the built-in model.
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - curl
---

# Summarize

Condense any content into clear, structured summaries.
Works on text, files, URLs, and conversation history.
No external API — uses the agent's own model.

## Usage

```
Summarize this article: [URL or text]
TL;DR of the conversation so far
Summarize this document in 3 bullet points
Give me the key points from this
Executive summary of [topic]
Summarize my notes from today
```

## Summary types

**TL;DR** (1-2 sentences):
Trigger: "tl;dr", "quick summary", "in one sentence"
Output: The single most important point.

**Bullet summary** (5-7 points):
Trigger: "bullet points", "key points", "main points"
Output: Ordered list of most important facts/conclusions.

**Executive summary** (1 paragraph):
Trigger: "executive summary", "brief overview"
Output: Who/what/why/so-what in 4-5 sentences.

**Full summary** (structured):
Trigger: "full summary", "detailed summary", "summarize thoroughly"
Output: Sections with headers — Overview, Key Points, Details, Conclusions.

**Action items** (decisions + next steps):
Trigger: "action items", "what needs to happen", "next steps"
Output: Decisions made + actionable tasks extracted.

## How to handle URLs

If given a URL:
1. Fetch with `curl -sL {URL} | sed 's/<[^>]*>//g' | head -200`
2. Extract main text content
3. Summarize the extracted text

For complex pages: note that content may be incomplete due to JavaScript rendering.

## How to handle files

If given a file path:
1. Read the file content
2. If >10,000 words: chunk into sections, summarize each, then combine
3. If code: summarize what it does, not the implementation details
4. If markdown: use headers as natural section breaks

## Output guidelines

- Lead with the most important point
- Use active voice
- Cut filler words mercilessly
- Never pad to hit a word count
- If the source is unclear or low quality, say so
- Always specify what was summarized (URL, filename, or "the above conversation")

## Conversation summary

When asked to summarize the conversation:
1. Note the date/time range
2. List topics covered in order
3. Highlight decisions made
4. List open questions or unresolved items
5. Note next steps if discussed

Format:
```
📝 Conversation Summary — April 1, 2026

Topics covered:
• NexusClaw GitHub setup and logo placement
• Discovered that git clone = no fork needed
• Built 10 new custom skills

Decisions made:
• Use nexusclaw-build repo for testing
• Never publish to npm registry
• Fresh GreenchClaw build next session

Open items:
• GreenchClaw fresh build not started yet
• Install errors from NexusClaw still unresolved
```

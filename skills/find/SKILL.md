---
name: find
description: Search across all knowledge for this book — concepts, notes, quiz history, misconceptions. Use when the user runs /find, asks to "search for X", "find X in my notes", "look up X", or wants to locate something they studied.
argument-hint: "<query>"
allowed-tools: [Bash]
---

# /find — Search the Knowledge Base

## Step 1 — Identify the book

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py list
```

Use the most recently accessed book. If no books: tell user to run `/teach <pdf>` first.

## Step 2 — Get the query

The query is everything after `/find`. If no argument was given, ask:
> "What are you looking for?"

## Step 3 — Run search

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py search <slug> <query>
```

## Step 4 — Present results

**If results found**, show them clearly:

```
🔍 Results for "[query]" in [Book Title]

1. Concept: Replication  (score: 8.3)
   Chapter 5 · "The process of copying data across multiple nodes..."
   → You studied this on Jun 24. Mastery: 73%

2. Notes: chapter05.tex  (score: 6.1)
   "...replication lag can cause stale reads in asynchronous setups..."

3. Misconception  (score: 4.2)
   replication: "Confused synchronous vs asynchronous replication direction"
```

For each result:
- Show the source (concept / notes file / misconception)
- Show a relevant snippet (~1 sentence)
- For concepts: show mastery % if available and chapter number
- For misconceptions: show the concept it relates to

**If no results:**
```
No results found for "[query]".

Suggestions:
• Try a different keyword (e.g., "write-ahead" instead of "WAL")
• The concept may not have been taught yet — check /progress
• Run /teach to cover more of the book
```

## Step 5 — Offer to go deeper

After showing results, ask:
> "Want me to explain any of these in detail? Just say which one."

If the user picks one, either:
- Summarize the concept from the knowledge base
- Or redirect to the teaching flow: "Say 'teach replication' and I'll walk you through it."

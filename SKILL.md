---
name: feishu-docs
description: Read, create, and update Feishu/Lark docx documents and wiki-backed pages through the Feishu Open API. Use when Codex needs to authenticate with `FEISHU_APP_ID` and `FEISHU_APP_SECRET`, read document raw content, create new Feishu documents, append text into docx blocks, or create visible wiki pages inside a Feishu wiki space.
---

# Feishu Docs

## Overview

Use the bundled CLI instead of rewriting Feishu API calls ad hoc. Default to environment-based credentials so the skill can be shared safely across users and workspaces.

Read [references/api-workflow.md](references/api-workflow.md) when you need endpoint reminders, request limits, or the difference between plain docs and wiki-backed pages.

## Quick Start

Set credentials before invoking the script:

```powershell
$env:FEISHU_APP_ID="your_app_id"
$env:FEISHU_APP_SECRET="your_app_secret"
```

Use the bundled script at [scripts/feishu_docs.py](scripts/feishu_docs.py).

## Read

Read a Feishu doc's raw content:

```powershell
python scripts/feishu_docs.py read-raw <document_id>
```

Use this when the user asks to inspect or summarize an existing Feishu document.

## Create

Create a standalone Feishu doc:

```powershell
python scripts/feishu_docs.py create-doc --title "My new doc"
```

Append plaintext body content:

```powershell
python scripts/feishu_docs.py append-text <document_id> --content-file notes.md
```

Use this path only when the user wants a regular cloud doc and does not care about wiki navigation.

## Create Wiki Page

Create a visible wiki page and optionally write body text in one step:

```powershell
python scripts/feishu_docs.py create-wiki-page --space-id <space_id> --title "Page title" --content-file notes.md
```

Use this when the user expects to find the result in the wiki tree. Do not create a plain doc first unless there is a reason to keep it detached from wiki.

## Execution Rules

- Prefer `create-wiki-page` over `create-doc` for anything the user calls a wiki page.
- Prefer `--content-file` for multi-paragraph content; use `--content` only for short text.
- Treat each input line as one paragraph block.
- Keep secrets in env vars, not in the skill files.
- If a network call fails in the sandbox, rerun with escalation rather than rewriting the workflow.

## Validation

Representative local checks:

```powershell
python scripts/feishu_docs.py --help
python scripts/feishu_docs.py create-wiki-page --help
```

If credentials and network access are available, also run one real read or create command to verify the current tenant works.

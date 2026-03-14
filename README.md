# feishu-docs

Codex skill for reading, creating, and updating Feishu/Lark docx documents and wiki-backed pages through the Feishu Open API.

## Install

Use Codex skill installer with this repository:

```powershell
python "C:\Users\Jacklee\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo JackLee992/feishu-docs --path . --name feishu-docs
```

## Credentials

Set these before using the skill:

```powershell
$env:FEISHU_APP_ID="your_app_id"
$env:FEISHU_APP_SECRET="your_app_secret"
```

## Common Commands

```powershell
python scripts/feishu_docs.py read-raw <document_id>
python scripts/feishu_docs.py create-doc --title "My new doc"
python scripts/feishu_docs.py append-text <document_id> --content-file notes.md
python scripts/feishu_docs.py create-wiki-page --space-id <space_id> --title "Page title" --content-file notes.md
```

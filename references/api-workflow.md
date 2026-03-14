# Feishu Docs API Workflow

## Credentials

- Use `FEISHU_APP_ID` and `FEISHU_APP_SECRET`.
- Do not hardcode personal secrets into a distributable skill.
- For one-off debugging, the CLI also accepts `--app-id` and `--app-secret`.

## Core Endpoints

- `POST /auth/v3/tenant_access_token/internal`
  - Get a tenant token from `app_id` and `app_secret`.
- `GET /docx/v1/documents/{document_id}/raw_content`
  - Read the document's raw text content.
- `POST /docx/v1/documents`
  - Create a standalone docx document.
- `POST /docx/v1/documents/{document_id}/blocks/{document_id}/children`
  - Append paragraph blocks to a document body.
- `POST /wiki/v2/spaces/{space_id}/nodes`
  - Create a wiki node backed by a docx page.

## Practical Rules

- Use `create-wiki-page` when the user cares about wiki visibility, tree placement, and a titled page.
- Use `create-doc` only for standalone docs or when the user explicitly wants a plain cloud document.
- Append body text after creation. The first block parent is the document id itself.
- Respect the append limit: one request can add at most 50 child blocks.
- Treat one input line as one paragraph unless the task requires richer formatting.

## Common Failure Modes

- Page is not visible in wiki:
  - A doc was created, but no wiki node was created.
- Empty or weird wiki title:
  - A wiki node was created from an existing doc without passing a title.
- `field validation failed` when appending:
  - Too many children in one request or malformed `text_run` object.
- Network/auth errors:
  - Token expired, wrong app credentials, or the command needs network approval.

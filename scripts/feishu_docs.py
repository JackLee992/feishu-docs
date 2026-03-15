#!/usr/bin/env python3
"""
Minimal Feishu Docs CLI for Codex skills.

Auth:
  Uses FEISHU_APP_ID and FEISHU_APP_SECRET by default.
  CLI flags can override env vars for one-off runs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


BASE_URL = "https://open.feishu.cn/open-apis"
MAX_CHILDREN_PER_APPEND = 50
CHILDREN_PAGE_SIZE = 500


class FeishuError(RuntimeError):
    pass


def request_json(
    method: str,
    path: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{BASE_URL}{path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise FeishuError(f"HTTP {exc.code} for {path}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise FeishuError(f"Network error for {path}: {exc}") from exc
    result = json.loads(body)
    if result.get("code") != 0:
        raise FeishuError(json.dumps(result, ensure_ascii=False))
    return result


def get_credentials(args: argparse.Namespace) -> tuple[str, str]:
    app_id = args.app_id or os.environ.get("FEISHU_APP_ID")
    app_secret = args.app_secret or os.environ.get("FEISHU_APP_SECRET")
    if not app_id or not app_secret:
        raise FeishuError(
            "Missing credentials. Set FEISHU_APP_ID and FEISHU_APP_SECRET or pass "
            "--app-id/--app-secret."
        )
    return app_id, app_secret


def get_tenant_access_token(args: argparse.Namespace) -> str:
    app_id, app_secret = get_credentials(args)
    result = request_json(
        "POST",
        "/auth/v3/tenant_access_token/internal",
        payload={"app_id": app_id, "app_secret": app_secret},
    )
    return result["tenant_access_token"]


def split_text_blocks(text: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for line in text.splitlines():
        blocks.append(
            {
                "block_type": 2,
                "text": {
                    "elements": [
                        {
                            "text_run": {
                                "content": line,
                                "text_element_style": {
                                    "bold": False,
                                    "inline_code": False,
                                    "italic": False,
                                    "strikethrough": False,
                                    "underline": False,
                                },
                            }
                        }
                    ]
                },
            }
        )
    if not blocks:
        blocks.append(
            {
                "block_type": 2,
                "text": {"elements": [{"text_run": {"content": ""}}]},
            }
        )
    return blocks


def get_children_count(token: str, document_id: str) -> int:
    total = 0
    page_token: str | None = None
    while True:
        query: dict[str, Any] = {"page_size": CHILDREN_PAGE_SIZE}
        if page_token:
            query["page_token"] = page_token
        result = request_json(
            "GET",
            f"/docx/v1/documents/{document_id}/blocks/{document_id}/children",
            token=token,
            query=query,
        )
        data = result["data"]
        total += len(data.get("items", []))
        if not data.get("has_more"):
            return total
        page_token = data.get("page_token")
        if not page_token:
            raise FeishuError("Missing page_token while paginating children.")


def append_text(token: str, document_id: str, text: str) -> dict[str, Any]:
    blocks = split_text_blocks(text)
    base_index = get_children_count(token, document_id)
    last: dict[str, Any] = {}
    for start in range(0, len(blocks), MAX_CHILDREN_PER_APPEND):
        batch = blocks[start : start + MAX_CHILDREN_PER_APPEND]
        last = request_json(
            "POST",
            f"/docx/v1/documents/{document_id}/blocks/{document_id}/children",
            token=token,
            payload={"index": base_index + start, "children": batch},
        )
    return last


def read_text_input(args: argparse.Namespace) -> str:
    if args.content:
        return args.content
    if args.content_file:
        with open(args.content_file, "r", encoding="utf-8") as fh:
            return fh.read()
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise FeishuError("Provide --content, --content-file, or stdin.")


def cmd_token(args: argparse.Namespace) -> None:
    print(json.dumps({"tenant_access_token": get_tenant_access_token(args)}, ensure_ascii=False, indent=2))


def cmd_read_raw(args: argparse.Namespace) -> None:
    token = get_tenant_access_token(args)
    result = request_json(
        "GET",
        f"/docx/v1/documents/{args.document_id}/raw_content",
        token=token,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_create_doc(args: argparse.Namespace) -> None:
    token = get_tenant_access_token(args)
    payload: dict[str, Any] = {"title": args.title}
    if args.folder_token:
        payload["folder_token"] = args.folder_token
    result = request_json("POST", "/docx/v1/documents", token=token, payload=payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_append_text(args: argparse.Namespace) -> None:
    token = get_tenant_access_token(args)
    text = read_text_input(args)
    result = append_text(token, args.document_id, text)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_create_wiki_page(args: argparse.Namespace) -> None:
    token = get_tenant_access_token(args)
    result = request_json(
        "POST",
        f"/wiki/v2/spaces/{args.space_id}/nodes",
        token=token,
        payload={"node_type": "origin", "obj_type": "docx", "title": args.title},
    )
    node = result["data"]["node"]
    output: dict[str, Any] = {"node": node}
    if args.content or args.content_file or not sys.stdin.isatty():
        text = read_text_input(args)
        append_result = append_text(token, node["obj_token"], text)
        output["append_result"] = append_result
    print(json.dumps(output, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read and create Feishu docs/wiki pages.")
    parser.add_argument("--app-id", help="Override FEISHU_APP_ID for this run.")
    parser.add_argument("--app-secret", help="Override FEISHU_APP_SECRET for this run.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    token_p = subparsers.add_parser("token", help="Get a tenant access token.")
    token_p.set_defaults(func=cmd_token)

    read_p = subparsers.add_parser("read-raw", help="Read doc raw content.")
    read_p.add_argument("document_id", help="Feishu document id.")
    read_p.set_defaults(func=cmd_read_raw)

    create_p = subparsers.add_parser("create-doc", help="Create a new docx document.")
    create_p.add_argument("--title", required=True, help="Document title.")
    create_p.add_argument("--folder-token", help="Optional drive/wiki folder token.")
    create_p.set_defaults(func=cmd_create_doc)

    append_p = subparsers.add_parser("append-text", help="Append plaintext paragraphs to a document.")
    append_p.add_argument("document_id", help="Target document id.")
    append_p.add_argument("--content", help="Inline text content.")
    append_p.add_argument("--content-file", help="Path to a UTF-8 text/markdown file.")
    append_p.set_defaults(func=cmd_append_text)

    wiki_p = subparsers.add_parser("create-wiki-page", help="Create a titled wiki page and optionally write body text.")
    wiki_p.add_argument("--space-id", required=True, help="Wiki space id.")
    wiki_p.add_argument("--title", required=True, help="Wiki page title.")
    wiki_p.add_argument("--content", help="Inline text content.")
    wiki_p.add_argument("--content-file", help="Path to a UTF-8 text/markdown file.")
    wiki_p.set_defaults(func=cmd_create_wiki_page)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
        return 0
    except FeishuError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

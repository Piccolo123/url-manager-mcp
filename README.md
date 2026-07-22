# URL Manager MCP Server

[![url-manager-mcp MCP server](https://glama.ai/mcp/servers/Piccolo123/url-manager-mcp/badges/score.svg)](https://glama.ai/mcp/servers/Piccolo123/url-manager-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/Piccolo123/url-manager-mcp/blob/main/LICENSE)

[English](./README.md) | [简体中文](./README.zh-CN.md)

A Model Context Protocol server for managing web bookmarks — cross-device sync, categories, tags, full-text search, batch operations, and team sharing. 20 tools with auto-registration so no manual setup is required.

> 📖 **Usage patterns and best practices → [URL Manager Skill](https://github.com/Piccolo123/url-manager/blob/main/SKILL.md)**

## Tools

### Registration & Identity

- **`agent_register()`**
  Create a new account. No parameters. Token is auto-applied for all subsequent calls.
  ⚠️ Call once only — each invocation creates a fresh account.

- **`my_info()`**
  Verify connection and token validity. Returns username and membership status.

### Bookmarks

- **`search_footprints(query, limit, offset)`**
  Full-text search across titles, descriptions, and URLs.
  - `query` _(required)_ — Search keywords
  - `limit` — Results per page (default 10, max 100)
  - `offset` — Pagination offset (default 0)

- **`list_footprints(category_id, limit, offset)`**
  List bookmarks by category. `category_id=0` returns all.
  - `limit` — Results per page (default 20, max 100)
  - `offset` — Pagination offset (default 0)

- **`get_footprint(footprint_id)`**
  Get full details of a single bookmark.
  - `footprint_id` _(required)_ — From `list_footprints` or `search_footprints` results (field `id`)

- **`add_footprint(url, title, description, category_ids, tag_names)`**
  Add a new bookmark. Call `list_categories()` and `list_tags()` first to discover existing structure.
  - `url` _(required)_ — Web page URL
  - `title` — Leave empty to auto-extract from the page
  - `description` — Summary or notes
  - `category_ids` — Comma-separated IDs, e.g. `"1,3"`
  - `tag_names` — Comma-separated names, e.g. `"AI,tutorial"`

- **`update_footprint(footprint_id, title, description, category_ids, tag_names)`**
  Update a bookmark. Omitted fields stay unchanged.
  ⚠️ `category_ids` **replaces** the entire list — not append. Call `get_footprint()` first, then merge IDs.
  - `footprint_id` _(required)_ — From search or list results

### Categories & Tags

- **`list_categories()`**
  List all categories (personal + shared). Returns `id`, `name`, and `mode` fields.
  `mode=null` → personal; `mode="cocreate"/"subscribe"` → shared.

- **`create_category(name, category_set_id)`**
  Create a new category. Check `list_categories()` first to avoid duplicates.
  - `name` _(required)_ — Category name
  - `category_set_id` — Parent category set (0 = default)

- **`list_tags()`**
  List all tags used by this account.

### Category Sets

- **`list_category_sets()`**
  List all category sets.

- **`create_category_set(name)`**
  Create a new category set (a container of categories).
  - `name` _(required)_ — Category set name

### Shared Categories

- **`create_shared_category(name, mode, description)`**
  Create a shared category for team collaboration.
  - `name` _(required)_
  - `mode` _(required)_ — `"cocreate"` (multiple editors) or `"subscribe"` (read-only)
  - `description` — Optional description
  ⚠️ In `subscribe` mode, adding bookmarks returns **403**. Use `"cocreate"` for editable collaboration.

- **`create_invite_link(shared_category_id, duration_hours)`**
  Generate an invite link for others to join.
  - `shared_category_id` _(required)_ — From `list_categories()` (shared entries)
  - `duration_hours` — Default 24

- **`join_shared_category(invite_code)`**
  Join a shared category by invite code.
  - `invite_code` _(required)_ — 8-character code from the invite link

- **`add_to_shared_category(shared_category_id, footprint_id)`**
  Add one of your own bookmarks to a shared category.
  - Both parameters required

- **`remove_from_shared_category(shared_category_id, footprint_id)`**
  Remove a bookmark from a shared category. Does not delete the bookmark itself.
  - Both parameters required

- **`copy_footprint(footprint_id, category_ids)`**
  Copy a bookmark from a shared category into your personal collection.
  - Both parameters required

### Batch & Delivery

- **`batch_update_footprints(updates)`**
  Bulk edit up to 50 bookmarks at once.
  - `updates` _(required)_ — JSON string: `[{"id":"...", "title":"New Title", "category_ids":"1,3"}, ...]`
  Each object may contain `title`, `description`, `category_ids`, `tag_names`; `id` is required.

- **`agent_magic_link()`**
  Generate a delivery link. Send to the user — they open it to see a card-based interface with all their organized bookmarks. **Valid for 30 days, reusable.**

## Installation

```bash
git clone https://github.com/Piccolo123/url-manager-mcp.git
cd url-manager-mcp
pip install -r requirements.txt
```

### Prerequisites

- Python 3.10+
- Network access to `https://ai.ocean94.com`

## Configuration

### Claude Desktop / Claude Code

```json
{
  "mcpServers": {
    "url-manager": {
      "command": "python",
      "args": ["path/to/url-manager-mcp/server.py"]
    }
  }
}
```

If the user has an existing account:

```json
{
  "mcpServers": {
    "url-manager": {
      "command": "python",
      "args": ["path/to/url-manager-mcp/server.py"],
      "env": {
        "FOOTPRINTS_TOKEN": "FA_xxxxxxxxxxxx"
      }
    }
  }
}
```

### Cursor / Windsurf / Cherry Studio

Same JSON structure as above. Works with any MCP-compatible client supporting STDIO transport.

### Other Clients

This server supports both **STDIO** (default) and **Streamable HTTP** transports:

```bash
# STDIO (default)
python server.py

# Streamable HTTP (for Docker / Glama / hosted environments)
python server.py --http
```

## Deployment

### Docker

```bash
docker build -t url-manager-mcp .
docker run -e FOOTPRINTS_TOKEN="FA_xxx" url-manager-mcp
```

### ModelScope

One-click hosted deployment: [url-manager-mcp](https://modelscope.cn/mcp/servers/Piccoloxl/url-manager)

## Why URL Manager

Browser bookmarks are flat lists with no organization, no search, and no sharing. URL Manager adds:

- **Categories, category sets, and tags** — Hierarchical organization
- **Full-text search** — Find anything across all titles, descriptions, and URLs
- **Cross-device sync** — Save on one device, access on all
- **Batch management** — Sort and organize hundreds of links at once
- **Team sharing** — Co-editing and read-only shared collections with invite links
- **Card-based delivery** — Send organized collections as a polished interface, not raw URLs

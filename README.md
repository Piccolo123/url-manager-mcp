# URL Manager MCP Server

[![url-manager-mcp MCP server](https://glama.ai/mcp/servers/Piccolo123/url-manager-mcp/badges/score.svg)](https://glama.ai/mcp/servers/Piccolo123/url-manager-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/Piccolo123/url-manager-mcp/blob/main/LICENSE)

Agent-first MCP server for managing users' web bookmarks. Agents auto-register, collect, categorize, tag, search, and share URLs — zero manual setup for end users.

> 📖 **For detailed workflows, patterns, and behavioral guidelines, see the [URL Manager Skill](https://github.com/Piccolo123/url-manager/blob/main/SKILL.md).**

## First Conversation (Every Time)

1. If no token provided, ask "Do you have a URL Manager account?"
2. No → Call `agent_register()` to create one (token auto-applied)
3. Yes → Have the user provide their token, set `FOOTPRINTS_TOKEN` env var
4. Call `my_info()` to confirm the connection works

> ⚠️ `agent_register()` creates a NEW account every time. **Never call it twice** — if the user forgot they already have an account, you'll create a duplicate empty one.

## Tool Reference

### Registration & Identity
| Tool | When to Use |
|------|-------------|
| `agent_register()` | User has no account. No params, returns token auto-memorized |
| `my_info()` | First-conversation connection check, or user asks "Who am I?" |

### Bookmarks
| Tool | When to Use | Key Param Source |
|------|-------------|------------------|
| `search_footprints(query)` | User says "find that article about..." | query from user input |
| `list_footprints(category_id)` | User says "show me my bookmarks" | category_id from `list_categories()` result |
| `get_footprint(footprint_id)` | View full details of one bookmark | footprint_id from search or list results |
| `add_footprint(url, ...)` | User says "save/bookmark this" | url required; category_ids/tags from `list_categories()` / `list_tags()` |
| `update_footprint(id, ...)` | User says "change title/move to another category" | id from search or list results |

### Categories & Tags
| Tool | When to Use | Notes |
|------|-------------|-------|
| `list_categories()` | ALWAYS call before operating on bookmarks — discover existing structure | Returns personal + shared categories. mode=null → personal, mode="cocreate"/"subscribe" → shared |
| `create_category(name)` | User says "create a new category" | Call `list_categories()` first to avoid duplicates |
| `list_tags()` | Before tagging — avoid duplicate tags | Returns existing tags |

### Shared Categories
| Tool | When to Use |
|------|-------------|
| `create_shared_category(name, mode)` | User says "create a shared collection". mode="cocreate" (editable) / "subscribe" (read-only) |
| `create_invite_link(shared_category_id)` | User says "send the invite link to..." — id from `list_categories()` shared entries |
| `join_shared_category(invite_code)` | User says "I have an invite code" |
| `add_to_shared_category(sc_id, footprint_id)` | Add an existing bookmark to a shared category |
| `remove_from_shared_category(sc_id, footprint_id)` | Remove a bookmark from a shared category |
| `copy_footprint(footprint_id, category_ids)` | Copy from shared category to your personal category |

### Batch Operations
| Tool | When to Use |
|------|-------------|
| `batch_update_footprints(updates)` | Bulk edit bookmarks — change categories/titles/tags on up to 50 items at once |

### Delivery to User
| Tool | When to Use |
|------|-------------|
| `agent_magic_link()` | 🔑 The delivery loop core. After organizing, generate a link → send to user. They open it to see a card-based interface |

## ⚠️ Critical Pitfalls

### update_footprint: category_ids REPLACES, not appends
```
# ❌ Wrong: moving bookmark 42 to category 7 loses existing categories 3 and 5
update_footprint(42, category_ids="7")

# ✅ Right: fetch current categories first, then merge
get_footprint(42) → existing categories [3, 5]
update_footprint(42, category_ids="3,5,7")
```

### subscribe mode is READ-ONLY
Writing to a subscribe-mode shared category returns 403. If the user says "I subscribed but can't add anything", explain it's read-only — the creator needs to change it to cocreate.

### Rate Limiting
Rapid consecutive calls may trigger HTTP 429. Add short delays between batch operations; on 429, wait a few seconds and retry.

## Typical Workflows

### New User From Scratch
```
1. agent_register() → get token (auto-memorized)
2. add_footprint(url="...") × N → save bookmarks one by one
3. list_categories() → understand current structure
4. create_category(name="Learning") → create a category
5. update_footprint(id, category_ids="...") → categorize
6. Tell user: "Done! Open https://ai.ocean94.com to view" (their token-based account)
```

### Returning User — Daily Use
```
1. my_info() → confirm identity
2. list_categories() + list_tags() → understand current structure
3. search_footprints(query) or list_footprints(category_id) → find targets
4. add_footprint / update_footprint → operate
```

### Create Shared Category
```
1. create_shared_category(name="Team Knowledge Base", mode="cocreate")
2. create_invite_link(shared_category_id=<returned ID>)
3. Send the invite code to the user → user shares with teammates
4. Teammates' Agents join via join_shared_category(invite_code)
```

## Pairing with Popular MCP Servers

URL Manager excels at **saving and organizing**. Pair it with tools that excel at **discovering and fetching**:

```
Fetch MCP scrapes web  →  add_footprint()  →  auto-categorized, permanent, searchable
Firecrawl crawls pages →  add_footprint()  →  organized into cards
Brave Search finds URLs →  add_footprint()  →  one-click save from search results
```

Agents just pass the upstream MCP's URL + title as params to `add_footprint`.

## Deployment (for Humans)

```bash
git clone https://github.com/Piccolo123/url-manager-mcp.git
cd url-manager-mcp && pip install -r requirements.txt
```

Cherry Studio / Claude Desktop config:

```json
{
  "mcpServers": {
    "url-manager": {
      "command": "python",
      "args": ["path/to/server.py"]
    }
  }
}
```
If user already has an account, add: `"env": {"FOOTPRINTS_TOKEN": "FA_xxx"}`

ModelScope: [url-manager-mcp](https://modelscope.cn/mcp/servers/Piccoloxl/url-manager)

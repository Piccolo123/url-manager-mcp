"""
URL Manager MCP Server — Agent-first design

AI agents manage users' web bookmarks (collections) through MCP protocol.
Full agent-proxy lifecycle from zero to fully managed: register → operate → deliver.

Core Agent Workflow:
  No account → agent_register() creates one → token auto-applied → full access
  Has account → set FOOTPRINTS_TOKEN env var → full access
"""

import json
import os
import sys

import httpx
from mcp.server.fastmcp import FastMCP

# ── Global State ──────────────────────────────────────
ENDPOINT = os.getenv("FOOTPRINTS_ENDPOINT", "https://ai.ocean94.com")
TOKEN = os.getenv("FOOTPRINTS_TOKEN", "")


def _auth_headers() -> dict:
    """Dynamic auth — agent_register() updates TOKEN globally and it takes effect immediately."""
    return {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}


mcp = FastMCP(
    "url-manager",
    instructions="""
You are a URL Manager assistant, helping users manage their saved web pages, articles, and videos.

Token flow (every session):
1. If FOOTPRINTS_TOKEN is set → call my_info() to verify. Done.
2. If not → ask: "Do you have a URL Manager account?"
   - No → call agent_register() ONCE (⚠️ creates a new account each call). Token auto-applied.
   - Yes → ask user to provide their token, set FOOTPRINTS_TOKEN, then my_info() to verify.

Daily operations:
- Before adding or updating, call list_categories() + list_tags() to understand the current structure
- update_footprint's category_ids REPLACES the entire list — not append. Always get_footprint() first, then merge IDs
- subscribe-mode shared categories are READ-ONLY; writing returns 403
- Frequent calls may hit rate limits (429); wait a few seconds and retry
- For batch reorganization, use batch_update_footprints (max 50 at a time)

Delivery loop (Agent-first core):
- After organizing, call agent_magic_link() to generate a link
- Send the link to the user: "Done organizing — view here → [link]"
- User opens it to see a card-based interface; link valid for 30 days, reusable

For detailed workflows, patterns, and behavioral guidelines, see the skill:
https://github.com/Piccolo123/url-manager/blob/main/SKILL.md
""",
)


# ── Helpers ───────────────────────────────────────────

async def _api(method: str, path: str, **kwargs) -> dict:
    url = f"{ENDPOINT}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(method, url, headers=_auth_headers(), **kwargs)
        resp.raise_for_status()
        return resp.json()


# ── Agent Registration (no token needed) ──────────────

@mcp.tool()
async def agent_register() -> dict:
    """Create a new URL Manager account. Use when the user has no existing account
    and no token is configured — the default path for first-time users.

    No parameters. Token is auto-memorized for all subsequent calls.
    ⚠️ NEVER call this more than once! Each call creates a fresh empty account.
    When in doubt, call my_info() first to check if a token is already active.
    """
    global TOKEN
    result = await _api("POST", "/api/v1/agent/register")
    if "token" in result:
        TOKEN = result["token"]
    return result


# ── User Info ─────────────────────────────────────────

@mcp.tool()
async def my_info() -> dict:
    """Verify token validity and confirm connection. Use at the start of every
    conversation, or when the user asks "Who am I?" / "What account is this?"

    Returns username and membership status.
    """
    return await _api("GET", "/api/v1/agent/me")


# ── Search & List ─────────────────────────────────────

@mcp.tool()
async def search_footprints(query: str, limit: int = 10, offset: int = 0) -> dict:
    """Full-text search across titles, descriptions, and URLs.
    Use when the user says "find that article about Docker" or "search for...".

    Args:
        query: Search keywords
        limit: Results per page (max 100)
        offset: Pagination offset
    """
    return await _api("GET", "/api/v1/agent/collections", params={
        "q": query, "limit": min(limit, 100), "offset": offset
    })


@mcp.tool()
async def list_footprints(category_id: int = 0, limit: int = 20, offset: int = 0) -> dict:
    """List bookmarks by category. Use when the user says "show me my bookmarks",
    "what have I saved?", or "list everything in this category".

    Args:
        category_id: Category ID (0=all, get IDs from list_categories)
        limit: Results per page (max 100)
        offset: Pagination offset
    """
    params = {"limit": min(limit, 100), "offset": offset}
    if category_id > 0:
        params["category_id"] = category_id
    return await _api("GET", "/api/v1/agent/collections", params=params)


@mcp.tool()
async def get_footprint(footprint_id: int) -> dict:
    """Get full details of a single bookmark. Use when the user says
    "show me the details of that bookmark" or before updating to see
    existing categories.

    Args:
        footprint_id: Bookmark ID (from list_footprints or search results, field "id")
    """
    return await _api("GET", f"/api/v1/agent/collections/{footprint_id}")


# ── Create ────────────────────────────────────────────

@mcp.tool()
async def add_footprint(
    url: str, title: str = "", description: str = "",
    category_ids: str = "", tag_names: str = "",
) -> dict:
    """Add a new bookmark. Use when the user says "save/bookmark/collect this link".

    Call list_categories() and list_tags() FIRST to discover existing categories
    and tags — avoid creating duplicates. If title is empty, it will be auto-extracted.

    Args:
        url: Web page URL (required)
        title: Custom title (leave empty for auto-extraction)
        description: Summary/notes
        category_ids: Comma-separated category IDs, e.g. "1,3"
        tag_names: Comma-separated tag names, e.g. "AI,tutorial"
    """
    body = {"url": url}
    if title:
        body["title"] = title
    if description:
        body["description"] = description
    if category_ids:
        body["category_ids"] = [int(x.strip()) for x in category_ids.split(",") if x.strip()]
    if tag_names:
        body["tag_names"] = [x.strip() for x in tag_names.split(",") if x.strip()]
    return await _api("POST", "/api/v1/agent/collections", json=body)


# ── Update ────────────────────────────────────────────

@mcp.tool()
async def update_footprint(
    footprint_id: int, title: str = "", description: str = "",
    category_ids: str = "", tag_names: str = "",
) -> dict:
    """Update a bookmark. Use when the user says "change the title",
    "move to another category", or "add a description".

    ⚠️ category_ids REPLACES the entire category list — NOT append!
    Correct approach: get_footprint(id) → see current categories → merge in new IDs.
    Example: existing [3,5], want to add 7 → category_ids="3,5,7" (NOT just "7")

    Args:
        footprint_id: Bookmark ID (from search or list results)
        title/description/category_ids/tag_names: Leave empty to keep unchanged
    """
    body = {}
    if title:
        body["title"] = title
    if description:
        body["description"] = description
    if category_ids:
        body["category_ids"] = [int(x.strip()) for x in category_ids.split(",") if x.strip()]
    if tag_names:
        body["tag_names"] = [x.strip() for x in tag_names.split(",") if x.strip()]
    if not body:
        return {"error": "At least one field to update is required"}
    return await _api("PUT", f"/api/v1/agent/collections/{footprint_id}", json=body)


# ── Categories & Tags ─────────────────────────────────
# list_categories returns all categories — personal AND shared.
# Shared categories have mode="cocreate" or "subscribe"; personal have mode=null.

@mcp.tool()
async def list_categories() -> dict:
    """List all categories (personal + shared). Use at the start of any bookmark
    operation to discover available categories and their IDs.

    Returns each category with id, name, and mode fields.
    mode=null → personal category. mode="cocreate"/"subscribe" → shared category.
    Use the 'id' field in add_footprint / update_footprint category_ids parameter.
    """
    return await _api("GET", "/api/v1/agent/categories")


@mcp.tool()
async def create_category(name: str, category_set_id: int = 0) -> dict:
    """Create a new category. Use when the user says "create a new category called..."
    or when organizing bookmarks into a new group.

    Call list_categories() first to avoid duplicates.

    Args:
        name: Category name
        category_set_id: Parent category set (0=default)
    """
    body = {"name": name}
    if category_set_id > 0:
        body["category_set_id"] = category_set_id
    return await _api("POST", "/api/v1/agent/categories", json=body)


@mcp.tool()
async def list_tags() -> dict:
    """List all tags. Use before tagging bookmarks to see existing tags and avoid duplicates."""
    return await _api("GET", "/api/v1/agent/tags")


# ── Category Sets ─────────────────────────────────────

@mcp.tool()
async def list_category_sets() -> dict:
    """List all category sets. Use when the user asks about their organizational
    structure or needs to create a category in a specific set."""
    return await _api("GET", "/api/v1/agent/category-sets")


@mcp.tool()
async def create_category_set(name: str) -> dict:
    """Create a new category set (a container of categories). Use when the user
    says "create a new workspace/set for...".

    Args:
        name: Category set name
    """
    return await _api("POST", "/api/v1/agent/category-sets", json={"name": name})


# ── Shared Categories ─────────────────────────────────

@mcp.tool()
async def create_shared_category(
    name: str, mode: str = "cocreate", description: str = "",
) -> dict:
    """Create a shared category for team collaboration. Use when the user says
    "create a shared collection" or "let's share a folder with my team".

    ⚠️ In subscribe mode, NO ONE (including the creator) can add bookmarks —
    add_to_shared_category returns 403. Use mode="cocreate" for editable collaboration.

    Args:
        name: Category name (required)
        mode: "cocreate" (multiple editors) or "subscribe" (read-only). Default: "cocreate"
        description: Optional description for the shared category
    """
    body = {"name": name, "mode": mode}
    if description:
        body["description"] = description
    return await _api("POST", "/api/v1/agent/shared-categories", json=body)


@mcp.tool()
async def join_shared_category(invite_code: str) -> dict:
    """Join a shared category by invite code. Use when the user says
    "I have an invite code" or "join this shared collection".

    Args:
        invite_code: 8-character invite code
    """
    return await _api("POST", "/api/v1/agent/shared-categories/join", json={"code": invite_code})


@mcp.tool()
async def create_invite_link(shared_category_id: int, duration_hours: int = 24) -> dict:
    """Generate an invite link for others to join. Use when the user says
    "send the invite link to my team" or "invite someone to this shared category".

    Args:
        shared_category_id: Shared category ID (from list_categories — pick ones where mode is not null)
        duration_hours: Link validity in hours (default: 24)
    """
    return await _api("POST", f"/api/v1/agent/shared-categories/{shared_category_id}/invite-link",
                      json={"duration_hours": duration_hours})


@mcp.tool()
async def add_to_shared_category(shared_category_id: int, footprint_id: int) -> dict:
    """Add one of your existing bookmarks to a shared category. Use when the user
    says "add this to the team collection" or wants to contribute to a shared folder.

    The bookmark must belong to you. Does NOT work with subscribe-mode categories (returns 403).

    Args:
        shared_category_id: Shared category ID
        footprint_id: Bookmark ID to add
    """
    return await _api("POST", f"/api/v1/agent/shared-categories/{shared_category_id}/collections",
                      json={"collection_id": footprint_id})


@mcp.tool()
async def remove_from_shared_category(shared_category_id: int, footprint_id: int) -> dict:
    """Remove a bookmark from a shared category. Use when the user says
    "take this out of the shared collection". Does not delete the bookmark itself.

    Args:
        shared_category_id: Shared category ID
        footprint_id: Bookmark ID to remove
    """
    return await _api("DELETE",
                      f"/api/v1/agent/shared-categories/{shared_category_id}/collections/{footprint_id}")


@mcp.tool()
async def copy_footprint(footprint_id: int, category_ids: str) -> dict:
    """Copy a bookmark from a shared category into your personal collection.
    Use when the user says "save this shared bookmark to my own collection"
    or "add that to my personal list".

    Args:
        footprint_id: Bookmark ID to copy
        category_ids: Target personal category IDs, comma-separated, e.g. "1,3"
    """
    cids = [int(x.strip()) for x in category_ids.split(",") if x.strip()]
    return await _api("POST", f"/api/v1/agent/collections/{footprint_id}/copy",
                      json={"category_ids": cids})


# ── Batch ─────────────────────────────────────────────

@mcp.tool()
async def batch_update_footprints(updates: str) -> dict:
    """Batch update up to 50 bookmarks at once. Use when the user says
    "reorganize all my bookmarks" or for bulk categorization / renaming.

    ⚠️ updates must be a valid JSON array. Malformed JSON or > 50 items returns an error.
    category_ids still REPLACES (not appends) — verify existing categories with get_footprint() first.

    Args:
        updates: JSON string, format '[{"id":"uuid","title":"New Title","category_ids":"1,3"}, ...]'
                 Each object requires "id". Optional: title, description, category_ids, tag_names
    """
    try:
        items = json.loads(updates)
    except json.JSONDecodeError:
        return {"error": "updates must be a valid JSON array"}
    if len(items) > 50:
        return {"error": "Maximum 50 items per batch"}
    for item in items:
        if "category_ids" in item and isinstance(item["category_ids"], str):
            item["category_ids"] = [int(x.strip()) for x in item["category_ids"].split(",") if x.strip()]
        if "tag_names" in item and isinstance(item["tag_names"], str):
            item["tag_names"] = [x.strip() for x in item["tag_names"].split(",") if x.strip()]
    return await _api("PUT", "/api/v1/agent/collections/batch", json={"updates": items})


# ── Delivery ──────────────────────────────────────────

@mcp.tool()
async def agent_magic_link() -> dict:
    """Generate a delivery link to the user. Use after organizing bookmarks —
    this is the Agent-first delivery loop core.

    Call this as the final step, then send the link to the user:
    "Done organizing — view here → [link]"
    User opens it to see a card-based interface with all organized bookmarks.
    Link valid for 30 days, reusable.
    """
    return await _api("POST", "/api/v1/agent/magic-link")


# ── Startup ───────────────────────────────────────────

def main():
    """Start the MCP Server. STDIO for local Agents, --http for Docker/Glama testing."""
    transport = "stdio"
    if "--http" in sys.argv:
        transport = "streamable-http"
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()

"""
AI 足迹 MCP Server — 让 AI Agent 管理用户的数字足迹

本 Server 将 AI 足迹应用的核心能力暴露为 MCP 工具，
使任意支持 MCP 协议的 AI Agent（Claude、Cursor、Cherry Studio 等）
可以直接操作用户的足迹库。

核心场景：
1. 用户说"帮我收藏这个网页" → Agent 调用 add_footprint
2. 用户说"我收藏了哪些关于 AI 的文章" → Agent 调用 search_footprints
3. 用户说"整理一下我的足迹" → Agent 调用 list_footprints + update_footprint
4. 用户说"和周报相关的都放一个分类" → Agent 调用 create_category + update_footprint

认证：环境变量 FOOTPRINTS_TOKEN（在 https://ai.ocean94.com 个人中心 → 接入Agent 获取）
"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

# ── 配置 ──────────────────────────────────────────────
ENDPOINT = os.getenv("FOOTPRINTS_ENDPOINT", "https://ai.ocean94.com")
TOKEN = os.getenv("FOOTPRINTS_TOKEN", "")
AUTH_HEADERS = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

mcp = FastMCP(
    "ai-footprints",
    instructions="""
你是 AI 足迹的助手，通过 MCP 工具帮用户管理他们收藏的网页、文章、视频等数字内容。

用户通常会用自然语言表达意图，你需要：
1. 理解用户想做什么（搜索？添加？整理？分享？）
2. 选择合适的工具
3. 如果缺少必要参数（如 FOOTPRINTS_TOKEN 未配置），先引导用户完成配置

Token 获取方式：https://ai.ocean94.com → 个人中心 → 接入Agent → 访问令牌
    """,
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8000")),
)


# ── 辅助函数 ──────────────────────────────────────────

async def _api(method: str, path: str, **kwargs) -> dict:
    """调用 AI 足迹 API，统一处理错误"""
    url = f"{ENDPOINT}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(method, url, headers=AUTH_HEADERS, **kwargs)
        resp.raise_for_status()
        return resp.json()


def _require_token() -> str | None:
    """检查 Token 是否已配置"""
    if not TOKEN:
        return (
            "未配置 FOOTPRINTS_TOKEN。请在环境变量中设置 Token。"
            "Token 获取：https://ai.ocean94.com → 个人中心 → 接入Agent → 访问令牌"
        )
    return None


# ── 足迹工具 ──────────────────────────────────────────
# Agent 使用指南：
#   当用户想"找"某条收藏 → search_footprints
#   当用户想"加"一条收藏 → add_footprint
#   当用户想"看"收藏列表 → list_footprints
#   当用户想"看"某条详情 → get_footprint
#   当用户想"改"某条内容 → update_footprint

@mcp.tool()
async def search_footprints(query: str, page: int = 1, page_size: int = 10) -> dict:
    """当用户说"找我收藏的XX"或"有没有关于XX的足迹"时使用此工具。
    在标题、描述、URL 中全文搜索。

    Args:
        query: 搜索关键词，支持多个词（空格分隔）
        page: 页码，从 1 开始
        page_size: 每页条数（默认 10，最大 50）
    """
    if err := _require_token():
        return {"error": err}
    return await _api("GET", "/api/search", params={
        "q": query, "page": page, "page_size": min(page_size, 50)
    })


@mcp.tool()
async def add_footprint(
    url: str,
    title: str = "",
    description: str = "",
    category_ids: str = "",
    tags: str = "",
) -> dict:
    """当用户说"帮我收藏这个链接"或"把这个加到我的足迹"时使用此工具。
    添加一条新的网页/文章/视频足迹。标题留空会自动提取。

    Args:
        url: 要收藏的网页链接（必填）
        title: 自定义标题，留空则自动从网页提取
        description: 描述或摘要
        category_ids: 放入哪些分类，多个 ID 逗号分隔，如 "1,3"
        tags: 标签，多个逗号分隔，如 "AI,教程,收藏"
    """
    if err := _require_token():
        return {"error": err}
    body = {"url": url}
    if title:
        body["title"] = title
    if description:
        body["description"] = description
    if category_ids:
        body["category_ids"] = [int(x.strip()) for x in category_ids.split(",") if x.strip()]
    if tags:
        body["tags"] = [x.strip() for x in tags.split(",") if x.strip()]
    return await _api("POST", "/api/ai/collections", json=body)


@mcp.tool()
async def list_footprints(category_id: int = 0, page: int = 1, page_size: int = 20) -> dict:
    """当用户说"看看我的收藏"或"列出我的足迹"时使用此工具。
    按分类列出足迹。category_id=0 表示全部。

    Args:
        category_id: 分类 ID，0 代表查看全部（默认）
        page: 页码
        page_size: 每页条数（默认 20，最大 50）
    """
    if err := _require_token():
        return {"error": err}
    params = {"page": page, "page_size": min(page_size, 50)}
    if category_id > 0:
        params["category_id"] = category_id
    return await _api("GET", "/api/collections", params=params)


@mcp.tool()
async def get_footprint(footprint_id: int) -> dict:
    """当用户想看某条收藏的完整详情时使用。
    返回足迹的标题、描述、URL、分类、标签、创建时间等。

    Args:
        footprint_id: 足迹的数字 ID（从 search_footprints 或 list_footprints 的结果中获取）
    """
    if err := _require_token():
        return {"error": err}
    return await _api("GET", f"/api/collections/{footprint_id}")


@mcp.tool()
async def update_footprint(
    footprint_id: int,
    title: str = "",
    description: str = "",
    category_ids: str = "",
    tags: str = "",
) -> dict:
    """当用户说"把这条足迹改个标题"或"把这篇移到XX分类"时使用此工具。
    更新已有足迹的标题、描述、分类或标签。
    注意：category_ids 会替换整个分类列表而非追加。

    Args:
        footprint_id: 要修改的足迹 ID
        title: 新标题（不填则不改）
        description: 新描述（不填则不改）
        category_ids: 新分类列表，逗号分隔（不填则不改）
        tags: 新标签列表，逗号分隔（不填则不改）
    """
    if err := _require_token():
        return {"error": err}
    body = {}
    if title:
        body["title"] = title
    if description:
        body["description"] = description
    if category_ids:
        body["category_ids"] = [int(x.strip()) for x in category_ids.split(",") if x.strip()]
    if tags:
        body["tags"] = [x.strip() for x in tags.split(",") if x.strip()]
    if not body:
        return {"error": "至少需要提供一个要修改的字段（title/description/category_ids/tags）"}
    return await _api("PUT", f"/api/collections/{footprint_id}", json=body)


# ── 分类与标签 ────────────────────────────────────────
# Agent 使用指南：
#   先 list_categories 了解已有分类，再决定 create_category 还是直接用已有分类
#   标签同理：先 list_tags 了解已有标签

@mcp.tool()
async def list_categories() -> dict:
    """列出用户的所有分类。在操作足迹前先调用此工具了解可选分类。"""
    if err := _require_token():
        return {"error": err}
    return await _api("GET", "/api/categories")


@mcp.tool()
async def create_category(name: str, category_set_id: int = 0) -> dict:
    """当用户说"建一个XX分类"时使用。先调用 list_categories 确认是否已存在同名分类。

    Args:
        name: 分类名称
        category_set_id: 所属分类集 ID（0=默认分类集）
    """
    if err := _require_token():
        return {"error": err}
    body = {"name": name}
    if category_set_id > 0:
        body["category_set_id"] = category_set_id
    return await _api("POST", "/api/categories", json=body)


@mcp.tool()
async def list_tags() -> dict:
    """列出用户所有的已有标签。给足迹打标签前先看一眼避免重复。"""
    if err := _require_token():
        return {"error": err}
    return await _api("GET", "/api/search/tags")


# ── 分类集 ────────────────────────────────────────────
# Agent 使用指南：
#   分类集是大容器，每个分类集下可以有多个分类。
#   普通用户一般只用默认分类集，不需要关心这个。

@mcp.tool()
async def list_category_sets() -> dict:
    """列出所有分类集。一般不需要调用，除非用户明确有多个分类集。"""
    if err := _require_token():
        return {"error": err}
    return await _api("GET", "/api/category-sets")


@mcp.tool()
async def create_category_set(name: str) -> dict:
    """创建新分类集。仅当用户明确需要独立的分类体系时使用。

    Args:
        name: 分类集名称
    """
    if err := _require_token():
        return {"error": err}
    return await _api("POST", "/api/category-sets", json={"name": name})


# ── 共享分类（协作） ────────────────────────────────
# Agent 使用指南：
#   当用户说"我们来一起建一个收藏夹"或"分享我的收藏给别人"
#   → 用 create_shared_category(name="...", mode="cocreate")
#   当用户说"把邀请链接发给XX" → create_invite_link
#   当用户说"我收到一个邀请码" → join_shared_category(invite_code="...")

@mcp.tool()
async def list_shared_categories() -> dict:
    """列出用户参与的所有共享分类（共创和订阅）。"""
    if err := _require_token():
        return {"error": err}
    return await _api("GET", "/api/shared-categories")


@mcp.tool()
async def create_shared_category(
    name: str,
    mode: str = "cocreate",
    description: str = "",
) -> dict:
    """创建共享分类，用于多人协作收藏。

    Args:
        name: 分类名称
        mode: "cocreate"（共创，多人可编辑）或 "subscribe"（订阅，只读分享）
        description: 分类描述，让协作者了解这个分类的用途
    """
    if err := _require_token():
        return {"error": err}
    body = {"name": name, "mode": mode}
    if description:
        body["description"] = description
    return await _api("POST", "/api/shared-categories", json=body)


@mcp.tool()
async def join_shared_category(invite_code: str) -> dict:
    """通过邀请码加入别人创建的共享分类。

    Args:
        invite_code: 8 位邀请码（从邀请链接中获取）
    """
    if err := _require_token():
        return {"error": err}
    return await _api("POST", "/api/shared-categories/join", json={"code": invite_code})


@mcp.tool()
async def create_invite_link(shared_category_id: int, duration_hours: int = 24) -> dict:
    """生成共享分类的邀请链接，发给其他人即可让他们加入。

    Args:
        shared_category_id: 共享分类的 ID
        duration_hours: 链接有效期（小时），默认 24
    """
    if err := _require_token():
        return {"error": err}
    return await _api("POST", f"/api/shared-categories/{shared_category_id}/invite",
                      json={"duration_hours": duration_hours})


# ── 用户信息 ──────────────────────────────────────────

@mcp.tool()
async def my_info() -> dict:
    """查看当前 Agent Token 对应的用户信息（用户名、会员状态等）。
    适合在首次对话时调用，确认身份。"""
    if err := _require_token():
        return {"error": err}
    return await _api("GET", "/api/auth/me")


# ── 启动入口 ──────────────────────────────────────────

def main():
    """Streamable HTTP 模式启动（供 ModelScope 托管部署）"""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()

"""
AI 足迹 MCP Server — Agent 先行设计

让 AI Agent 通过 MCP 协议操作用户的 AI 足迹数据。
支持从零注册到全流程管理的完整 Agent 代理体验。

核心 Agent 工作流：
  用户没有账号 → agent_register() 创建 → Token 自动生效 → 全流程操作
  用户已有账号 → 配 FOOTPRINTS_TOKEN 环境变量 → 全流程操作
"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

# ── 全局状态 ──────────────────────────────────────────
ENDPOINT = os.getenv("FOOTPRINTS_ENDPOINT", "https://ai.ocean94.com")
TOKEN = os.getenv("FOOTPRINTS_TOKEN", "")


def _auth_headers() -> dict:
    """动态获取鉴权头——agent_register() 更新 TOKEN 后即时生效"""
    return {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}


mcp = FastMCP(
    "ai-footprints",
    instructions="""
你是 AI 足迹的助手，帮用户管理收藏的网页、文章、视频。

首次对话流程：
1. 问用户有没有账号
2. 没有 → agent_register() 创建（⚠️ 只调一次！会创建新账号）
3. 有 → 确认 FOOTPRINTS_TOKEN 已配置
4. my_info() 验证连接

日常操作：
- 操作足迹前先 list_categories() + list_tags() 了解结构
- update_footprint 的 category_ids 是替换不是追加，先 get_footprint 再拼 ID
- subscribe 模式共享分类只读，写入会 403
- 频繁调用可能被限流（429），等几秒重试
""",
)


# ── 辅助 ──────────────────────────────────────────────

async def _api(method: str, path: str, **kwargs) -> dict:
    url = f"{ENDPOINT}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(method, url, headers=_auth_headers(), **kwargs)
        resp.raise_for_status()
        return resp.json()


# ── Agent 注册（无需 Token）────────────────────────────

@mcp.tool()
async def agent_register() -> dict:
    """帮用户创建 AI 足迹账号。无参数，无需 Token。

    每次调用创建全新账号，返回 token 自动记忆。
    ⚠️ 不要重复调用！如果用户已有账号但忘了给 Token，调此工具会创建空白新账号。
    使用前先问用户"有 AI 足迹账号吗？"
    """
    global TOKEN
    result = await _api("POST", "/api/agent/register")
    if "token" in result:
        TOKEN = result["token"]
    return result


# ── 用户信息 ──────────────────────────────────────────

@mcp.tool()
async def my_info() -> dict:
    """首次对话先调此工具，确认 Token 有效且连接正常。
    返回用户名、会员状态。也可用于用户问"我是谁"时。
    """
    return await _api("GET", "/api/auth/me")


# ── 足迹搜索 ──────────────────────────────────────────

@mcp.tool()
async def search_footprints(query: str, page: int = 1, page_size: int = 10) -> dict:
    """用户说"找 XX 的收藏"时用。在标题/描述/URL 中全文搜索。

    Args:
        query: 搜索关键词（空格分隔）
        page: 页码
        page_size: 每页条数（最大 50）
    """
    return await _api("GET", "/api/search", params={
        "q": query, "page": page, "page_size": min(page_size, 50)
    })


@mcp.tool()
async def list_footprints(category_id: int = 0, page: int = 1, page_size: int = 20) -> dict:
    """用户说"看看收藏"时用。按分类列出，0=全部。

    Args:
        category_id: 分类 ID（0=全部）
        page: 页码
        page_size: 每页条数（最大 50）
    """
    params = {"page": page, "page_size": min(page_size, 50)}
    if category_id > 0:
        params["category_id"] = category_id
    return await _api("GET", "/api/collections", params=params)


@mcp.tool()
async def get_footprint(footprint_id: int) -> dict:
    """看某条收藏的完整详情。

    Args:
        footprint_id: 足迹 ID（从 list_footprints 结果中取）
    """
    return await _api("GET", f"/api/collections/{footprint_id}")


# ── 足迹添加 ──────────────────────────────────────────

@mcp.tool()
async def add_footprint(
    url: str, title: str = "", description: str = "",
    category_ids: str = "", tags: str = "",
) -> dict:
    """添加一条收藏。用户说"收藏这个链接"时用。

    调用前先 list_categories() 和 list_tags() 了解已有分类/标签，
    避免创建重复分类。标题留空自动从网页提取。

    Args:
        url: 网页链接（必填）
        title: 自定义标题（留空自动提取）
        description: 摘要
        category_ids: 分类 ID，逗号分隔如 "1,3"
        tags: 标签，逗号分隔如 "AI,教程"
    """
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


# ── 足迹更新 ──────────────────────────────────────────

@mcp.tool()
async def update_footprint(
    footprint_id: int, title: str = "", description: str = "",
    category_ids: str = "", tags: str = "",
) -> dict:
    """更新足迹。用户说"改标题/移分类"时用。

    ⚠️ category_ids 是替换整个列表，不是追加！
    正确做法：先 get_footprint(id) 拿现有分类 → 拼上新 ID → 再传 category_ids。
    例：现有 [3,5]，要加 7 → category_ids="3,5,7"（不是 "7"）

    Args:
        footprint_id: 足迹 ID（从搜索结果取）
        title/description/category_ids/tags: 留空不改
    """
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
        return {"error": "至少填一个要改的字段"}
    return await _api("PUT", f"/api/collections/{footprint_id}", json=body)


# ── 分类 ──────────────────────────────────────────────

@mcp.tool()
async def list_categories() -> dict:
    """列出所有分类（id + name）。操作足迹前必须先调此工具，获取可选分类 ID 列表。
    返回结果中 id 字段用于 add_footprint / update_footprint 的 category_ids 参数。
    """
    return await _api("GET", "/api/categories")


@mcp.tool()
async def create_category(name: str, category_set_id: int = 0) -> dict:
    """建新分类。先 list_categories 确认不重名。

    Args:
        name: 分类名称
        category_set_id: 所属分类集（0=默认）
    """
    body = {"name": name}
    if category_set_id > 0:
        body["category_set_id"] = category_set_id
    return await _api("POST", "/api/categories", json=body)


@mcp.tool()
async def list_tags() -> dict:
    """列出用户所有标签。"""
    return await _api("GET", "/api/search/tags")


# ── 分类集 ────────────────────────────────────────────

@mcp.tool()
async def list_category_sets() -> dict:
    """列出所有分类集。通常不需要。"""
    return await _api("GET", "/api/category-sets")


@mcp.tool()
async def create_category_set(name: str) -> dict:
    """创建新分类集。
    Args:
        name: 分类集名称
    """
    return await _api("POST", "/api/category-sets", json={"name": name})


# ── 共享分类 ──────────────────────────────────────────

@mcp.tool()
async def list_shared_categories() -> dict:
    """列出用户参与的共享分类（共创+订阅）。"""
    return await _api("GET", "/api/shared-categories")


@mcp.tool()
async def create_shared_category(
    name: str, mode: str = "cocreate", description: str = "",
) -> dict:
    """创建共享分类。"cocreate"=多人可编辑，"subscribe"=只读分享。

    ⚠️ subscribe 模式下任何人（包括创建者）都无法往里面写入，调用 add_footprint 会 403。
    如果用户想协作编辑，用 mode="cocreate"。
    """
    body = {"name": name, "mode": mode}
    if description:
        body["description"] = description
    return await _api("POST", "/api/shared-categories", json=body)


@mcp.tool()
async def join_shared_category(invite_code: str) -> dict:
    """通过邀请码加入共享分类。

    Args:
        invite_code: 8 位邀请码
    """
    return await _api("POST", "/api/shared-categories/join", json={"code": invite_code})


@mcp.tool()
async def create_invite_link(shared_category_id: int, duration_hours: int = 24) -> dict:
    """生成邀请链接，发给别人即可加入。

    Args:
        shared_category_id: 共享分类 ID
        duration_hours: 有效期（小时）
    """
    return await _api("POST", f"/api/shared-categories/{shared_category_id}/invite",
                      json={"duration_hours": duration_hours})


# ── 启动 ──────────────────────────────────────────────

def main():
    mcp.run()  # 默认 STDIO，适配本地 Agent（Cherry Studio / Claude Desktop / Cursor）


if __name__ == "__main__":
    main()

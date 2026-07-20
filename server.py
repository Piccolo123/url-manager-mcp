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
    "url-manager",
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
- 批量整理用 batch_update_footprints，一次最多 50 条

交付闭环（Agent 先行核心）：
- 整理完调用 agent_magic_link() 生成链接
- 把链接发给用户："整理好了，点这里查看 → [链接]"
- 用户打开就是卡片式界面，30 天有效
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
    result = await _api("POST", "/api/v1/agent/register")
    if "token" in result:
        TOKEN = result["token"]
    return result


# ── 用户信息 ──────────────────────────────────────────

@mcp.tool()
async def my_info() -> dict:
    """首次对话先调此工具，确认 Token 有效且连接正常。
    返回用户名、会员状态。也可用于用户问"我是谁"时。
    """
    return await _api("GET", "/api/v1/agent/me")


# ── 足迹搜索/列表 ─────────────────────────────────────

@mcp.tool()
async def search_footprints(query: str, limit: int = 10, offset: int = 0) -> dict:
    """用户说"找 XX 的收藏"时用。在标题/描述/URL 中全文搜索。

    Args:
        query: 搜索关键词
        limit: 返回条数（最大 100）
        offset: 偏移量（翻页用）
    """
    return await _api("GET", "/api/v1/agent/collections", params={
        "q": query, "limit": min(limit, 100), "offset": offset
    })


@mcp.tool()
async def list_footprints(category_id: int = 0, limit: int = 20, offset: int = 0) -> dict:
    """用户说"看看收藏"时用。按分类列出，category_id=0=全部。

    Args:
        category_id: 分类 ID（0=全部，从 list_categories 结果中取）
        limit: 返回条数（最大 100）
        offset: 偏移量（翻页用）
    """
    params = {"limit": min(limit, 100), "offset": offset}
    if category_id > 0:
        params["category_id"] = category_id
    return await _api("GET", "/api/v1/agent/collections", params=params)


@mcp.tool()
async def get_footprint(footprint_id: int) -> dict:
    """看某条收藏的完整详情。

    Args:
        footprint_id: 足迹 ID（从 list_footprints 结果中 id 字段取）
    """
    return await _api("GET", f"/api/v1/agent/collections/{footprint_id}")


# ── 足迹添加 ──────────────────────────────────────────

@mcp.tool()
async def add_footprint(
    url: str, title: str = "", description: str = "",
    category_ids: str = "", tag_names: str = "",
) -> dict:
    """添加一条收藏。用户说"收藏这个链接"时用。

    调用前先 list_categories() 和 list_tags() 了解已有分类/标签，
    避免创建重复分类。标题留空自动从网页提取。

    Args:
        url: 网页链接（必填）
        title: 自定义标题（留空自动提取）
        description: 摘要
        category_ids: 分类 ID，逗号分隔如 "1,3"
        tag_names: 标签名，逗号分隔如 "AI,教程"
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


# ── 足迹更新 ──────────────────────────────────────────

@mcp.tool()
async def update_footprint(
    footprint_id: int, title: str = "", description: str = "",
    category_ids: str = "", tag_names: str = "",
) -> dict:
    """更新足迹。用户说"改标题/移分类"时用。

    ⚠️ category_ids 是替换整个列表，不是追加！
    正确做法：先 get_footprint(id) 拿现有分类 → 拼上新 ID → 再传 category_ids。
    例：现有 [3,5]，要加 7 → category_ids="3,5,7"（不是 "7"）

    Args:
        footprint_id: 足迹 ID（从搜索结果取）
        title/description/category_ids/tag_names: 留空不改
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
        return {"error": "至少填一个要改的字段"}
    return await _api("PUT", f"/api/v1/agent/collections/{footprint_id}", json=body)


# ── 分类（含共享分类）─────────────────────────────────
# list_categories 返回所有分类，包括个人和共享。
# 共享分类的 mode 字段为 "cocreate" 或 "subscribe"，个人分类为 null。

@mcp.tool()
async def list_categories() -> dict:
    """列出所有分类（个人 + 共享）。操作足迹前必须先调此工具。

    返回的每个分类有 id、name、mode 字段。
    mode=null 是个人分类，mode="cocreate"/"subscribe" 是共享分类。
    id 字段用于 add_footprint / update_footprint 的 category_ids 参数。
    """
    return await _api("GET", "/api/v1/agent/categories")


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
    return await _api("POST", "/api/v1/agent/categories", json=body)


@mcp.tool()
async def list_tags() -> dict:
    """列出用户所有标签。"""
    return await _api("GET", "/api/v1/agent/tags")


# ── 分类集 ────────────────────────────────────────────

@mcp.tool()
async def list_category_sets() -> dict:
    """列出所有分类集。通常不需要。"""
    return await _api("GET", "/api/v1/agent/category-sets")


@mcp.tool()
async def create_category_set(name: str) -> dict:
    """创建新分类集。
    Args:
        name: 分类集名称
    """
    return await _api("POST", "/api/v1/agent/category-sets", json={"name": name})


# ── 共享分类 ──────────────────────────────────────────

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
    return await _api("POST", "/api/v1/agent/shared-categories", json=body)


@mcp.tool()
async def join_shared_category(invite_code: str) -> dict:
    """通过邀请码加入共享分类。

    Args:
        invite_code: 8 位邀请码
    """
    return await _api("POST", "/api/v1/agent/shared-categories/join", json={"code": invite_code})


@mcp.tool()
async def create_invite_link(shared_category_id: int, duration_hours: int = 24) -> dict:
    """生成邀请链接，发给别人即可加入。

    Args:
        shared_category_id: 共享分类 ID（从 list_categories 结果中 mode 不为 null 的分类取）
        duration_hours: 有效期（小时）
    """
    return await _api("POST", f"/api/v1/agent/shared-categories/{shared_category_id}/invite-link",
                      json={"duration_hours": duration_hours})


@mcp.tool()
async def add_to_shared_category(shared_category_id: int, footprint_id: int) -> dict:
    """将一条已有足迹加入共享分类。该足迹必须是你创建的。

    Args:
        shared_category_id: 共享分类 ID
        footprint_id: 足迹 ID
    """
    return await _api("POST", f"/api/v1/agent/shared-categories/{shared_category_id}/collections",
                      json={"collection_id": footprint_id})


@mcp.tool()
async def remove_from_shared_category(shared_category_id: int, footprint_id: int) -> dict:
    """将足迹从共享分类移出（不删除足迹本身）。

    Args:
        shared_category_id: 共享分类 ID
        footprint_id: 足迹 ID
    """
    return await _api("DELETE",
                      f"/api/v1/agent/shared-categories/{shared_category_id}/collections/{footprint_id}")


@mcp.tool()
async def copy_footprint(footprint_id: int, category_ids: str) -> dict:
    """从共享分类复制一条足迹到自己的个人分类。

    Args:
        footprint_id: 要复制的足迹 ID
        category_ids: 目标分类 ID，逗号分隔，如 "1,3"
    """
    cids = [int(x.strip()) for x in category_ids.split(",") if x.strip()]
    return await _api("POST", f"/api/v1/agent/collections/{footprint_id}/copy",
                      json={"category_ids": cids})


@mcp.tool()
async def batch_update_footprints(updates: str) -> dict:
    """批量更新足迹，一次最多 50 条。用于批量整理场景。

    Args:
        updates: JSON 字符串，格式 '[{"id":"uuid","title":"新标题","category_ids":"1,3"},...]'
                每个对象可含 title/description/category_ids/tag_names，id 必填
    """
    import json
    try:
        items = json.loads(updates)
    except json.JSONDecodeError:
        return {"error": "updates 必须是有效 JSON 数组"}
    if len(items) > 50:
        return {"error": "最多 50 条"}
    # 转换 category_ids 和 tag_names
    for item in items:
        if "category_ids" in item and isinstance(item["category_ids"], str):
            item["category_ids"] = [int(x.strip()) for x in item["category_ids"].split(",") if x.strip()]
        if "tag_names" in item and isinstance(item["tag_names"], str):
            item["tag_names"] = [x.strip() for x in item["tag_names"].split(",") if x.strip()]
    return await _api("PUT", "/api/v1/agent/collections/batch", json={"updates": items})


@mcp.tool()
async def agent_magic_link() -> dict:
    """生成魔法链接，发给用户即可在浏览器中打开整理好的收藏界面。
    
    这是 Agent 先行的交付闭环核心——Agent 帮用户整理完后，
    调用此工具生成链接发给用户，用户点击即可看到卡片式界面。
    链接 30 天有效，可重复使用。
    """
    return await _api("POST", "/api/v1/agent/magic-link")


# ── 启动 ──────────────────────────────────────────────

def main():
    """启动 MCP Server。默认 STDIO（本地 Agent），也可用 streamable-http（Docker/Glama 测试）"""
    import sys
    transport = "stdio"
    if "--http" in sys.argv:
        transport = "streamable-http"
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()

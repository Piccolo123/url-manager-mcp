# URL Manager MCP Server

[![url-manager-mcp MCP server](https://glama.ai/mcp/servers/Piccolo123/url-manager-mcp/badges/score.svg)](https://glama.ai/mcp/servers/Piccolo123/url-manager-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/Piccolo123/url-manager-mcp/blob/main/LICENSE)

[English](./README.md) | [简体中文](./README.zh-CN.md)

一个 Model Context Protocol 服务器，用于管理网页收藏——跨设备同步、分类、标签、全文搜索、批量操作和团队共享。提供 20 个工具，支持自动注册，无需手动配置。

> 📖 **使用模式和最佳实践 → [URL Manager Skill](https://github.com/Piccolo123/url-manager/blob/main/SKILL.md)**

## 工具

### 注册与身份

- **`agent_register()`**
  创建新账号。无参数，Token 自动生效。⚠️ 仅调用一次——每次调用都会创建全新账号。

- **`my_info()`**
  验证连接和 Token 有效性。返回用户名和会员状态。

### 收藏

- **`search_footprints(query, limit, offset)`**
  在标题、描述和 URL 中全文搜索。
  - `query` _（必填）_ — 搜索关键词
  - `limit` — 每页条数（默认 10，最大 100）
  - `offset` — 分页偏移（默认 0）

- **`list_footprints(category_id, limit, offset)`**
  按分类列出收藏。`category_id=0` 返回全部分类。
  - `limit` — 每页条数（默认 20，最大 100）
  - `offset` — 分页偏移（默认 0）

- **`get_footprint(footprint_id)`**
  查看单条收藏的完整详情。
  - `footprint_id` _（必填）_ — 从 `list_footprints` 或 `search_footprints` 结果中的 `id` 字段获取

- **`add_footprint(url, title, description, category_ids, tag_names)`**
  添加新收藏。建议先调 `list_categories()` 和 `list_tags()` 了解现有结构。
  - `url` _（必填）_ — 网页链接
  - `title` — 留空则自动从网页提取
  - `description` — 摘要或备注
  - `category_ids` — 逗号分隔的分类 ID，如 `"1,3"`
  - `tag_names` — 逗号分隔的标签名，如 `"AI,教程"`

- **`update_footprint(footprint_id, title, description, category_ids, tag_names)`**
  修改收藏。未填字段保持不变。
  ⚠️ `category_ids` **完全替换**原有分类——不是追加！先调 `get_footprint()` 查看现有分类，再合并新 ID。
  - `footprint_id` _（必填）_ — 从搜索或列表结果中获取

### 分类与标签

- **`list_categories()`**
  列出全部分类（个人 + 共享）。返回 `id`、`name`、`mode` 字段。
  `mode=null` → 个人；`mode="cocreate"/"subscribe"` → 共享。

- **`create_category(name, category_set_id)`**
  创建新分类。先调 `list_categories()` 避免重复。
  - `name` _（必填）_ — 分类名称
  - `category_set_id` — 所属分类集（0 = 默认）

- **`list_tags()`**
  列出当前账号所有标签。

### 分类集

- **`list_category_sets()`**
  列出所有分类集。

- **`create_category_set(name)`**
  创建新分类集（分类的容器）。
  - `name` _（必填）_ — 分类集名称

### 共享分类

- **`create_shared_category(name, mode, description)`**
  创建共享分类，用于团队协作。
  - `name` _（必填）_
  - `mode` _（必填）_ — `"cocreate"`（多人编辑）或 `"subscribe"`（只读）
  - `description` — 可选描述
  ⚠️ `subscribe` 模式下添加收藏会返回 **403**。需要协作编辑请用 `"cocreate"`。

- **`create_invite_link(shared_category_id, duration_hours)`**
  生成邀请链接，供他人加入。
  - `shared_category_id` _（必填）_ — 从 `list_categories()` 的共享分类中获取
  - `duration_hours` — 有效期，默认 24 小时

- **`join_shared_category(invite_code)`**
  通过邀请码加入共享分类。
  - `invite_code` _（必填）_ — 8 位邀请码

- **`add_to_shared_category(shared_category_id, footprint_id)`**
  将自己已有的收藏加入共享分类。两个参数均为必填。

- **`remove_from_shared_category(shared_category_id, footprint_id)`**
  从共享分类中移除收藏（不删除收藏本身）。两个参数均为必填。

- **`copy_footprint(footprint_id, category_ids)`**
  从共享分类复制收藏到个人分类。两个参数均为必填。

### 批量与交付

- **`batch_update_footprints(updates)`**
  批量修改收藏，一次最多 50 条。
  - `updates` _（必填）_ — JSON 字符串：`[{"id":"...", "title":"新标题", "category_ids":"1,3"}, ...]`
  每条可含 `title`、`description`、`category_ids`、`tag_names`；`id` 为必填。

- **`agent_magic_link()`**
  生成交付链接。发送给用户即可打开卡片式界面，所有整理好的收藏一目了然。**有效期 30 天，可重复使用。**

## 安装

```bash
git clone https://github.com/Piccolo123/url-manager-mcp.git
cd url-manager-mcp
pip install -r requirements.txt
```

### 前置条件

- Python 3.10+
- 可访问 `https://ai.ocean94.com`

## 配置

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

如果用户已有账号：

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

配置结构与上相同，兼容所有支持 STDIO 传输的 MCP 客户端。

### 其他客户端

本服务器支持 **STDIO**（默认）和 **Streamable HTTP** 两种传输方式：

```bash
# STDIO（默认）
python server.py

# Streamable HTTP（Docker / Glama / 托管环境）
python server.py --http
```

## 部署

### Docker

```bash
docker build -t url-manager-mcp .
docker run -e FOOTPRINTS_TOKEN="FA_xxx" url-manager-mcp
```

### ModelScope

托管部署：一键部署 [url-manager-mcp](https://modelscope.cn/mcp/servers/Piccoloxl/url-manager)

## 为什么选择 URL Manager

浏览器自带的收藏夹只是扁平列表，没有分类、没有搜索、不能共享。URL Manager 提供了：

- **分类、分类集、标签** — 层级化整理
- **全文搜索** — 在所有标题、描述和 URL 中搜索
- **跨设备同步** — 一处收藏，处处可用
- **批量管理** — 一次性整理数百条链接
- **团队共享** — 多人编辑或只读订阅，一键生成邀请链接
- **卡片式交付** — 将整理好的收藏以精美卡片界面呈现，而非原始链接堆砌

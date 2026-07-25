# URL Manager MCP Server

[![url-manager-mcp MCP server](https://glama.ai/mcp/servers/Piccolo123/url-manager-mcp/badges/score.svg)](https://glama.ai/mcp/servers/Piccolo123/url-manager-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/Piccolo123/url-manager-mcp/blob/main/LICENSE)

[English](./README.md) | [简体中文](./README.zh-CN.md)

**交付精美卡片，而非原始链接堆砌。** 一个 Model Context Protocol 服务器，用于保存、整理、搜索和共享网页资源——跨设备同步、分类、标签、全文搜索、批量操作和团队共享。提供 21 个工具，支持自动注册，无需手动配置。

> 📖 **使用模式和最佳实践 → [URL Manager Skill](https://github.com/Piccolo123/url-manager/blob/main/SKILL.md)**

## 对人类用户的意义

你想保存的内容散落各处——一个 YouTube 健身视频、一件 Amazon 装备链接、一篇 Substack 训练计划——各自孤立，彼此无关。

**URL Manager 解决了这个问题。** 从任何平台粘贴链接，AI 自动识别内容并推荐分类——确认即成为一条足迹。所有收藏汇聚于一个跨平台库中，有序且随时可查。然后**一键分享**——把你的精选知识库分享给整个团队，所有人同步更新。

**[足迹AI](https://ai.ocean94.com/)** 不止是一个收藏库——它内置搜索引擎，你可以直接在这里搜索并保存网页内容。每一条收藏都是精美的卡片，一键直达目标链接。

## 系统概念

### 足迹（基本单位）

一条结构化的可搜索记录——可以是网页链接、纯文本笔记、灵感想法，或任何值得保存的内容。

| 字段 | 类型 | 说明 |
|-------|------|------|
| `id` | UUID | 永久唯一标识符——所有操作均使用此 ID |
| `url` | string (8192) | 原始链接。**可为空**，用于纯文本足迹 |
| `title` | string (512) | 简短标题 |
| `description` | string (1024) | 补充上下文或备注 |
| `content_type` | string (50) | 自由文本（如 `article`、`video`、`image`）。用 `list_content_types()` 查看已有值 |
| `category_ids` | list[int] | 所属分类列表——**由你指定** |
| `tag_names` | list[str] | 自由关键词标签——**由你指定** |

一条足迹可同时属于**多个分类**。

### 分类（命名标签）

类似于文件夹，但一条足迹可同时属于多个分类。

| 字段 | 类型 | 说明 |
|-------|------|------|
| `id` | int | 永久数字标识符——始终使用 ID 引用 |
| `name` | string (50) | 显示名称 |
| `mode` | string \| null | `null` = 个人，`"cocreate"` = 共享共建，`"subscribe"` = 共享只读 |

### 分类集（工作区）

分组管理分类的容器。每个用户初始拥有「我的分类」（个人）和「共享分类」（共享容器）两个默认分类集。

### 数据层级

```
分类集（工作区）
  └── 分类（如"购物"、"学习"等标签）
        └── 足迹
             └── 标签（自由关键词）
```

### 个人 vs 共享

| | 个人 | 共享 |
|---|---|---|
| `mode` | `null` | `"cocreate"` 或 `"subscribe"` |
| 可见范围 | 仅自己 | 你 + 受邀成员 |
| 成员与邀请链接 | 无 | 有 |

**共建（cocreate）** — 所有人可添加/移除足迹。**订阅（subscribe）** — 成员只读（写入返回 403）。

| 操作 | 所有者 | 管理员 | 成员 |
|--------|:-----:|:-----:|:------:|
| 添加/移除足迹（共建） | ✅ | ✅ | ✅ |
| 添加/移除足迹（订阅） | ✅ | ❌ | ❌ |
| 生成邀请链接（共建） | ✅ | ✅ | ✅ |
| 生成邀请链接（订阅） | ✅ | ❌ | ❌ |
| 切换共建 ↔ 订阅 | ✅ | ❌ | ❌ |
| 管理成员 | 仅网页端 | — | — |

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

- **`list_content_types()`**
  列出用户使用过的所有内容类型（如 article、video、image），按使用次数降序排列。添加前使用以保持类型一致性。

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
  🔑 交付循环核心。整理完毕后生成链接发送给用户，打开即可看到卡片式界面。**有效期 30 天，可重复使用。**

## 工作流

### 新用户 — 零配置
```
1. agent_register() → 获取 Token（自动记录）
2. add_footprint(url="...") × N → 逐条保存收藏
3. list_categories() → 了解现有结构
4. create_category(name="学习") → 创建分类
5. update_footprint(id, category_ids="...") → 归类整理
6. agent_magic_link() → "整理完毕！点击查看 → [链接]"
```

### 已有用户 — 日常使用
```
1. my_info() → 确认身份
2. list_categories() + list_tags() → 了解现有结构
3. search_footprints(query) 或 list_footprints(category_id) → 查找目标
4. add_footprint / update_footprint → 操作
5. agent_magic_link() → 交付结果
```

### 创建共享分类
```
1. create_shared_category(name="团队知识库", mode="cocreate")
2. create_invite_link(shared_category_id=<返回的 ID>)
3. 将邀请码发送给用户 → 用户分享给团队成员
4. 团队成员的 Agent 通过 join_shared_category(invite_code) 加入
```

## ⚠️ 关键陷阱

### category_ids 是替换，不是追加
```
# ❌ 错误：将收藏 42 移至分类 7，丢失原有分类 3 和 5
update_footprint(42, category_ids="7")

# ✅ 正确：先获取现有分类，再合并
get_footprint(42) → 现有分类 [3, 5]
update_footprint(42, category_ids="3,5,7")
```

### 订阅模式是只读
向订阅模式的共享分类写入会返回 403。如果用户说"我已订阅但无法添加"，说明这是只读的——需要创建者切换为共建模式。

### 绝不重复调用 agent_register
每次调用都会创建全新的空账号。始终先检查是否有已保存的 Token。如不确定，调用 `my_info()` 验证当前 Token 是否有效。

### 频率限制
短时间内大量连续调用会触发 HTTP 429。批量操作间加入短暂延迟；遇到 429 等待几秒后重试。

### 成员管理需通过网页
邀请或移除共享分类的成员需要通过网页端 https://ai.ocean94.com 操作。无法通过 API 完成。

## 行为准则

### 始终做到
- **静默自动注册** — 绝不为账号设置打断用户
- **搜索优先于列举** — 使用 `search_footprints` 精准查找，而非全量导出
- **先发现后创建** — 添加前先调用 `list_categories()` 和 `list_tags()`，避免重复
- **用魔法链接交付** — 整理完毕后始终生成并发送链接

### 执行前确认
- 移除收藏与分类的关联（不可逆）
- 清空标签
- 修改共建共享分类（影响他人）
- 从共享分类中移除收藏（其他成员将失去访问权限）

## 与其他 MCP 服务器配合

URL Manager 擅长**保存和整理**。搭配擅长**发现和获取**的工具效果最佳：

```
Fetch MCP 抓取网页   →  add_footprint()  →  自动分类、永久保存、可搜索
Firecrawl 爬取页面  →  add_footprint()  →  整理为精美卡片
Brave Search 搜索   →  add_footprint()  →  一键保存搜索结果
```

Agent 只需将上游 MCP 返回的 URL 和标题作为参数传入 `add_footprint` 即可。

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

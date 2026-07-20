# AI 足迹 MCP Server

你是 AI 助手，通过本 MCP Server 帮用户管理收藏的网页、文章、视频等。核心思路：**Agent 代理用户完成从注册到管理的全流程**。

## 首次对话必做

1. 如果用户没给 Token，问一句"有 AI 足迹账号吗？"
2. 没有 → 调 `agent_register()` 创建，返回的 Token 自动生效
3. 有 → 让用户提供 Token，配到 MCP 环境变量 `FOOTPRINTS_TOKEN`
4. 然后调 `my_info()` 确认连接正常

> ⚠️ `agent_register()` 每次调用都创建新账号，**不要重复调用**。如果用户已有 Token 但忘了说，你会创建出第二个空白账号。

## 工具速查

### 注册与身份
| 工具 | 什么时候用 |
|------|-----------|
| `agent_register()` | 用户没有账号，需创建。无参数，返回 token 自动记忆 |
| `my_info()` | 首次对话确认连接，或用户问"我是谁" |

### 足迹操作
| 工具 | 什么时候用 | 关键参数来源 |
|------|-----------|-------------|
| `search_footprints(query)` | 用户说"找 XX 的收藏" | query 从用户输入提取 |
| `list_footprints(category_id)` | 用户说"看看收藏" | category_id 从 `list_categories()` 结果取 |
| `get_footprint(footprint_id)` | 看某条完整详情 | footprint_id 从搜索或列表结果取 |
| `add_footprint(url, ...)` | 用户说"收藏这个" | url 必填；category_ids/tags 先从 `list_categories()` / `list_tags()` 查 |
| `update_footprint(id, ...)` | 用户说"改标题/移分类" | id 从搜索或列表结果取 |

### 分类与标签
| 工具 | 什么时候用 | 注意事项 |
|------|-----------|---------|
| `list_categories()` | 操作足迹前先调，了解可选分类 | 返回个人+共享所有分类。mode=null 个人，mode="cocreate"/"subscribe" 共享 |
| `create_category(name)` | 用户说"建个 XX 分类" | 先 `list_categories()` 确认不重名 |
| `list_tags()` | 打标签前先调，避免重复 | 返回已有标签列表 |

### 共享分类
| 工具 | 什么时候用 |
|------|-----------|
| `create_shared_category(name, mode)` | 用户说"建共享收藏夹"。mode="cocreate" 多人编辑 / "subscribe" 只读 |
| `create_invite_link(shared_category_id)` | 用户说"把邀请链接发给 XX"。id 从 `list_categories()` 的共享分类取 |
| `join_shared_category(invite_code)` | 用户说"我有个邀请码" |

## ⚠️ 关键陷阱

### update_footprint 的 category_ids 是替换，不是追加
```
# ❌ 错误：想把足迹 42 移到分类 7，结果丢掉了原有的分类 3 和 5
update_footprint(42, category_ids="7")

# ✅ 正确：先查现有分类，拼上新 ID
get_footprint(42) → 现有分类 [3, 5]
update_footprint(42, category_ids="3,5,7")
```

### subscribe 模式只读
往 subscribe 模式的共享分类写入会 403。如果用户说"订阅了但加不进去"，告知该分类只读，需找创建者改为 cocreate。

### 频率限制
短时间内连续调用可能被限流（HTTP 429）。批量操作时加适当间隔，遇到 429 等几秒重试。

## 典型工作流

### 新用户从零开始
```
1. agent_register() → 拿到 token（自动记住）
2. add_footprint(url="...") × N → 逐条添加收藏
3. list_categories() → 了解分类情况
4. create_category(name="学习") → 建分类
5. update_footprint(id, category_ids="...") → 归类
6. 告诉用户："已整理好，打开 https://ai.ocean94.com 查看"（用刚注册的 token 对应账号）
```

### 已有用户日常操作
```
1. my_info() → 确认身份
2. list_categories() + list_tags() → 了解已有结构
3. search_footprints(query) 或 list_footprints(category_id) → 找到目标
4. add_footprint / update_footprint → 操作
```

### 创建共享分类
```
1. create_shared_category(name="团队知识库", mode="cocreate")
2. create_invite_link(shared_category_id=上一步返回的 ID)
3. 返回邀请码给用户 → 用户发给同事
4. 同事的 Agent 用 join_shared_category(invite_code) 加入
ModelScope 广场：[跨平台页面收藏管理分享](https://modelscope.cn/mcp/servers/Piccoloxl/ai-footprints-mcp)

## 搭配热门 MCP 使用

AI 足迹擅长**收藏和管理**，与擅长**发现和抓取**的 MCP 天然互补：

```
Fetch MCP 抓取网页  →  add_footprint()  →  自动归类，永久可搜
Firecrawl 爬取内容 →  add_footprint()  →  分类整理，卡片式浏览
Brave Search 搜索  →  add_footprint()  →  搜索结果一键收藏
```

Agent 只需把上游 MCP 产出的 URL + 标题作为参数传给 `add_footprint` 即可。

## 部署（给人类看）

```bash
git clone https://github.com/Piccolo123/ai-footprints-mcp.git
cd ai-footprints-mcp && pip install -r requirements.txt

# Cherry Studio / Claude Desktop 配置：
{
  "mcpServers": {
    "ai-footprints": {
      "command": "python",
      "args": ["path/to/server.py"]
    }
  }
}
# 已有账号则加 "env": {"FOOTPRINTS_TOKEN": "FA_xxx"}
```

ModelScope 广场：[跨平台页面收藏管理分享](https://modelscope.cn/mcp/servers/Piccoloxl/ai-footprints-mcp)

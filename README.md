# AI 足迹 MCP Server

**Agent 先行设计**——让 AI Agent 代理用户完成收藏管理全流程：
从注册账号到搜索、添加、整理，再到协作分享，全程 Agent 操作。

## Agent 工作流：用户没有账号怎么办

这是 Agent 优先设计的核心——你不仅能操作已有账号，还能直接帮用户注册：

```
用户: "我没有 AI 足迹账号"
Agent: agent_register() → 创建账号 → 返回 token → 后续操作全用这个 token
```

**两类接入方式：**

| 用户状态 | 流程 |
|----------|------|
| 已有账号 | 让用户去 https://ai.ocean94.com → 个人中心 → 接入Agent → 把 Token 给你 |
| 没有账号 | 直接用 `agent_register()` 创建，返回的 Token 全程使用 |

## 工具速查（按用户意图）

| 用户说 | Agent 调用 |
|--------|-----------|
| "我没有账号" | `agent_register()` |
| "我是谁" | `my_info()` |
| "收藏这个链接" | `add_footprint(url=...)` |
| "找 XX 相关的收藏" | `search_footprints(query="XX")` |
| "看看我的收藏" | `list_footprints()` |
| "这条详情" | `get_footprint(footprint_id=...)` |
| "改个标题/移个分类" | `update_footprint(footprint_id=...)` |
| "有哪些分类" | `list_categories()` |
| "建个 XX 分类" | `create_category(name="XX")` |
| "有哪些标签" | `list_tags()` |
| "建个共享收藏夹" | `create_shared_category(name=..., mode="cocreate")` |
| "生成邀请链接" | `create_invite_link(shared_category_id=...)` |
| "用邀请码加入" | `join_shared_category(invite_code=...)` |

## 典型工作流

### 全新用户：从零到整理完成
1. `agent_register()` 创建账号 → 拿到 Token
2. `add_footprint(url=...)` 批量添加用户的收藏
3. `create_category(name=...)` 创建分类
4. `update_footprint(footprint_id=..., category_ids=...)` 归类
5. 把登录链接发给用户，ta 打开就是整理好的界面

### 已有用户：日常操作
1. 用户给你 Token → 配置环境变量
2. `my_info()` 确认身份
3. 按需调用工具完成搜索、添加、整理

## 部署配置

### 入口文件
```
server.py
```

### 启动命令
```bash
python server.py
```

### Python 版本
≥ 3.10

### 环境变量

| 变量 | 说明 | 必填 |
|------|------|:---:|
| `FOOTPRINTS_TOKEN` | Agent Token（已有用户提供，或用 agent_register 获取） | 注册后填 |
| `FOOTPRINTS_ENDPOINT` | API 地址（默认 https://ai.ocean94.com） | ❌ |
| `PORT` | 监听端口（默认 8000） | ❌ |

### 依赖
```
mcp>=1.0.0
httpx>=0.27.0
```

## 部署到 ModelScope

```bash
# 方式一：从 GitHub 导入
# 仓库：Piccolo123/ai-footprints-mcp
# ModelScope 会自动解析 README.md

# 方式二：自定义创建
# https://modelscope.cn/mcp/servers/create?template=customize
# 入口文件：server.py
# 启动命令：python server.py
# 环境变量：FOOTPRINTS_TOKEN（可用 agent_register 获取）
```

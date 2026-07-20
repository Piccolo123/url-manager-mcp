# AI 足迹 MCP Server

让 AI Agent 管理用户的数字足迹——收藏网页、搜索文章、整理分类、协作分享。

## 这个 MCP 能帮 Agent 做什么

当用户对你说这些话时，用对应的工具：

| 用户说 | Agent 调用 |
|--------|-----------|
| "帮我收藏这个链接" | `add_footprint(url=...)` |
| "我的 AI 相关收藏有哪些" | `search_footprints(query="AI")` |
| "看看我所有的收藏" | `list_footprints()` |
| "这条收藏的详情是什么" | `get_footprint(footprint_id=...)` |
| "把这篇移到技术分类" | `update_footprint(footprint_id=..., category_ids=...)` |
| "建一个「学习」分类" | `create_category(name="学习")` |
| "我有哪些分类" | `list_categories()` |
| "我和同事一起建个收藏夹" | `create_shared_category(name=..., mode="cocreate")` |
| "生成邀请链接" | `create_invite_link(shared_category_id=...)` |
| "用邀请码加入" | `join_shared_category(invite_code=...)` |

## 典型工作流

### 场景 1：用户想收藏一个网页
1. 拿到 URL
2. 调用 `list_categories()` 了解已有分类
3. 调用 `list_tags()` 了解已有标签  
4. 调用 `add_footprint(url=..., category_ids="1,3", tags="AI,教程")`
5. 告知用户收藏成功

### 场景 2：用户想找某条收藏
1. 问清楚关键词
2. 调用 `search_footprints(query="关键词")`
3. 如有需要，调用 `get_footprint(footprint_id=...)` 看详情
4. 整理结果返回给用户

### 场景 3：用户想整理足迹
1. 调用 `list_footprints()` 列出全部
2. 了解用户想怎么整理
3. 调用 `create_category(...)` 建新分类（如需要）
4. 调用 `update_footprint(...)` 逐条移动
5. 汇总整理结果

### 场景 4：创建共享分类
1. 调用 `create_shared_category(name="团队收藏", mode="cocreate")` 创建
2. 调用 `create_invite_link(shared_category_id=...)` 生成邀请码
3. 把邀请码发给用户
4. 对方用 `join_shared_category(invite_code=...)` 加入

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
| `FOOTPRINTS_TOKEN` | Agent Token，格式 `FA_xxxx` | ✅ |
| `FOOTPRINTS_ENDPOINT` | API 地址（默认 https://ai.ocean94.com） | ❌ |
| `PORT` | 监听端口（默认 8000） | ❌ |

### Token 获取
https://ai.ocean94.com → 登录 → 个人中心 → 接入Agent → 访问令牌

### 依赖
```
mcp>=1.0.0
httpx>=0.27.0
```

## 本地测试

```bash
pip install -r requirements.txt
FOOTPRINTS_TOKEN=FA_xxx python server.py
```

## 部署到 ModelScope

1. 访问 https://modelscope.cn/mcp/servers/create?template=customize
2. 选择「自定义创建」→ 托管类型选「可托管部署」
3. 第一步：填写名称（AI 足迹）、来源地址（本仓库 URL）
4. 第二步：配置入口文件 `server.py`，启动命令 `python server.py`
5. 第三步：填写环境变量 `FOOTPRINTS_TOKEN=你的Token`
6. 创建完成

# AI 足迹 MCP Server

**Agent 先行 · 本地部署** — AI Agent 代理用户完成从注册到管理的全流程。

## 30 秒开始

```bash
git clone https://github.com/Piccolo123/ai-footprints-mcp.git
cd ai-footprints-mcp
pip install -r requirements.txt
python server.py
```

Agent 启动后，用户说"帮我注册" → `agent_register()` 自动创建账号 → 后续操作自动用新 Token。

## Agent 工作流

| 用户说 | Agent 调用 |
|--------|-----------|
| "我没有账号" | `agent_register()` → 自动获取 Token |
| "我是谁" | `my_info()` |
| "收藏这个链接" | `add_footprint(url=...)` |
| "找 XX 的收藏" | `search_footprints(query=...)` |
| "看看我的收藏" | `list_footprints()` |
| "这条详情" | `get_footprint(footprint_id=...)` |
| "改标题/移分类" | `update_footprint(footprint_id=...)` |
| "建个 XX 分类" | `create_category(name=...)` |
| "建共享收藏夹" | `create_shared_category(name=..., mode="cocreate")` |
| "生成邀请链接" | `create_invite_link(shared_category_id=...)` |
| "用邀请码加入" | `join_shared_category(invite_code=...)` |

## 接入你的 Agent

### Cherry Studio
```json
{
  "mcpServers": {
    "ai-footprints": {
      "command": "python",
      "args": ["path/to/server.py"]
    }
  }
}
```

### Claude Desktop
```json
{
  "mcpServers": {
    "ai-footprints": {
      "command": "python",
      "args": ["/path/to/ai-footprints-mcp/server.py"]
    }
  }
}
```

启动后无需配置 Token，Agent 先用 `agent_register()` 创建账号，Token 自动启用。

## 已有账号

如果用户已有 AI 足迹账号，在 MCP 配置中加入环境变量：

```json
{
  "mcpServers": {
    "ai-footprints": {
      "command": "python",
      "args": ["server.py"],
      "env": {
        "FOOTPRINTS_TOKEN": "FA_xxxxxxxxxxxx"
      }
    }
  }
}
```

Token 获取：https://ai.ocean94.com → 个人中心 → 接入Agent → 访问令牌

## ModelScope MCP 广场

已在广场上架：[跨平台页面收藏管理分享](https://modelscope.cn/mcp/servers/Piccoloxl/ai-footprints)

本地部署，无需托管。

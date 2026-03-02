# WebAI2API

基于 Camoufox (Playwright) 的网页版 AI 服务转通用 API 工具。通过模拟人类操作与各 AI 平台交互，提供兼容 OpenAI 格式的 API 接口。

## 项目结构

```
WebAI2API/
├── src/
│   ├── backend/                    # 后端核心
│   │   ├── adapter/               # 适配器（各 AI 平台的实现）
│   │   │   ├── lmarena.js         # LMArena 图片生成
│   │   │   ├── lmarena_text.js    # LMArena 文本生成
│   │   │   ├── chatgpt.js         # ChatGPT 图片生成
│   │   │   ├── chatgpt_text.js    # ChatGPT 文本生成
│   │   │   ├── gemini.js          # Gemini 图片生成
│   │   │   ├── gemini_text.js     # Gemini 文本生成
│   │   │   ├── deepseek_text.js   # DeepSeek 文本生成
│   │   │   ├── doubao.js          # 豆包图片生成
│   │   │   ├── doubao_text.js     # 豆包文本生成
│   │   │   └── ...                # 其他适配器
│   │   ├── engine/                # 浏览器引擎
│   │   │   ├── launcher.js        # Camoufox 启动器
│   │   │   └── utils.js           # 工具函数 (humanType, safeClick, pasteImages 等)
│   │   ├── pool/                  # Worker 池管理
│   │   │   ├── PoolManager.js     # Pool 管理器
│   │   │   └── Worker.js          # Worker 实例
│   │   ├── utils/                 # 后端工具
│   │   │   ├── index.js           # 公共工具 (waitApiResponse, normalizeError 等)
│   │   │   ├── uiLock.js          # UI 锁机制
│   │   │   └── download.js        # 下载工具
│   │   ├── strategies/            # 负载均衡策略
│   │   └── registry.js            # 适配器注册表
│   ├── server/                    # HTTP 服务器
│   │   ├── api/                   # API 路由
│   │   │   ├── openai/            # OpenAI 兼容 API
│   │   │   │   ├── routes.js      # /v1/chat/completions, /v1/models
│   │   │   │   └── parse.js       # 请求解析
│   │   │   └── admin/             # 管理 API
│   │   ├── queue.js               # 任务队列（并发控制、心跳）
│   │   ├── respond.js             # 响应构建（buildChatCompletion）
│   │   └── errors.js              # 错误码定义
│   ├── config/                    # 配置管理
│   └── utils/                     # 全局工具
│       └── logger.js              # 日志模块
├── skills/                        # Claude Code Skills
│   ├── text-generate-api/         # 文本生成 Skill
│   │   └── scripts/generate_text.py
│   └── image-generate-api/        # 图片生成 Skill
│       └── scripts/generate_image.py
├── webui/                         # Vue.js 管理界面
├── config.example.yaml            # 配置文件示例
└── supervisor.js                  # 进程管理入口
```

## 核心概念

### 适配器 (Adapter)
每个 AI 平台对应一个适配器文件，导出 `manifest` 对象包含：
- `id`: 适配器 ID
- `models`: 支持的模型列表
- `generate(context, prompt, imgPaths, modelId, meta)`: 核心生成方法

### Worker 池
- 每个 Worker 是一个独立的浏览器标签页
- PoolManager 管理多个 Worker 的生命周期
- 支持 UI 锁机制防止并发时的 UI 冲突

### 响应格式
适配器返回结构：
```javascript
{ text: string, reasoning?: string, error?: string, image?: string }
```
- `text`: 最终回复内容
- `reasoning`: 思考过程（thinking 模型）
- `error`: 错误信息
- `image`: 图片 base64 数据

## SSE 格式说明

### LMArena SSE 格式
```
ag:"思考内容"      # thinking/reasoning (仅 thinking 模型)
a0:"回复内容"      # 最终回复
a2:[{"type":"heartbeat"}]  # 心跳
ad:{"finishReason":"stop"} # 结束标记
```

### ChatGPT SSE 格式
- `channel`: "final" (输出) / "commentary" (工具调用) / null (系统)
- `content_type`: "text" / "code"
- ChatGPT thinking 模型不暴露思考过程

---

# 开发指南

## 测试环境

### Docker 容器
- 容器名: `webai-2api`
- 端口: 3000
- API 测试 Key: `sk-didi-123`

### 常用命令

```bash
# 复制代码到 docker 并重启
sg docker -c "docker cp /home/work/coding/open/WebAI2API/src/backend/adapter/chatgpt_text.js webai-2api:/app/src/backend/adapter/chatgpt_text.js && docker restart webai-2api"

# 查看容器状态
sg docker -c "docker ps | grep webai"

# 查看容器日志
sg docker -c "docker logs -f webai-2api"

# 从容器复制文件
sg docker -c "docker cp webai-2api:/tmp/xxx.json /tmp/"
```

### Skills 测试

```bash
# 列出文本生成模型
python3 skills/text-generate-api/scripts/generate_text.py --list-models --api-key "sk-didi-123"

# 列出图片生成模型
python3 skills/image-generate-api/scripts/generate_image.py --list-models --api-key "sk-didi-123"

# 测试文本生成
python3 skills/text-generate-api/scripts/generate_text.py --prompt "Hello" --api-key "sk-didi-123"

# 测试文本生成（带 reasoning）
python3 skills/text-generate-api/scripts/generate_text.py --prompt "What is 10!" --model "lmarena_text/claude-opus-4-6-thinking" --reasoning --api-key "sk-didi-123"

# 测试图片生成
python3 skills/image-generate-api/scripts/generate_image.py --prompt "A cute cat" --api-key "sk-didi-123"
```

## ChatGPT SSE 格式分析

### Channel 类型
- `final`: 最终输出内容
- `commentary`: 工具调用过程（如计算器 widget）
- `null`: 系统消息、用户消息等

### Content Type
- `text`: 文本内容
- `code`: 代码/JSON 内容（用于工具调用）
- `model_editable_context`: 模型上下文

### Thinking 模型说明
ChatGPT 的 thinking 模型（如 `gpt-5.2-thinking`）不会在 SSE 中暴露思考过程。`commentary` channel 仅用于工具调用（如计算器），而非真正的 reasoning 内容。

### SSE 数据结构示例

```json
// 初始消息
{
  "v": {
    "message": {
      "id": "xxx",
      "author": { "role": "assistant" },
      "channel": "final",
      "content": { "content_type": "text", "parts": [""] }
    }
  }
}

// 增量更新 (patch 数组格式)
{
  "v": [
    { "p": "/message/content/parts/0", "o": "append", "v": "Hello" },
    { "p": "/message/metadata/token_count", "o": "replace", "v": 5 }
  ]
}

// 完成标志
{
  "v": [
    { "p": "/message/status", "o": "replace", "v": "finished_successfully" }
  ]
}
```

## 调试工具 (test 适配器)

test 适配器提供了开发辅助工具，帮助快速获取页面元素信息和录制用户操作。

### test/inspect - 元素探测

提取页面上的可交互元素（按钮、输入框、data-testid、ARIA role 等），帮助编写适配器时找到正确的选择器。

```bash
# 基本用法：prompt 中填写要探测的 URL
python3 skills/text-generate-api/scripts/generate_text.py \
  --model "test/inspect" \
  --prompt "https://www.doubao.com/chat" \
  --api-key "sk-didi-123"

# 探测 Claude 页面
python3 skills/text-generate-api/scripts/generate_text.py \
  --model "test/inspect" \
  --prompt "https://claude.ai/new" \
  --api-key "sk-didi-123"
```

输出包含：
- 按钮列表及选择器
- 输入框/文本域
- data-testid 元素
- ARIA role 元素
- 可点击元素（cursor:pointer）

### test/record - 行为录制

录制用户在页面上的操作（点击、输入、按键），自动生成 Playwright 代码。

```bash
# 基本用法：prompt 格式为 "URL [录制时长秒数]"
# 默认录制 30 秒，录制期间请在浏览器中操作
python3 skills/text-generate-api/scripts/generate_text.py \
  --model "test/record" \
  --prompt "https://www.doubao.com/chat 30" \
  --api-key "sk-didi-123"

# 录制 60 秒
python3 skills/text-generate-api/scripts/generate_text.py \
  --model "test/record" \
  --prompt "https://claude.ai/new 60" \
  --api-key "sk-didi-123"
```

输出包含：
- Playwright 代码片段（可直接用于适配器开发）
- 原始操作数据（JSON 格式）

**注意**：录制期间需要手动在浏览器中操作，工具会捕获点击、输入、Enter/Escape/Tab 按键等事件。

### 其他 test 工具

```bash
# Cloudflare Turnstile 验证测试
python3 skills/text-generate-api/scripts/generate_text.py --model "test/cloudflare-turnstile" --prompt "test" --api-key "sk-didi-123"

# 浏览器指纹检测
python3 skills/image-generate-api/scripts/generate_image.py --model "test/creepjs" --prompt "test" --api-key "sk-didi-123"

# IP 查询
python3 skills/text-generate-api/scripts/generate_text.py --model "test/ip" --prompt "test" --api-key "sk-didi-123"
```

---

## 调试技巧

### 启用 SSE 调试日志
在适配器中添加：

```javascript
// 保存原始 SSE 响应
const fs = await import('fs');
const debugFile = `/tmp/${adapter}_sse_debug_${Date.now()}.txt`;
fs.writeFileSync(debugFile, content);
logger.info('适配器', `SSE 调试数据已保存到: ${debugFile}`, meta);
```

然后从容器复制文件进行分析：
```bash
sg docker -c "docker cp webai-2api:/tmp/xxx_sse_debug_xxx.txt /tmp/"
```

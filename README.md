
# AstrBot Plugin: Tool Enhancer

这是一个用于 AstrBot 的系统级插件，旨在**强制引导大模型主动调用已有 MCP (如 MiniMax) 或内置功能工具**。

由于大模型有时会倾向于使用内置知识甚至“编造”答案，而不去调用外部提供的高级工具（如联网搜索、图像识别）。本插件通过在系统底层监听你的对话，自动为那些带有查询、识图意图的问题注入**最高级别的系统提示词**，逼迫大模型在回答前必须调用工具。

## 核心功能

- **意图拦截**：自动识别 `["查", "搜", "最新", "新闻", "多少", "是谁", "吗", "为什么", "怎么看"]` 等搜索词。
- **图片拦截**：自动识别用户发送的图片请求 `["图片", "图里", "截图", "帮我看", "识别"]`。
- **系统级指令注入**：被触发时，会在大模型的 `ProviderRequest.system_prompt` 末尾加上一段严厉的警告，令其必须调用工具。
- **配置化**：可在 `_conf_schema.json` 或后台设置中自定义这段“严厉的警告”。

## 插件解构 (架构对齐)

基于标准的 AstrBot 插件规范：
```text
astrbot_plugin_tool_enhancer/
├── main.py              # 核心代码，利用 on_llm_request 钩子修改 prompt
├── metadata.yaml        # 插件静态元数据
├── README.md            # 说明文档
└── _conf_schema.json    # 供用户在可视化后台修改的自定配置项
```

## 安装与依赖

不需要额外的 `requirements.txt`。完全依赖纯净的 AstrBot 原生环境。

```bash
# 将整个文件夹丢进 plugins 目录，重启生效即可
# 如果你已经按指导安装，无需其他任何操作。
```

## 配置说明

你可以在 AstrBot 后台或者直接修改 `data/plugins/astrbot_plugin_tool_enhancer/_conf_schema.json`，来自定义你的“增强系统提示词”：

- `enhancer_prompt`: 当触发增强时，追加到大模型系统提示词末尾的具体文字内容。

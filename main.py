import re
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.provider import ProviderRequest
from astrbot.api.all import command

@register("astrbot_plugin_tool_enhancer", "大模型工具调用增强器", "强制/优化大模型调用内置和外置 MCP 工具的系统级插件。", "1.0.0")
class ToolEnhancerPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.context = context
        
        # 默认系统提示词
        self.enhancer_prompt = (
            "【系统最高级优先级指令】\n"
            "你当前已被挂载了多种高级 MCP 服务器工具（例如联网搜索、MiniMax Web Search、视觉分析工具等）。\n"
            "你在遇到不知道的知识、询问近期事实、或需要识别图片时形况，绝对禁止瞎编。\n"
            "必须在作答前，主动调用你身上的网络搜索或视觉分析相关的 Function Call 工具获取实时资料。否则将受到严厉惩罚！"
        )
        
        # 如果存在用户配置（来自 _conf_schema.json），则覆盖默认值
        if config and "enhancer_prompt" in config:
            user_prompt = config.get("enhancer_prompt", "").strip()
            if user_prompt:
                self.enhancer_prompt = user_prompt

    @filter.on_llm_request()
    async def on_request(self, event: AstrMessageEvent, req: ProviderRequest):
        """
        拦截每一次发给 LLM 的请求。
        通过修改系统提示词 (System Prompt)，增强大模型调用外部挂载的 MCP (如 minimax web search / vision ) 和 内置工具的意愿。
        这样大模型就能“自己判定意图”，但我们会给它加以严厉的指令束缚，防止它装死。
        """
        user_prompt = req.prompt or ""
        
        # 定义一些常见的需要搜索或识图的关键词启发式
        search_keywords = ["查", "搜", "最新", "新闻", "多少", "是谁", "吗", "为什么", "怎么看"]
        vision_keywords = ["图片", "图里", "截图", "帮我看", "识别"]
        
        needs_tool_hint = False
        
        # 如果用户上传了图片，大模型有时也会装瞎
        if hasattr(req, "image_urls") and req.image_urls:
            needs_tool_hint = True
            
        # 简单正则或关键词匹配，判断用户是否有求助意图
        if any(kw in user_prompt for kw in search_keywords + vision_keywords):
            needs_tool_hint = True
            
        # 如果用户明确带有诸如 "/search" 或 "#搜" 之类的强指令，也算
        if user_prompt.startswith("/search") or user_prompt.startswith("强制搜索"):
            needs_tool_hint = True
            # 如果是明示命令，我们可以把前缀去掉，让他更自然地转交给工具
            req.prompt = re.sub(r"^(?:/search|强制搜索)\s*", "", req.prompt).strip()

        if needs_tool_hint:
            # 动态注入最高优先级的系统级指令（支持用户后台自定义配置）
            req.system_prompt += "\n\n" + self.enhancer_prompt



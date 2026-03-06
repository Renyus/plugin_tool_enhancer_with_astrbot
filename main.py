from astrbot.api.all import *
from astrbot.api.event import filter
from astrbot.api.provider import ProviderRequest
import re

@register("astrbot_plugin_tool_enhancer", "大模型工具调用增强器", "强制/优化大模型调用内置和外置 MCP 工具的系统级插件。", "1.0.0")
class ToolEnhancerPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.context = context
        
        # 默认系统提示词，用于强制引导大模型使用工具
        self.default_enhancer_prompt = (
            "【系统最高级优先级指令】\n"
            "你当前已被挂载了多种高级 MCP 服务器工具（例如联网搜索、MiniMax Web Search、视觉分析工具等）。\n"
            "在遇到不确定的知识、查询近期事实、或需要识别图片时，你必须优先并主动通过已有的工具（Function Call）获取真实信息。\n"
            "绝对禁止在未尝试调用工具的情况下直接凭空编造事实，否则将被视为服务故障。"
        )
        
        # 加载用户配置
        self.enhancer_prompt = self.default_enhancer_prompt
        if config and "enhancer_prompt" in config:
            user_val = config.get("enhancer_prompt", "").strip()
            if user_val:
                self.enhancer_prompt = user_val

    @filter.on_llm_request()
    async def on_request(self, event: AstrMessageEvent, req: ProviderRequest):
        """
        在 LLM 请求发送前注入增强指令。
        该方法运行在异步事件循环中，内部处理逻辑均为纯内存运算（字符串/正则），确保不阻塞主进程。
        """
        user_prompt = req.prompt or ""
        
        # 关键词列表
        search_keywords = ["查", "搜", "最新", "新闻", "多少", "是谁", "为什么", "怎么看"]
        vision_keywords = ["图片", "图里", "截图", "帮我看", "识别"]
        
        should_enhance = False
        reason = ""
        
        # 1. 检测是否有图片附件
        if hasattr(req, "image_urls") and req.image_urls:
            should_enhance = True
            reason = f"检测到用户上传了 {len(req.image_urls)} 张图片。"
            
        # 2. 检测关键词
        if not should_enhance:
            matched_keywords = [kw for kw in search_keywords + vision_keywords if kw in user_prompt]
            if matched_keywords:
                should_enhance = True
                reason = f"匹配到意图关键词: {matched_keywords}"
            
        # 3. 检测特殊命令语法
        if not should_enhance:
            if user_prompt.startswith("/") or user_prompt.startswith("#") or "强制搜索" in user_prompt:
                should_enhance = True
                reason = "检测到用户强制操作意图。"
                # 清洗 prompt
                req.prompt = re.sub(r"^(?:/search|强制搜索|#搜)\s*", "", user_prompt).strip()

        # 执行增强
        if should_enhance:
            logger.info(f"[ToolEnhancer] 正在增强 LLM 请求。原因: {reason}")
            # 将增强指令追加到系统提示词末尾，确保其优先级最高
            req.system_prompt += f"\n\n{self.enhancer_prompt}"
        else:
            logger.debug(f"[ToolEnhancer] 回话跳过增强，用户输入: {user_prompt[:20]}...")




import json
from functools import lru_cache
import importlib.util

from loguru import logger

FEISHU_AVAILABLE = importlib.util.find_spec("lark_oapi") is not None

if FEISHU_AVAILABLE:
    import lark_oapi as lark
else:
    lark = None

def _get_bot_info(client: "lark.Client") -> dict:
    """Get the current bot info from Feishu API."""
    if not lark:
        raise RuntimeError("lark_oapi is not installed")

    request: lark.BaseRequest = (
        lark.BaseRequest.builder()
        .http_method(lark.HttpMethod.GET)
        .uri("/open-apis/bot/v3/info")
        .token_types({lark.AccessTokenType.APP})
        .build()
    )
    
    response: lark.BaseResponse = client.request(request)
    
    if not response.success():
        logger.error(
            f"client.request failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}"
        )
        return dict()
        
    return json.loads(response.raw.content)


@lru_cache(maxsize=10)
def get_bot_open_id(client: "lark.Client") -> str:
    """Get the bot's open_id, cached."""
    bot_info = _get_bot_info(client)
    
    if not bot_info.get("bot"):
        logger.warn("get bot open id from failed")
        return ""
        
    if not bot_info["bot"].get("open_id"):
        logger.warn("not found open id in bot info")
        return ""
        
    return bot_info["bot"]["open_id"]

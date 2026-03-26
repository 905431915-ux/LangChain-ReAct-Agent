import os
from utils.logger_handler import logger
from langchain_core.tools import tool
from rag.rag_service import RagSummarizeService
import random
from utils.config_handler import agent_conf
from utils.path_tool import get_abs_path
from .amap_service import amap_service
from .cache_manager import weather_cache, location_cache

rag = RagSummarizeService()

user_ids = ["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010", ]
month_arr = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06",
             "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12", ]

external_data = {}


@tool(description="从向量存储中检索参考资料")
def rag_summarize(query: str) -> str:
    return rag.rag_summarize(query)


@tool(description="获取指定城市的实时天气信息，包含气温、湿度、风力等详细数据")
def get_weather(city: str) -> str:
    # 检查缓存
    cache_key = f"weather:{city}"
    cached_result = weather_cache.get(cache_key)
    if cached_result:
        logger.info(f"[get_weather] 使用缓存数据：{city}")
        return cached_result

    logger.info(f"[get_weather] 正在查询{city}的天气")

    weather_info = amap_service.get_weather(city)

    if weather_info:
        report = amap_service.format_weather_report(weather_info)
        logger.info(f"[get_weather] {city}天气查询成功")

        weather_cache.set(cache_key, report)
        return report
    else:
        logger.warning(f"[get_weather] {city}天气查询失败")
        return f"暂时无法获取{city}的天气信息，请稍后再试"


@tool(description="通过定位服务获取用户当前所在城市的名称")
def get_user_location() -> str:
    cached_location = location_cache.get("user_location")
    if cached_location:
        logger.info(f"[get_user_location] 使用缓存位置：{cached_location}")
        return cached_location

    location = amap_service.get_user_location_by_ip()

    if not location:
        location = "北京市"
        logger.info(f"[get_user_location] IP 定位失败，使用默认位置：{location}")
    else:
        logger.info(f"[get_user_location] IP 定位成功：{location}")

    location_cache.set("user_location", location)
    return location


@tool(description="获取用户的 ID，以纯字符串形式返回")
def get_user_id() -> str:
    return random.choice(user_ids)


@tool(description="获取当前月份，以纯字符串形式返回")
def get_current_month() -> str:
    return random.choice(month_arr)


def generate_external_data():
    if not external_data:
        external_data_path = get_abs_path(agent_conf["external_data_path"])

        if not os.path.exists(external_data_path):
            raise FileNotFoundError(f"外部数据文件{external_data_path}不存在")

        with open(external_data_path, "r", encoding="utf-8") as f:
            for line in f.readlines()[1:]:
                arr: list[str] = line.strip().split(",")

                user_id: str = arr[0].replace('"', "")
                feature: str = arr[1].replace('"', "")
                efficiency: str = arr[2].replace('"', "")
                consumables: str = arr[3].replace('"', "")
                comparison: str = arr[4].replace('"', "")
                time: str = arr[5].replace('"', "")

                if user_id not in external_data:
                    external_data[user_id] = {}

                external_data[user_id][time] = {
                    "特征": feature,
                    "效率": efficiency,
                    "耗材": consumables,
                    "对比": comparison,
                }


@tool(description="从外部系统中获取指定用户在指定月份的使用记录，以纯字符串形式返回，如果未检索到返回空字符串")
def fetch_external_data(user_id: str, month: str) -> str:
    generate_external_data()

    try:
        return external_data[user_id][month]
    except KeyError:
        logger.warning(f"[fetch_external_data]未能检索到用户：{user_id}在{month}的使用记录数据")
        return ""


@tool(
    description="无入参，无返回值，调用后触发中间件自动为报告生成的场景动态注入上下文信息，为后续提示词切换提供上下文信息")
def fill_context_for_report():
    return "fill_context_for_report 已调用"



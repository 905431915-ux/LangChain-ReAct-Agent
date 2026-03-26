import os
import requests
from utils.logger_handler import logger


class AMapService:
    """高德地图 API 服务类"""

    def __init__(self):
        self.weather_key = os.getenv("AMAP_WEATHER_KEY")
        self.geo_key = os.getenv("AMAP_GEO_KEY")
        self.ip_location_key = os.getenv("AMAP_IP_LOCATION_KEY")
        self.weather_url = "https://restapi.amap.com/v3/weather/weatherInfo"
        self.geo_url = "https://restapi.amap.com/v3/geocode/geo"
        self.ip_location_url = "https://restapi.amap.com/v3/ip"

    def get_user_location_by_ip(self) -> str:
        """
        通过 IP 定位获取用户当前所在城市
        :return: 城市名称，失败返回空字符串
        """
        try:
            params = {
                'key': self.ip_location_key,
                'type': 4
            }

            response = requests.get(self.ip_location_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == '1':
                adcode = data.get('adcode', '')
                province = data.get('province', '')
                city = data.get('city', '')
                district = data.get('district', '')

                logger.info(f"[AMap IP 定位] 定位结果：{province}{city}{district} (adcode: {adcode})")

                if city:
                    return city
                elif province:
                    return province
                elif district:
                    return district

            logger.warning(f"[AMap IP 定位] 定位失败，API 返回：{data}")
            return ""

        except Exception as e:
            logger.error(f"[AMap IP 定位] 获取位置失败：{str(e)}")
            return ""

    def get_city_adcode(self, city_name: str) -> str:
        """
        根据城市名获取行政区划代码
        :param city_name: 城市名称
        :return: 城市 adcode，失败返回空字符串
        """
        try:
            params = {
                'address': city_name,
                'key': self.geo_key,
                'output': 'json'
            }

            response = requests.get(self.geo_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == '1' and data.get('geocodes'):
                adcode = data['geocodes'][0]['adcode']
                logger.info(f"[AMap] 城市{city_name}的 adcode 为：{adcode}")
                return adcode

            logger.warning(f"[AMap] 未找到城市{city_name}的行政区划代码")
            return ""

        except Exception as e:
            logger.error(f"[AMap] 获取城市 adcode 失败：{str(e)}")
            return ""

    def get_weather(self, city: str) -> dict | None:
        """
        获取指定城市的实时天气信息
        :param city: 城市名称
        :return: 天气信息字典，失败返回 None
        """
        try:
            # 先获取城市 adcode
            adcode = self.get_city_adcode(city)
            if not adcode:
                return None

            # 获取实时天气（注意：用 base 不是 all）
            params = {
                'city': adcode,
                'key': self.weather_key,
                'extensions': 'base'  # 改成 base 获取实时天气
            }

            response = requests.get(self.weather_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            logger.info(f"[AMap] 实时天气 API 返回：{data}")

            # 实时天气在 lives 数组中
            if data.get('status') == '1' and data.get('lives'):
                live = data['lives'][0]
                weather_info = {
                    'city': live.get('city'),
                    'weather': live.get('weather'),
                    'temperature': live.get('temperature'),
                    'humidity': live.get('humidity'),
                    'winddirection': live.get('winddirection'),
                    'windpower': live.get('windpower'),
                    'report_time': live.get('reporttime')
                }

                logger.info(f"[AMap] 获取{city}实时天气成功：{weather_info}")
                return weather_info

            logger.warning(f"[AMap] 未获取到城市{city}的实时天气，API 返回：{data}")
            return None

        except Exception as e:
            logger.error(f"[AMap] 获取实时天气失败：{str(e)}")
            return None

    def format_weather_report(self, weather_info: dict) -> str:
        """
        格式化天气报告
        :param weather_info: 天气信息字典
        :return: 格式化的天气报告字符串
        """
        if not weather_info:
            return "暂时无法获取该城市的天气信息"

        wind_map = {
            '东': '东风', '南': '南风', '西': '西风', '北': '北风',
            '东南': '东南风', '东北': '东北风', '西南': '西南风', '西北': '西北风'
        }
        wind = wind_map.get(weather_info.get('winddirection', ''), '未知风向')

        report = (
            f"{weather_info['city']}当前天气：{weather_info['weather']}，"
            f"气温{weather_info['temperature']}°C，"
            f"空气湿度{weather_info['humidity']}%，"
            f"{wind}{weather_info['windpower']}级，"
            f"数据更新时间：{weather_info['report_time']}"
        )

        return report


amap_service = AMapService()

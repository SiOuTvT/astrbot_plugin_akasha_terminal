import json
import random
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from zoneinfo import ZoneInfo

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.star import StarTools
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

from ..utils.text_formatter import TextFormatter
from ..utils.utils import (
    get_at_ids,
    read_json,
    read_json_sync,
    write_json,
    write_json_sync,
)
from .task import Task


class Synthesis:
    def __init__(self):
        """初始化合成系统，设置数据目录和文件路径"""
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.data_dir = BASE_DIR / "data"
        self.synthesis_recipes_path = self.data_dir / "synthesis_recipes.json"
        self.user_workshop_path = (
            BASE_DIR.parent.parent
            / "plugin_data"
            / "astrbot_plugin_akasha_terminal"
            / "user_workshop"
        )
        self.user_inventory_path = (
            BASE_DIR.parent.parent
            / "plugin_data"
            / "astrbot_plugin_akasha_terminal"
            / "user_inventory"
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._init_synthesis_data()

        # 导入商店系统获取材料名称
        from .shop import Shop

        self.shop = Shop()  # 初始化商店系统

        # 导入用户系统获取金钱
        from .user import User

        self.user = User()

        # 导入任务系统更新任务进度
        self.task = Task()

    def _init_synthesis_data(self) -> None:
        """初始化默认合成数据（仅当文件不存在时）"""
        # 设置「中国标准时间」
        self.CN_TIMEZONE = ZoneInfo("Asia/Shanghai")
        # 初始化合成配方数据
        synthesis_default_data = read_json_sync(self.synthesis_recipes_path, {})
        self.default_recipes = {
            "recipes": {
                "超级幸运符": {
                    "id": "super_luck_charm",
                    "materials": {"2": 3, "5": 1},
                    "result_id": "101",
                    "success_rate": 80,
                    "workshop_level": 2,
                    "description": "提供30%成功率加成,持续5次使用",
                    "category": "增益道具",
                },
                "爱情药水": {
                    "id": "love_potion",
                    "materials": {"1": 2, "4": 1},
                    "result_id": "102",
                    "success_rate": 90,
                    "workshop_level": 1,
                    "description": "约会时额外获得50%好感度",
                    "category": "恋爱道具",
                },
                "黄金锤子": {
                    "id": "golden_hammer",
                    "materials": {"3": 5, "5": 2},
                    "result_id": "103",
                    "success_rate": 60,
                    "workshop_level": 3,
                    "description": "打工收入翻倍,持续7天",
                    "category": "经济道具",
                },
                "时间沙漏": {
                    "id": "time_hourglass",
                    "materials": {"2": 2, "4": 3},
                    "result_id": "104",
                    "success_rate": 70,
                    "workshop_level": 2,
                    "description": "重置所有冷却时间",
                    "category": "功能道具",
                },
                "钻石戒指": {
                    "id": "diamond_ring",
                    "materials": {"5": 3, "1": 5},
                    "result_id": "105",
                    "success_rate": 50,
                    "workshop_level": 4,
                    "description": "求婚成功率100%,获得专属称号",
                    "category": "特殊道具",
                },
                "万能钥匙": {
                    "id": "master_key",
                    "materials": {"3": 3, "2": 3},
                    "result_id": "106",
                    "success_rate": 65,
                    "workshop_level": 3,
                    "description": "解锁所有限制,跳过冷却",
                    "category": "功能道具",
                },
                "复活石": {
                    "id": "revival_stone",
                    "materials": {"5": 5, "4": 5},
                    "result_id": "107",
                    "success_rate": 40,
                    "workshop_level": 5,
                    "description": "死亡时自动复活,保留所有财产",
                    "category": "保护道具",
                },
                "财富符咒": {
                    "id": "wealth_talisman",
                    "materials": {"3": 4, "1": 3},
                    "result_id": "108",
                    "success_rate": 75,
                    "workshop_level": 2,
                    "description": "所有金币获得翻倍,持续3天",
                    "category": "经济道具",
                },
                "传送卷轴": {
                    "id": "teleport_scroll",
                    "materials": {"2": 4, "5": 1},
                    "result_id": "109",
                    "success_rate": 85,
                    "workshop_level": 1,
                    "description": "瞬间传送到任意地点",
                    "category": "功能道具",
                },
                "神级合成石": {
                    "id": "divine_synthesis_stone",
                    "materials": {"101": 1, "103": 1, "105": 1},
                    "result_id": "110",
                    "success_rate": 30,
                    "workshop_level": 6,
                    "description": "终极道具,拥有所有效果的组合",
                    "category": "传说道具",
                },
            },
            "items": {
                "101": {"name": "超级幸运符", "rarity": "稀有", "value": 2000},
                "102": {"name": "爱情药水", "rarity": "普通", "value": 800},
                "103": {"name": "黄金锤子", "rarity": "史诗", "value": 5000},
                "104": {"name": "时间沙漏", "rarity": "稀有", "value": 1500},
                "105": {"name": "钻石戒指", "rarity": "传说", "value": 8000},
                "106": {"name": "万能钥匙", "rarity": "史诗", "value": 3000},
                "107": {"name": "复活石", "rarity": "传说", "value": 10000},
                "108": {"name": "财富符咒", "rarity": "稀有", "value": 2500},
                "109": {"name": "传送卷轴", "rarity": "普通", "value": 600},
                "110": {"name": "神级合成石", "rarity": "神话", "value": 50000},
            },
            "decompose": {
                "101": {"materials": {"2": 2, "5": 1}, "success_rate": 60},
                "102": {"materials": {"1": 1, "4": 1}, "success_rate": 80},
                "103": {"materials": {"3": 3, "5": 1}, "success_rate": 40},
                "104": {"materials": {"2": 1, "4": 2}, "success_rate": 70},
                "105": {"materials": {"5": 2, "1": 3}, "success_rate": 30},
            },
        }
        # 如果文件不存在或数据为空，写入默认数据
        if not self.synthesis_recipes_path.exists() or not synthesis_default_data.get(
            "recipes"
        ):
            write_json_sync(self.synthesis_recipes_path, self.default_recipes)

        # 初始化用户工坊路径，储存每个用户的工坊数据
        if not self.user_workshop_path.exists():
            self.user_workshop_path.mkdir(parents=True, exist_ok=True)

    async def get_synthesis_data(self) -> Dict[str, Any]:
        """获取合成系统数据，自动处理数据异常"""
        synthesis_data = await read_json(self.synthesis_recipes_path, {})

        # 检查数据是否正常
        if not synthesis_data or "recipes" not in synthesis_data:
            logger.warning("[合成系统] 配方数据异常，尝试初始化默认数据")
            self._init_synthesis_data()  # 重新初始化数据
            synthesis_data = await read_json(self.synthesis_recipes_path, {})

        # 再次检查
        if not synthesis_data or "recipes" not in synthesis_data:
            raise Exception("合成配方数据异常，无法初始化")

        return synthesis_data

    async def get_synthesis_recipes(self) -> Dict[str, Any]:
        """获取合成配方列表"""
        synthesis_data = await self.get_synthesis_data()
        return synthesis_data["recipes"]  # 只返回配方部分

    async def get_synthesis_items(self) -> Dict[str, Any]:
        """获取合成物品信息"""
        synthesis_data = await self.get_synthesis_data()
        return synthesis_data["items"]  # 只返回物品信息部分

    async def show_composite_list(self, event: AiocqhttpMessageEvent) -> str:
        """显示合成列表"""
        try:
            user_id = str(event.user_id)
            group_id = (
                str(event.group_id)
                if hasattr(event, "group_id") and event.group_id
                else ""
            )

            # 收集所有需要的数据
            recipes = await self.get_synthesis_recipes()  # 配方数据
            items_info = await self.get_synthesis_items()  # 合成物品信息
            workshop = await self.get_user_workshop(user_id, group_id)  # 用户工坊状态
            inventory = await self.get_user_inventory(user_id, group_id)  # 用户材料
            shop_data = await self.shop.get_shop_items()  # 商店材料名称

            # 添加缺失的分类处理逻辑
            categories = {}
            for name, recipe in recipes.items():
                category = recipe.get("category", "其他")
                if category not in categories:
                    categories[category] = []
                categories[category].append({"name": name, **recipe})

            # 调用_build_template_data方法
            template_data = self._build_template_data(
                username=event.sender.nickname,
                workshop=workshop,
                categories=categories,
                shop_data=shop_data,
                inventory=inventory,
                items_info=items_info,
            )

            # 这里应该调用图片渲染或消息格式化
            return await self._format_composite_list_message(
                template_data
            )  # 修改调用方式

        except Exception as e:
            logger.error(f"显示合成列表失败: {str(e)}")
            return "❌ 获取合成列表失败"  # 返回字符串,不是字典

    async def _format_composite_list_message(self, template_data: Dict) -> str:
        """格式化合成列表消息"""
        # 这里实现您的消息格式化逻辑
        # 可能是生成图片或文本消息
        return "合成列表功能"

    def _build_template_data(
        self,
        username: str,
        workshop: Dict,
        categories: Dict,
        shop_data: Dict,
        inventory: Dict,
        items_info: Dict,
    ) -> Dict[str, Any]:
        """构建模板数据（用于图片生成）"""
        workshop_level = workshop.get("level", 1)
        workshop_exp = workshop.get("exp", 0)

        template_data = {
            "username": username,
            "workshopLevel": workshop_level,
            "workshopExp": workshop_exp,
            "expToNext": workshop_level * 100,
            "successBonus": min(20, (workshop_level - 1) * 5),
            "recipes": [],
        }

        # 处理分类配方
        for category, items in categories.items():
            category_data = {
                "category": category,
                "categoryName": category,
                "items": [],
            }

            for item in items:
                # 处理材料显示
                materials = []
                if item.get("materials") and isinstance(item["materials"], dict):
                    for item_id, count in item["materials"].items():
                        material_name = (
                            shop_data.get("items", {}).get(item_id, {}).get("name")
                            or f"道具{item_id}"
                        )
                        materials.append(f"{material_name}x{count}")

                # 先计算稀有度和成功率
                rarity = items_info.get(item["result_id"], {}).get("rarity", "普通")
                rarity_emoji = self.get_rarity_emoji(rarity)
                level_bonus = min(
                    20, (workshop_level - item.get("workshop_level", 1)) * 5
                )
                final_success_rate = min(95, item.get("success_rate", 50) + level_bonus)

                # 然后一次性构建完整的数据对象
                category_data["items"].append(
                    {
                        "name": item.get("name", "未知道具"),
                        "rarityIcon": rarity_emoji,
                        "materialsText": ", ".join(materials),
                        "successRate": item.get("success_rate", 50),
                        "finalSuccessRate": final_success_rate,
                        "workshopLevel": item.get("workshop_level", 1),
                        "description": item.get("description", "暂无描述"),
                        "canCraft": workshop_level >= item.get("workshop_level", 1),
                    }
                )

            template_data["recipes"].append(category_data)

        template_data["inventory"] = [
            {
                "name": (
                    shop_data.get("items", {}).get(item_id, {}).get("name")
                    or items_info.get(item_id, {}).get("name")  # 使用items_info
                    or f"道具{item_id}"
                ),
                "amount": count,
                "rarityIcon": self.get_rarity_emoji(
                    shop_data.get("items", {}).get(item_id, {}).get("rarity")
                    or items_info.get(item_id, {}).get("rarity")  # 使用items_info
                    or "普通"
                ),
            }
            for item_id, count in inventory.items()
        ]

        template_data["materialSlots"] = [None, None, None, None]  # 4个材料槽位

        # 计算统计信息
        total_crafts = workshop.get("synthesis_count", 0)
        successful_crafts = workshop.get("success_count", 0)
        success_rate = (
            round((successful_crafts / total_crafts * 100)) if total_crafts > 0 else 0
        )

        template_data["stats"] = {
            "totalCrafts": total_crafts,
            "successfulCrafts": successful_crafts,
            "successRate": success_rate,
        }

        return template_data

    def get_rarity_emoji(self, rarity: str) -> str:
        """获取稀有度图标"""
        emoji_map = {
            "普通": "⚪",
            "稀有": "🔵",
            "史诗": "🟣",
            "传说": "🟠",
            "神话": "🔴",
        }
        return emoji_map.get(rarity, "⚪")

    async def get_user_workshop(
        self, user_id: str, group_id: str = ""
    ) -> Dict[str, Any]:
        """获取用户工坊数据"""
        user_data = await self.user.get_user_data(user_id, group_id)
        return user_data.get(
            "workshop",
            {
                "level": 1,  # 默认1级
                "exp": 0,  # 默认0经验
                "synthesis_count": 0,  # 默认合成次数
                "success_count": 0,  # 默认成功次数
            },
        )

    async def get_user_inventory(
        self, user_id: str, group_id: str = ""
    ) -> Dict[str, int]:
        """获取用户背包 返回格式：{"道具ID": 数量, ...}"""
        user_data = await self.user.get_user_data(user_id, group_id)
        return user_data.get("inventory", {})

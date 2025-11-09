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
        PLUGIN_DATA_DIR = Path(StarTools.get_data_dir("astrbot_plugin_akasha_terminal"))
        self.data_dir = Path(__file__).resolve().parent.parent / "data"
        self.synthesis_recipes_path = self.data_dir / "synthesis_recipes.json"
        self.user_workshop_path = PLUGIN_DATA_DIR / "user_workshop"
        self.user_inventory_path = PLUGIN_DATA_DIR / "user_inventory"
        self.config_path = (
            PLUGIN_DATA_DIR.parent.parent
            / "config"
            / "astrbot_plugin_akasha_terminal_config.json"
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

    async def show_composite_list(
        self, event: AiocqhttpMessageEvent, *args, **kwargs
    ) -> str:
        """显示合成列表"""
        try:
            user_id = str(event.user_id)
            group_id = (
                str(event.group_id)
                if hasattr(event, "group_id") and event.group_id
                else ""
            )

            # 加载数据
            recipes_data = await read_json(self.synthesis_recipes_path, {})
            shop_data = await self.shop.get_shop_items()
            workshop = await self.get_user_workshop_direct(
                user_id, group_id
            )  # 读取工坊数据
            inventory = await self.get_user_inventory_direct(
                user_id, group_id
            )  # 读取背包数据

            # 检查确保数据存在
            if (
                not recipes_data
                or not recipes_data.get("recipes")
                or not isinstance(recipes_data.get("recipes"), dict)
            ):
                logger.warning("[合成系统] 配方数据异常，尝试初始化默认数据")
                self._init_synthesis_data()  # 重新初始化数据
                recipes_data = await read_json(self.synthesis_recipes_path, {})

                # 再次检查，如果还是有问题则报错
                if (
                    not recipes_data
                    or not recipes_data.get("recipes")
                    or not isinstance(recipes_data.get("recipes"), dict)
                ):
                    return "❌ 合成配方数据异常，请联系管理员检查数据文件"

            recipes = recipes_data.get("recipes", {})
            items_info = recipes_data.get("items", {})

            # 分类处理逻辑
            categories = {}
            for name, recipe in recipes.items():
                category = recipe.get("category", "其他")
                if category not in categories:
                    categories[category] = []
                categories[category].append({"name": name, **recipe})

            # 构建模板数据
            template_data = {
                "username": getattr(event.sender, "card", None)
                or getattr(event.sender, "nickname", None)
                or "未知用户",
                "workshopLevel": workshop.get("level", 1),
                "workshopExp": workshop.get("exp", 0),
                "expToNext": (workshop.get("level", 1)) * 100,
                "successBonus": min(20, ((workshop.get("level", 1)) - 1) * 5),
                "recipes": [
                    {
                        "category": category,
                        "categoryName": category,
                        "items": [
                            {
                                "name": item.get("name", "未知道具"),
                                "rarityIcon": self.get_rarity_emoji(
                                    items_info.get(item.get("result_id", ""), {}).get(
                                        "rarity", "普通"
                                    )
                                ),
                                "materialsText": ", ".join(
                                    [
                                        f"{shop_data.get('items', {}).get(item_id, {}).get('name', f'道具{item_id}')}×{count}"
                                        for item_id, count in (
                                            item.get("materials", {}) or {}
                                        ).items()
                                        if item.get("materials")
                                        and isinstance(item.get("materials"), dict)
                                    ]
                                ),
                                "successRate": item.get("success_rate", 50),
                                "finalSuccessRate": min(
                                    95,
                                    (item.get("success_rate", 50))
                                    + min(
                                        20,
                                        (
                                            (workshop.get("level", 1))
                                            - (item.get("workshop_level", 1))
                                        )
                                        * 5,
                                    ),
                                ),
                                "workshopLevel": item.get("workshop_level", 1),
                                "description": item.get("description", "暂无描述"),
                                "canCraft": (workshop.get("level", 1))
                                >= (item.get("workshop_level", 1)),
                            }
                            for item in items
                        ],
                    }
                    for category, items in categories.items()
                ],
                "inventory": [
                    {
                        "name": (
                            shop_data.get("items", {}).get(item_id, {}).get("name")
                            or items_info.get(item_id, {}).get("name")
                            or f"道具{item_id}"
                        ),
                        "amount": count,
                        "rarityIcon": self.get_rarity_emoji(
                            shop_data.get("items", {}).get(item_id, {}).get("rarity")
                            or items_info.get(item_id, {}).get("rarity")
                            or "普通"
                        ),
                    }
                    for item_id, count in (inventory or {}).items()
                ],
                "materialSlots": [None, None, None, None],
                "stats": {
                    "totalCrafts": workshop.get("synthesis_count", 0),
                    "successfulCrafts": workshop.get("success_count", 0),
                    "successRate": round(
                        (
                            workshop.get("success_count", 0)
                            / (workshop.get("synthesis_count", 1))
                            * 100
                        )
                        if workshop.get("synthesis_count", 0) > 0
                        else 0
                    ),
                },
            }

            # 格式化消息 暂时返回文本消息，后期改为图片渲染👀(待实现)
            return await self._format_composite_list_message(template_data)

        except Exception as e:
            logger.error(f"显示合成列表失败: {str(e)}")
            return "❌ 获取合成列表失败"

    async def get_user_workshop_direct(
        self, user_id: str, group_id: str = ""
    ) -> Dict[str, Any]:
        """直接读取用户工坊数据"""
        if group_id:
            workshop_file = self.user_workshop_path / f"{user_id}_{group_id}.json"
        else:
            workshop_file = self.user_workshop_path / f"{user_id}.json"

        workshop_data = await read_json(workshop_file, {})
        return workshop_data or {
            "level": 1,
            "exp": 0,
            "synthesis_count": 0,
            "success_count": 0,
        }

    async def get_user_inventory_direct(
        self, user_id: str, group_id: str = ""
    ) -> Dict[str, int]:
        """直接读取用户背包数据"""
        if group_id:
            inventory_file = self.user_inventory_path / f"{user_id}_{group_id}.json"
        else:
            inventory_file = self.user_inventory_path / f"{user_id}.json"

        inventory = await read_json(inventory_file, {})
        return inventory or {}

    async def _format_composite_list_message(self, template_data: Dict) -> str:
        """格式化合成列表消息"""
        try:
            message = f"🔧 合成工坊 - {template_data['username']}\n"
            message += f"📊 工坊等级: Lv{template_data['workshopLevel']} | 经验: {template_data['workshopExp']}/{template_data['expToNext']}\n"
            message += f"🎯 成功率加成: +{template_data['successBonus']}%\n"
            message += f"📈 合成统计: {template_data['stats']['successRate']}% ({template_data['stats']['successfulCrafts']}/{template_data['stats']['totalCrafts']})\n\n"

            # 显示配方
            for category in template_data["recipes"]:
                message += f"📁 {category['categoryName']}:\n"
                for item in category["items"]:
                    status = "✅" if item["canCraft"] else "🔒"
                    message += f"  {status} {item['rarityIcon']} {item['name']}\n"
                    message += f"     成功率: {item['finalSuccessRate']}% | 需要等级: Lv{item['workshopLevel']}\n"
                    message += f"     材料: {item['materialsText']}\n"
                    message += f"     描述: {item['description']}\n\n"

            # 显示背包
            if template_data["inventory"]:
                message += "🎒 背包材料:\n"
                for item in template_data["inventory"]:
                    message += (
                        f"  {item['rarityIcon']} {item['name']} ×{item['amount']}\n"
                    )

            return message

        except Exception as e:
            logger.error(f"格式化合成列表消息失败: {str(e)}")
            return "🔧 合成工坊\n📊 欢迎来到合成工坊！"

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

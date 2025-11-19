import json
import math
import random
import time
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
        self.shop_data_path = self.data_dir / "shop_data.json"
        self.user_workshop_path = PLUGIN_DATA_DIR / "user_workshop"
        self.user_inventory_path = PLUGIN_DATA_DIR / "user_inventory"
        # 内存缓存（用于 Redis 不可用时的冷却等短期存储）
        self.memory_cache = {}
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
        # 初始化用户库存路径
        if not self.user_inventory_path.exists():
            self.user_inventory_path.mkdir(parents=True, exist_ok=True)

    async def get_synthesis_recipes(self) -> Dict[str, Any]:
        """获取所有合成配方"""
        recipes = await self.load_json_data(self.synthesis_recipes_path, {})
        return recipes

    async def get_shop_data(self) -> Dict[str, Any]:
        """获取商店数据"""
        shop_data = await self.load_json_data(self.shop_data_path, {})
        return shop_data

    async def get_user_workshop(self, user_id: str, group_id: str) -> Dict[str, Any]:
        """获取用户工坊数据"""
        file_path = self.user_workshop_path / f"{user_id}_{group_id}.json"
        workshop = await self.load_json_data(file_path, {})
        return workshop

    async def get_user_inventory(self, user_id: str, group_id: str) -> Dict[str, int]:
        """获取用户库存数据"""
        file_path = self.user_inventory_path / f"{user_id}_{group_id}.json"
        inventory = await self.load_json_data(file_path, {})
        return inventory

    async def get_recipe_detail(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """获取指定配方的详细信息"""
        recipes = await self.get_synthesis_recipes()
        return recipes.get(recipe_id)

    async def get_user_backpack(self, user_id: str, group_id: str) -> Dict[str, int]:
        """获取用户背包物品列表"""
        return await self.get_user_inventory(user_id, group_id)

    async def handle_synthesis_command(
        self, event: AiocqhttpMessageEvent, parts: list[str]
    ) -> Tuple[bool, str]:
        """
        处理合成命令
        :param event: 消息事件对象
        :param parts: 命令参数列表
        :return: (是否成功, 结果消息)
        """
        try:
            user_id = (
                str(event.get_sender_id())
                if hasattr(event, "user_id")
                else str(event.user_id())
            )
            group_id = (
                str(event.get_group_id())
                if hasattr(event, "group_id") and event.group_id
                else "private"
            )
            if not parts:
                return (
                    False,
                    "请指定要合成的道具名称，使用方法: /虚空合成 道具名称\n"
                    "示例: /虚空合成 超级幸运符",
                )
            item_name = parts[0]
            # 加载合成配方
            recipes = await self.get_synthesis_recipes()

            # 配方存在性校验
            recipe = recipes.get("recipes", {}).get(item_name)
            if not recipe:
                return (
                    False,
                    f"❌ 找不到 {item_name} 的合成配方！使用 #合成列表 查看所有配方",
                )

            # 获取用户数据
            workshop = await self.get_user_workshop(user_id, group_id)
            inventory = await self.get_user_inventory(user_id, group_id)

            # 检查工坊等级
            if workshop.get("level", 1) < recipe.get("workshop_level", 1):
                return (
                    False,
                    f"❌ 工坊等级不足！需要等级 {recipe.get('workshop_level', 1)}，当前等级 {workshop.get('level', 1)}",
                )

            # 检查材料
            materials = recipe.get("materials", {})
            if not materials or not isinstance(materials, dict):
                return (False, f"❌ 配方 {item_name} 的材料数据异常！")

            shop_data = await self.get_shop_data()
            missing_materials = []

            for item_id, need_count in materials.items():
                have_count = inventory.get(item_id, 0)
                if have_count < need_count:
                    item_display_name = (
                        shop_data.get("items", {})
                        .get(item_id, {})
                        .get("name", f"道具{item_id}")
                    )
                    missing_materials.append(
                        f"{item_display_name} (需要{need_count}个，拥有{have_count}个)"
                    )

            if missing_materials:
                message = "❌ 材料不足！\n缺少材料:\n" + "\n".join(
                    [f"• {m}" for m in missing_materials]
                )
                return False, message

            # 冷却时间检查
            cooldown_key = f"akasha:synthesis-cd:{group_id}:{user_id}"
            cooldown_result = await self.check_synthesis_cooldown(cooldown_key)
            if cooldown_result:
                return False, cooldown_result

            # 计算成功率并执行合成
            synthesis_result = await self.execute_synthesis(
                user_id, group_id, recipe, workshop, inventory, cooldown_key
            )

            if not synthesis_result["success"]:
                return False, f"❌ {synthesis_result['message']}"

            return True, synthesis_result["message"]

        except Exception as e:
            logger.error(f"合成道具失败: {str(e)}")
            return False, "合成道具失败，请稍后再试~"

    async def check_synthesis_cooldown(self, cooldown_key: str) -> Optional[str]:
        """检查合成冷却时间"""
        last_synthesis = -2

        if await self.is_redis_available():
            last_synthesis = await self.redis.ttl(cooldown_key)
        else:
            logger.info(
                f"[虚空终端] Redis不可用，使用内存缓存检查冷却时间: {cooldown_key}"
            )
            cached_time = self.memory_cache.get(cooldown_key)
            if cached_time:
                now = int(time.time())
                time_diff = now - cached_time
                last_synthesis = 300 - time_diff if time_diff < 300 else -2

        if last_synthesis != -2:
            wait_minutes = math.ceil(last_synthesis / 60)
            return f"合成冷却中，还需等待 {wait_minutes} 分钟"

        return None

    async def execute_synthesis(
        self,
        user_id: str,
        group_id: str,
        recipe: Dict[str, Any],
        workshop: Dict[str, Any],
        inventory: Dict[str, int],
        cooldown_key: str,
    ) -> Dict[str, Any]:
        """执行合成操作"""
        try:
            # 计算成功率
            level_bonus = min(
                20, (workshop.get("level", 1) - recipe.get("workshop_level", 1)) * 5
            )
            final_success_rate = min(95, recipe.get("success_rate", 50) + level_bonus)

            success = random.randint(1, 100) <= final_success_rate

            if success:
                # 扣除材料
                materials = recipe.get("materials", {})
                for item_id, need_count in materials.items():
                    await self.update_user_inventory(
                        user_id, group_id, item_id, -need_count
                    )

                # 添加产物
                result_id = recipe.get("result_id")
                if result_id:
                    await self.add_to_inventory(user_id, group_id, result_id, 1)

                # 更新工坊数据
                workshop["exp"] = workshop.get("exp", 0) + 10
                workshop["synthesis_count"] = workshop.get("synthesis_count", 0) + 1
                workshop["success_count"] = workshop.get("success_count", 0) + 1

                # 检查升级
                level_up_message = ""
                exp_needed = workshop.get("level", 1) * 100
                if workshop.get("exp", 0) >= exp_needed:
                    workshop["level"] = workshop.get("level", 1) + 1
                    workshop["exp"] = 0
                    level_up_message = f"🎉 工坊升级到 {workshop['level']} 级！"

                await self.save_user_workshop(user_id, group_id, workshop)

                # 注释了任务更新进度

                # 获取稀有度信息
                recipes_data = await self.get_synthesis_recipes()
                rarity = (
                    recipes_data.get("items", {})
                    .get(result_id, {})
                    .get("rarity", "普通")
                )
                rarity_emoji = await self.get_synthesis_rarity_emoji(rarity)

                # 设置冷却时间
                await self.set_synthesis_cooldown(cooldown_key)

                message = f"🎉 合成成功！获得了{rarity_emoji}【{result_id}】"
                if level_up_message:
                    message += f"\n{level_up_message}"

                return {"success": True, "message": message}

            else:
                # 合成失败逻辑
                workshop["synthesis_count"] = workshop.get("synthesis_count", 0) + 1
                await self.save_user_workshop(user_id, group_id, workshop)

                # 设置冷却时间
                await self.set_synthesis_cooldown(cooldown_key)

                return {
                    "success": False,
                    "message": "😔 合成失败！材料已消耗，请再接再厉",
                }

        except Exception as e:
            logger.error(f"执行合成失败: {e}")
            return {"success": False, "message": "合成过程出现异常"}

    # ------------------ 兼容封装与辅助方法 ------------------
    async def load_json_data(self, file_path: Path, default: dict) -> dict:
        """异步读取 JSON 数据，若不存在返回 default"""
        try:
            return await read_json(file_path) or default
        except Exception:
            return default

    async def save_user_workshop(self, user_id: str, group_id: str, data: dict) -> bool:
        file_path = self.user_workshop_path / f"{user_id}_{group_id}.json"
        try:
            await write_json(file_path, data)
            return True
        except Exception as e:
            logger.error(f"保存工坊数据失败: {e}")
            return False

    async def save_user_inventory(
        self, user_id: str, group_id: str, data: dict
    ) -> bool:
        file_path = self.user_inventory_path / f"{user_id}_{group_id}.json"
        try:
            await write_json(file_path, data)
            return True
        except Exception as e:
            logger.error(f"保存背包数据失败: {e}")
            return False

    async def update_user_inventory(
        self, user_id: str, group_id: str, item_id: str, delta: int
    ) -> None:
        inv = await self.get_user_inventory(user_id, group_id) or {}
        cur = int(inv.get(item_id, 0))
        new = cur + int(delta)
        if new <= 0:
            if item_id in inv:
                inv.pop(item_id, None)
        else:
            inv[item_id] = new
        await self.save_user_inventory(user_id, group_id, inv)

    async def add_to_inventory(
        self, user_id: str, group_id: str, item_id: str, count: int
    ) -> None:
        await self.update_user_inventory(user_id, group_id, item_id, count)

    async def is_redis_available(self) -> bool:
        """当前实现不依赖 Redis，保持向后兼容性"""
        # 这里保守返回 False，除非插件实例显式注入 redis 属性
        return hasattr(self, "redis") and self.redis is not None

    async def set_synthesis_cooldown(
        self, cooldown_key: str, seconds: int = 300
    ) -> None:
        # 尝试使用 redis，否则使用内存缓存
        try:
            if await self.is_redis_available():
                await self.redis.setex(cooldown_key, seconds, 1)
                return
        except Exception:
            pass

        if not hasattr(self, "memory_cache"):
            self.memory_cache = {}
        self.memory_cache[cooldown_key] = int(time.time())

    async def get_synthesis_rarity_emoji(self, rarity: str) -> str:
        mapping = {
            "普通": "🔹",
            "稀有": "🔷",
            "史诗": "🔶",
            "传说": "🔸",
            "神话": "💠",
        }
        return mapping.get(rarity, "🔹")

    # ------------------ 对外兼容方法（供 main.py 调用） ------------------
    async def show_composite_list(
        self, event: AiocqhttpMessageEvent | None = None
    ) -> str:
        """返回合成配方的友好字符串列表"""
        recipes = await self.get_synthesis_recipes()
        recipes = recipes.get("recipes", {}) if isinstance(recipes, dict) else {}
        if not recipes:
            return "当前暂无合成配方。"
        lines = ["合成配方列表："]
        for name, info in recipes.items():
            lvl = info.get("workshop_level", 1)
            rate = info.get("success_rate", 50)
            desc = info.get("description", "")
            lines.append(f"• {name} - 需求工坊等级: {lvl} 成功率: {rate}% {desc}")
        return "\n".join(lines)

    async def handle_composite_command(
        self, event: AiocqhttpMessageEvent, input_str: str
    ) -> tuple[bool, str]:
        """兼容 main.py 的 /合成 调用：将输入拆分为 parts 并调用底层处理器"""
        parts = input_str.strip().split()
        return await self.handle_synthesis_command(event, parts)

    async def show_workshop(self, event: AiocqhttpMessageEvent) -> str:
        user_id = str(event.get_sender_id())
        group_id = str(event.get_group_id()) if event.get_group_id() else "private"
        workshop = await self.get_user_workshop(user_id, group_id) or {}
        level = workshop.get("level", 1)
        exp = workshop.get("exp", 0)
        synthesis_count = workshop.get("synthesis_count", 0)
        success_count = workshop.get("success_count", 0)
        lines = [
            f"工坊等级: {level}",
            f"经验: {exp}",
            f"合成次数: {synthesis_count}",
            f"成功次数: {success_count}",
        ]
        return "\n".join(lines)

    async def upgrade_workshop(self, event: AiocqhttpMessageEvent) -> str:
        """简单的工坊升级：直接增加一级并保存（未校验资源）"""
        user_id = str(event.get_sender_id())
        group_id = str(event.get_group_id()) if event.get_group_id() else "private"
        workshop = await self.get_user_workshop(user_id, group_id) or {}
        workshop["level"] = workshop.get("level", 1) + 1
        workshop["exp"] = 0
        await self.save_user_workshop(user_id, group_id, workshop)
        return f"🎉 工坊已升级到 {workshop['level']} 级（提示：此操作未验证消耗，生产环境请补充校验）。"

    async def handle_batch_composite_command(
        self, event: AiocqhttpMessageEvent, input_str: str
    ) -> tuple[bool, str]:
        """批量合成兼容方法：当前仅支持单次合成，批量会提示暂不支持。"""
        parts = input_str.strip().split()
        if not parts:
            return False, "请指定要合成的道具名称，使用方法: /批量合成 物品名称 数量"
        # 如果用户传入数量，则简单拒绝以免触发冷却或复杂流程
        if len(parts) >= 2:
            try:
                count = int(parts[-1])
                if count > 1:
                    return (
                        False,
                        "批量合成功能暂不可用（请先单次合成）。如需此功能，可提交 issue 请求实现。",
                    )
            except Exception:
                pass
        return await self.handle_synthesis_command(event, [parts[0]])

    async def handle_prop_decomposition_command(
        self, event: AiocqhttpMessageEvent, input_str: str
    ) -> tuple[bool, str]:
        """实现一个基础的道具分解：将物品按配表分解为材料（只处理数量为1的分解）。"""
        name = input_str.strip()
        if not name:
            return False, "请指定要分解的道具名称，使用方法: /道具分解 物品名称"
        # 查找 items 中的 id
        recipes = await self.get_synthesis_recipes()
        items = recipes.get("items", {})
        item_id = None
        for k, v in items.items():
            if v.get("name") == name or k == name:
                item_id = k
                break
        if not item_id:
            return False, f"找不到道具：{name}"
        decompose_map = recipes.get("decompose", {})
        if item_id not in decompose_map:
            return False, "该道具无法分解或未配置分解配方。"

        user_id = str(event.get_sender_id())
        group_id = str(event.get_group_id()) if event.get_group_id() else "private"
        inventory = await self.get_user_inventory(user_id, group_id)
        if inventory.get(item_id, 0) <= 0:
            return False, "背包中没有该道具，无法分解。"

        materials = decompose_map[item_id].get("materials", {})
        # 扣除物品
        await self.update_user_inventory(user_id, group_id, item_id, -1)
        # 添加材料
        for mid, cnt in materials.items():
            await self.add_to_inventory(user_id, group_id, mid, int(cnt))

        return True, f"✅ 成功分解{name}，获得材料：{materials}"

    async def show_composite_history(self, event: AiocqhttpMessageEvent) -> str:
        user_id = str(event.get_sender_id())
        group_id = str(event.get_group_id()) if event.get_group_id() else "private"
        workshop = await self.get_user_workshop(user_id, group_id) or {}
        synthesis_count = workshop.get("synthesis_count", 0)
        success_count = workshop.get("success_count", 0)
        lines = [
            "合成历史：",
            f"总合成次数: {synthesis_count}",
            f"成功次数: {success_count}",
        ]
        return "\n".join(lines)

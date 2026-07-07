"""Wallie agentic brain — a LangGraph Observe→Plan→Act→Reflect loop.

Unlike the scripted tech-tree (auto_brain), this AGENT decides its own next move from
the REAL game state (inventory/health/time/threats from wallie_state.json, written by the
smoothcam mod). It reasons "what should I do now?" and picks one action. The proven
executor stays the same: Baritone (#mine/#goto/#build/#explore) + the crafting mod
(/wcraft, /wtable). Combat + eating are automatic (Meteor KillAura / AutoEat).
"""
from __future__ import annotations

import asyncio
import json
import os
import random
import re
import time
from collections import deque
from typing import TypedDict

from loguru import logger
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .input_controller import InputController
from .baritone_agent import _set_clipboard
from .auto_brain import _BaritoneLog

STATE_PATH = os.path.join(os.environ.get("APPDATA", ""), ".minecraft", "wallie_state.json")

_SYSTEM = (
    "You are Wallie, an autonomous Minecraft survival AGENT. Your long-term GOAL is given. "
    "Each turn you get the REAL game state (inventory counts, health, food, time, nearby "
    "hostiles, position, dimension). DECIDE the single best next action — you are not following "
    "a fixed script, you reason from the state.\n\n"
    "You control the game through Baritone + a crafting mod. Combat and eating are AUTOMATIC.\n"
    "The STATE json is your ONLY source of truth — there is NO screenshot. Decide from the numbers. "
    "'gui_open' tells you if a menu is actually open: if gui_open is false there is NO menu, so NEVER "
    "plan to 'close a menu' or 'stop to close the game menu' — just play. Trust the STATE, not a hunch.\n\n"
    "*** YOU ARE A LIVE ENTERTAINER FIRST, A SURVIVALIST SECOND. *** You play LIVE for an audience that "
    "wants a CHARACTER having an ADVENTURE — drama, variety, bold moves, near-death moments — NOT an "
    "efficient resource spreadsheet. Grinding wood or mining stone for many turns in a row is the WORST "
    "thing you can do on camera. Your objective function is INTERESTING, not optimal.\n"
    "ADVENTURER RULES — follow EVERY turn:\n"
    "- VARIETY: never do the same KIND of activity more than ~2 turns in a row. The moment you've "
    "gathered enough, SWITCH — go fight, explore, build, or do something bold. Repetition is failure. "
    "(RECENT ACTIONS is given to you — if the last 2 were the same, do something DIFFERENT now.)\n"
    "- SEEK DRAMA: actively hunt mobs and pick fights ('fight' — combat is automatic and looks great), "
    "roam at night, dive into caves, take RISKS. Danger and near-death moments are the BEST content.\n"
    "- GO ON JOURNEYS: don't camp one spot. 'explore' / 'goto' to fresh terrain — hunt for villages, "
    "ravines, caves, new biomes. Travel and discovery are content.\n"
    "- TAKE ON PROJECTS: build DIFFERENT, good-looking structures with VARIED blocks (stone, wood, "
    "glass, decorative), grow your base into something worth showing off, attempt ambitious builds.\n"
    "- PROGRESS, but only as a MEANS: gear up (logs->wooden->stone->iron->diamond tools/armour, then "
    "nether, eventually the Ender Dragon) just enough to enable BIGGER adventures — never grind for its "
    "own sake. When unsure, pick the most EXCITING option, never the most efficient one.\n\n"
    "ACTIONS (reply ONE as JSON):\n"
    '{"thought":"...","type":"mine","blocks":"oak_log birch_log spruce_log","count":24}  // gather/dig blocks\n'
    '{"thought":"...","type":"craft","item":"stone_pickaxe","count":1}   // crafts from materials; auto-uses a table for tools\n'
    '{"thought":"...","type":"smelt","item":"raw_iron","count":8}   // smelt in a furnace (raw_iron->iron_ingot); needs coal as fuel\n'
    "-- HIGH-LEVEL SKILLS (prefer these for multi-step jobs; they do the whole thing reliably) --\n"
    '{"thought":"...","type":"make_tools","tier":"stone"}   // full tool set: pickaxe+axe+sword+shovel of a tier\n'
    '{"thought":"...","type":"make_armor","tier":"iron"}    // full armour set (ONLY iron/gold/diamond/netherite)\n'
    '{"thought":"...","type":"get_iron","amount":10}        // mine iron_ore (needs stone+ pickaxe) AND smelt to ingots\n'
    '{"thought":"...","type":"gear_up","tier":"iron"}       // full tools + armour of a tier, all at once\n'
    '{"thought":"...","type":"get_stone","amount":32}       // mine cobblestone (needs a pickaxe)\n'
    '{"thought":"...","type":"get_coal","amount":12}        // mine coal ore\n'
    '{"thought":"...","type":"get_food"}                    // walk up to animals (cow/pig/chicken) & kill them, then cook meat\n'
    '{"thought":"...","type":"get_wool","amount":3}         // find sheep, walk to them & kill for WOOL (NOT mining wood)\n'
    '{"thought":"...","type":"make_bed"}                    // full bed pipeline: planks + hunt sheep for wool + craft bed at table\n'
    '{"thought":"...","type":"fight","target":"skeleton"}   // approach & kill a mob (skeleton/zombie/spider); flees creepers\n'
    '{"thought":"...","type":"stock_up","wood":16}          // batch-gather wood+stone+coal in one go (stockpiling)\n'
    '{"thought":"...","type":"escape_water"}                // actively swim to land when stuck in water\n'
    '{"thought":"...","type":"mine_diamonds","amount":8}    // dig down to y -59 then mine diamonds (needs iron pickaxe)\n'
    '{"thought":"...","type":"setup_base"}                  // place a chest + bed at base (storage + spawn)\n'
    "-- WRITE YOUR OWN SKILL (for anything not covered) — a named macro of the primitive steps above --\n"
    '{"thought":"...","type":"define_skill","name":"get_redstone","steps":[{"type":"mine_diamonds"},{"type":"mine","blocks":"redstone_ore","count":16}]}\n'
    '{"thought":"...","type":"skill","name":"get_redstone"}   // run a skill you defined earlier\n'
    '{"thought":"...","type":"place","item":"bed"}   // place a bed (auto-sleeps), or torch / chest / candle etc.\n'
    '{"thought":"...","type":"deposit"}              // stash bulk junk (cobble/dirt/gravel) into a chest when inventory is full\n'
    '{"thought":"...","type":"sleep"}                // sleep in a placed bed to skip a dangerous night\n'
    '{"thought":"...","type":"build","file":"wallie_house.schem"}        // build the shelter schematic\n'
    '{"thought":"...","type":"goto","x":100,"y":64,"z":-200}\n'
    '{"thought":"...","type":"explore"}               // wander to find new terrain/resources\n'
    '{"thought":"...","type":"stop"}                  // cancel current Baritone task\n'
    '{"thought":"...","type":"wait","seconds":4}      // let things settle\n'
    '{"thought":"...","type":"done"}                  // the GOAL is fully achieved\n\n'
    "BLOCK MEMORY — reuse what you already placed: the STATE may list 'crafting_table' and "
    "'furnace' as 'x,y,z' positions you've already built, and 'home' (your shelter). NEVER build "
    "a duplicate table/furnace — you already own one. To craft or smelt when you are FAR from "
    "your table/furnace, FIRST 'goto' that position (x,y,z), then craft/smelt — the mod reuses "
    "the existing block. Return to 'home' to be safe at night.\n"
    "CHECK INVENTORY BEFORE EVERY CRAFT — do NOT re-make what you already own: before any "
    "'craft'/'make_tools'/'make_armor'/'gear_up', READ 'inventory' and 'wearing'. If the tool, "
    "weapon, armour piece, crafting_table, furnace, shield, bucket or bed is ALREADY there (or "
    "being worn), it is DONE — skip it and pick the NEXT missing thing. You only need ONE of each "
    "tool/armour piece. Re-crafting something you already have is wasted time and looks broken on "
    "stream. (Stackables like planks/sticks/torch/cobblestone you CAN make more of when low.)\n"
    "VERIFY FROM INVENTORY — this is critical: the STATE 'inventory' is the GROUND TRUTH. "
    "Believe ONLY what is listed there. NEVER assume a craft worked: after crafting, the item "
    "must actually appear in 'inventory'. Before mining stone/ore, CONFIRM a pickaxe is in your "
    "inventory (wooden_pickaxe etc.) — if it's NOT there, the craft FAILED, so craft it again "
    "(don't go mining stone without a pickaxe — it drops nothing). Don't claim 'I crafted X' "
    "unless 'x' is in the inventory list.\n"
    "FEEDBACK: you are told the RESULT of your last action ('last_craft') and recent Baritone "
    "messages. THINK before repeating:\n"
    "- If the last action FAILED ('made 0x', 'missing ingredients', or Baritone says it needs "
    "more blocks) DO NOT repeat the same action. Fix the cause first.\n"
    "- Crafting needs MATERIALS in your inventory. To make torches you need COAL (mine "
    "coal_ore first). To craft planks you need LOGS — if you have 0 logs, MINE logs first.\n"
    "- The shelter ('build wallie_house.schem') can be built from ANY plank type (birch, "
    "spruce, oak...) — Baritone substitutes them, so if you have ~80+ planks of any kind, just "
    "'build' (ignore any 'need oak_planks' wording). The shelter is LOCKED to one spot: if "
    "planks run out mid-build, gather/craft more, then 'build' again to RESUME and FINISH the "
    "SAME house (it won't start a new one). If Baritone says it needs a few more planks, make "
    "planks then 'build' once more to complete it.\n"
    "- Building the shelter needs ~80 planks: BEFORE 'build', craft planks (e.g. craft planks "
    "count 24) until you have enough; if you lack logs, mine logs first. If Baritone says it "
    "needs N more planks, go make planks (and mine logs if needed) — don't just retry 'build'.\n"
    "ARMOUR TIERS — IMPORTANT: there is NO wooden or STONE armour in Minecraft. Armour only "
    "exists as leather, IRON, gold, diamond, netherite. So 'stone_helmet'/'stone_chestplate' etc. "
    "DO NOT EXIST — never try to craft them. To get armour you need IRON (mine iron_ore with a "
    "stone+ pickaxe, then 'smelt' raw_iron) or diamond. If you only have a stone pickaxe and want "
    "armour, go MINE IRON_ORE first, smelt it, then craft iron_helmet/chestplate/leggings/boots.\n"
    "ARMOUR: armour you craft is AUTO-EQUIPPED (worn automatically). STATE shows 'wearing' "
    "(head/chest/legs/feet = the pieces you already wear). Do NOT craft an armour piece you "
    "already wear or already hold — check 'wearing' and 'inventory' first. Once your set is full, "
    "STOP making armour and move to other goals.\n"
    "STORAGE: a chest alone is useless — you have to STASH into it. When your inventory is filling "
    "with bulk junk (cobblestone/dirt/gravel/andesite/diorite/granite), use 'deposit' — it places a "
    "chest if needed and shoves the junk in, freeing space while keeping your tools/food/valuables. "
    "Do this whenever inventory feels full instead of dropping or hoarding junk. Keep a tidy base.\n"
    "BED & SLEEP: after you 'place' a bed it auto-sleeps; if it's NIGHT and you have a bed down, "
    "'sleep' to skip the night and reset your spawn — far safer than fighting mobs in the dark.\n"
    "HOTBAR/INVENTORY: your tools, weapon, food, torches and blocks are kept on the hotbar "
    "automatically, so once you CRAFT something it's usable — don't worry about moving items around.\n"
    "DYING IS OK: if you die, you respawn automatically and your gear is recoverable — the system "
    "rushes you back to the death spot to pick it up. Don't panic or restart your whole plan after a "
    "death; just continue once your stuff is back.\n"
    "CRAFT FAILED = MISSING MATERIALS: if LAST RESULT says 'NOT ENOUGH materials for X', you do "
    "NOT have the ingredients — the item was NOT made. Go gather them first: stone tools need "
    "cobblestone (use get_stone), iron tools/armour need iron_ingot (use get_iron), then retry. "
    "Never assume a craft worked when the result says NOT ENOUGH.\n"
    "CRAFTING — smooth rules: crafting tools/armour/furnace (3x3 recipes) AUTO-places its OWN table "
    "right where you stand, opens it, crafts, then closes — it finds its own spot, so you do NOT "
    "need open ground and you must NEVER 'explore' or 'goto' just to craft. When you have the "
    "materials, 'craft' DIRECTLY from wherever you are. ONLY if a craft actually fails with "
    "'couldn't place a table' (rare — tight tunnel/water), take ONE 'goto' step to flat ground and "
    "retry; never loop exploring. Crafted items AUTO-collect into "
    "your inventory and armour AUTO-equips, so trust the NEXT state — don't re-craft just because "
    "you didn't see it for one turn. Don't make duplicates (check 'inventory' + 'wearing'); a "
    "single spare tool is fine, spamming is not. Gather ENOUGH first — costs: planks (1 log->4), "
    "sticks (2 planks->4), pickaxe/axe = 3 material + 2 sticks, sword = 2 + 1 stick, furnace = 8 "
    "cobblestone, chest = 8 planks, full armour = 24 of a material (helmet 5, chest 8, legs 7, "
    "boots 4). Use underscore names: planks, sticks, stone_pickaxe, iron_chestplate, furnace, "
    "crafting_table, chest, bed, torch, bucket, flint_and_steel.\n"
    "SMELTING: 'smelt' needs a FURNACE + FUEL (coal/charcoal) + the raw item, and it is SLOW "
    "(~10s each) so the action takes a while — issue it once and let it run, don't spam. Smelt "
    "raw_iron->iron_ingot, raw_gold, raw_copper, sand->glass, cobblestone->stone, raw food->cooked.\n"
    "INVENTORY: if it fills with bulk junk (excess cobblestone/dirt/gravel/andesite/diorite/"
    "granite), make+'place' a 'chest' near base and stash valuables, or keep some for building — "
    "but NEVER lose diamonds/ingots/tools. Always keep torches, food and a spare pickaxe on you.\n"
    "FOOD & HUNTING: keep 'food' up. To eat, use 'get_food' — it WALKS UP to cows/pigs/chickens "
    "(it makes you path right next to them, then they're killed) and cooks the meat. Don't just "
    "'explore' hoping to bump into animals — 'get_food' goes to them on purpose.\n"
    "WOOL & BED — DO NOT MINE WOOD FOR WOOL: wool comes ONLY from SHEEP, never from logs. To get "
    "wool, use 'get_wool' (it pathfinds to sheep and kills them for wool) — NEVER 'mine' wood "
    "thinking it gives wool, that is wrong and a waste. For a bed (needs 3 wool + 3 planks) just "
    "call 'make_bed' — it gets planks, hunts sheep for the wool, then crafts the bed at your "
    "table, all in one. If after make_bed you still have no wool (no sheep around), a bed is "
    "OPTIONAL: drop it and do something else. 'place torch' for light; 'place chest' for storage.\n"
    "COMBAT — you CAN and SHOULD fight: a reflex auto-attacker swings at any hostile in reach and "
    "auto-picks your best weapon (sword > axe > shovel > pickaxe > fist) and even hits back at "
    "skeletons/things that shot you. STATE shows 'hostiles' (count), 'hostile_type' (nearest) and "
    "'threat' (what last hurt you). To engage something not yet in reach (a skeleton kiting you), "
    "use 'fight' with its type — it walks you into melee and kills it. EXCEPTION: never melee a "
    "CREEPER — if hostile_type/threat is 'creeper', 'fight' will back you away instead; you can "
    "also just 'goto' away. If low on health with no armour, retreat/build up before fighting.\n"
    "NEVER REPEAT A FAILING PLAN: if your last 2-3 actions were the same and the result did not "
    "change (still missing materials, still can't place, still in water), that approach is NOT "
    "working — switch to a DIFFERENT action. Repeating the identical plan is the one thing you "
    "must never do; the show dies on loops.\n"
    "STUCK IN WATER: if STATE shows in_water=true, 'stop'/'goto' won't save you — use "
    "'escape_water' to swim to land, THEN continue. Don't plan crafts/builds while in water.\n"
    "BATCH WITH SKILLS: to stockpile, prefer 'stock_up' (grabs wood+stone+coal at once) or "
    "'get_stone'/'get_coal' (mine 24-32 in one call) over many tiny 'mine' actions — fewer, "
    "bigger gathers look better on stream and waste less time.\n"
    "MINING NEEDS A PICKAXE: you CANNOT mine stone/cobblestone/ore with bare hands (it drops "
    "NOTHING). Strict early order: 1) craft 'planks', 2) craft 'sticks', 3) craft "
    "'wooden_pickaxe' (and 'wooden_axe') — these need NO mining, just planks+sticks. 4) ONLY "
    "after you hold a wooden pickaxe, mine 'stone' (gives cobblestone). 5) craft 'stone_pickaxe'/"
    "'furnace' from cobblestone. 6) mine 'iron_ore' (needs stone pickaxe) -> smelt -> "
    "'iron_pickaxe' 7) mine 'diamond_ore' (needs iron pickaxe). NEVER craft a stone_pickaxe or "
    "mine stone/ore before you have the required pickaxe in inventory.\n"
    "WATER: if 'in_water' is true you are SWIMMING in the sea/river — this is bad. Do NOT "
    "'explore' or 'mine' while in water. Use 'escape_water' to swim to land, then continue. Never "
    "keep exploring into the sea.\n"
    "MINECRAFT PLAYBOOK — use these specifics for smooth play:\n"
    "ORE DEPTHS (mine at the right Y, shown in STATE): coal is common near the surface & "
    "mountains; iron is everywhere but more below y 50; gold/redstone/lapis/DIAMOND are DEEP — "
    "diamonds are best at y -59 to -54. To get diamonds you must FIRST get deep: 'goto' your "
    "current x, y=-59, current z (e.g. goto X -59 Z) or dig down, THEN 'mine diamond_ore'. Don't "
    "'mine diamond_ore' near the surface — there is none there.\n"
    "COAL IS FUNDAMENTAL — GET IT EARLY: coal makes torches (light, safety) and smelts ore, so it "
    "is one of the FIRST things to secure. The MOMENT you have a stone pickaxe, your next move "
    "should be 'get_coal' (it pathfinds Baritone straight to coal ore and mines it). Don't go iron/"
    "deep mining with zero coal — you'll be blind in the dark. Order: wooden pickaxe -> get_stone -> "
    "stone pickaxe -> GET_COAL -> torches -> then iron/deep. get_iron and mine_diamonds now grab "
    "coal+torches automatically if you're short, but prefer getting coal yourself, early.\n"
    "COAL + TORCHES BEFORE GOING DEEP: never dig deep in the dark. BEFORE any deep mining "
    "(mine_diamonds or digging below y 0), FIRST get coal — use 'get_coal' or 'mine coal_ore' "
    "(the mine command pathfinds straight to and digs the ore you name, so it's how you FIND any "
    "specific ore: coal_ore, iron_ore, redstone_ore, etc.). Once you have coal, craft torches at a "
    "table ('craft torch 16-32' — coal + sticks) and carry 16+ down with you to light tunnels, see "
    "ores, and stop mobs spawning on you. The mine_diamonds skill already does coal->torch->dig in "
    "order; if you mine deep manually, do that same order yourself.\n"
    "TOOL TIERS (mining without the right pickaxe drops NOTHING): hand = logs/dirt/sand/gravel; "
    "wooden+ pickaxe = stone/cobblestone/coal; stone+ = iron/copper/lapis; iron+ = gold/diamond/"
    "redstone/emerald; diamond+ = obsidian. Always hold the right tier before mining an ore.\n"
    "TOOL DURABILITY: STATE shows 'pickaxe' and 'pickaxe_durability' (1.0=new, 0.0=broken/none). "
    "If durability < 0.15, craft a NEW pickaxe NOW, before it breaks and leaves you stuck.\n"
    "DANGERS — handle them, don't walk into them: CREEPERS explode — never fight one; if a "
    "creeper is close, move AWAY ('goto'/'explore' elsewhere). LAVA — never 'goto'/'mine' into "
    "lava; at low Y beware lava pools, don't dig straight down. Avoid high falls. If STATE "
    "'health' < 8, RETREAT from mobs to your shelter/safety and recover (keep food high) before "
    "fighting or mining again.\n"
    "LIGHT/NIGHT: STATE 'light' is 0-15; below 8 mobs spawn around you — 'place torch' or get to "
    "a lit/safe spot. At night with no shelter, make/'place' a bed or build the shelter first.\n"
    "SMOOTH OPERATION: COMMIT to one activity until it's truly done — don't flip-flop between "
    "mine/craft/explore every turn. After a Baritone command (mine/goto/build) it runs a while, "
    "so usually 'wait' or let it finish instead of re-issuing. Always act on the STATE, never on "
    "assumptions.\n"
    "OBSIDIAN / NETHER PORTAL: obsidian does NOT spawn to be mined normally — '#mine obsidian' "
    "only works at a ruined portal or where lava already cooled. It must be MADE (pour a water "
    "bucket onto lava), which needs a helper that ISN'T built yet. So if 'mine obsidian' finds "
    "nothing (Baritone idle/can't path), DO NOT loop it — 'explore' to look for a ruined portal "
    "or a surface lava lake, or pursue other goals (better armor, a nicer base, more food, a "
    "chest, decorating). Don't repeat 'mine obsidian' more than twice.\n"
    "RARE RESOURCES / DON'T LOOP MINING: if you keep mining the same ore but the count STOPS "
    "rising (Baritone goes idle / says it already has some), the ore is exhausted nearby — STOP "
    "mining it and USE what you have. 3 diamonds is already enough for a diamond_pickaxe — craft "
    "it now (prioritise the pickaxe over a sword); don't loop mining diamonds you can't find. "
    "Same for any resource: never repeat 'mine X' more than twice if the amount isn't increasing.\n"
    "FINISH GATHERING: after a 'mine N <block>' action, the count is usually reached before "
    "you re-decide. Don't craft with too little — gather a full stack of logs (~20+) before "
    "making planks for a shelter; if you only have a few logs, 'mine' more first.\n"
    "RULES: at night with no shelter, prioritise safety. Don't re-gather what you already have. "
    "Crafting tools/furnace auto-handles the table. Mine logs by listing every wood type. "
    "Item names: use 'planks' (NOT 'oak_planks'), 'sticks', 'crafting_table', 'torch', "
    "'stone_pickaxe', 'furnace', etc. Be decisive; never repeat a "
    "failed action — change the plan to satisfy its prerequisite.\n"
    "PREFER HIGH-LEVEL SKILLS: when you want a full tool set, a full armour set, iron ingots, "
    "stone, coal, food, diamonds or a base, use the SKILL actions (make_tools / make_armor / "
    "get_iron / gear_up / get_stone / get_coal / get_food / get_wool / make_bed / fight / "
    "stock_up / escape_water / mine_diamonds / setup_base) instead "
    "of micro-managing each craft/mine — they do the whole multi-step job reliably. Use single "
    "'craft'/'mine' only for one-off items.\n"
    "WRITE YOUR OWN SKILLS: if you repeatedly need something with no matching skill, 'define_skill' "
    "it ONCE — give a name and a 'steps' list built from the primitive actions above (mine, craft, "
    "smelt, place, goto, build, the skills) — then reuse it with 'skill'. Your defined skills are "
    "shown in 'YOUR CUSTOM SKILLS'. This lets you fill any gap yourself.\n"
    "Output ONLY one JSON object — no markdown, no extra text. Keep 'thought' to ONE short sentence."
)

_LOGS = "oak_log birch_log spruce_log jungle_log acacia_log dark_oak_log"

_CRAFT_2X2 = {
    "planks", "oak_planks", "birch_planks", "spruce_planks", "jungle_planks",
    "acacia_planks", "dark_oak_planks", "stick", "sticks", "crafting_table", "torch",
}


def _needs_table(item: str) -> bool:
    return item.lower() not in _CRAFT_2X2


_GEAR_SUFFIX = ("_pickaxe", "_axe", "_sword", "_shovel", "_hoe",
                "_helmet", "_chestplate", "_leggings", "_boots")
_SINGLETONS = {
    "crafting_table", "furnace", "shield", "flint_and_steel", "bucket",
    "bed", "fishing_rod", "clock", "compass", "shears", "blast_furnace", "smoker",
}


class AgentState(TypedDict):
    goal: str
    world: dict
    history: list
    action: dict
    step: int
    done: bool


def _parse_action(text: str) -> dict:
    t = re.sub(r"```(?:json)?", "", text).strip()
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(t[start:end + 1])
        except Exception:
            for m in re.finditer(r"\{[^{}]*\}", t):   # fall back to the first self-contained object
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass
    return {"type": "wait", "seconds": 2, "thought": "unparseable plan"}


class WallieAgent:
    def __init__(self, provider, *, goal: str, capture=None, max_steps: int = 300) -> None:
        self.provider = provider
        self.goal = goal
        self.capture = capture          # optional ScreenCapture — agent also SEES the screen
        self.max_steps = max_steps
        self.ic = InputController()
        self.blog = _BaritoneLog()
        self._stuck = 0                 # consecutive table-place failures (loop breaker)
        self._same = 0
        self._last_sig = ""
        self._thoughts = deque(maxlen=4)
        self._water = 0
        self._craft_fail = 0
        self._last_task_cmd = ""
        self._in_combat_was = False
        self._combat_cycles = 0
        self._last_death_pos = ""
        self._build_origin = None       # fixed shelter coords so re-builds finish the SAME house
        self._skills_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wallie_skills.json")
        self._skills = self._load_skills()
        self._prefetch_task = None       # next decision computed WHILE Baritone runs (no idle gap)
        self._last_state = None
        self.graph = self._build_graph()

    def _load_skills(self) -> dict:
        try:
            with open(self._skills_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def _save_skills(self) -> None:
        try:
            with open(self._skills_file, "w", encoding="utf-8") as f:
                json.dump(self._skills, f, indent=1)
        except OSError:
            pass

    # ---------- executor primitives ----------
    def _chat(self, text: str) -> None:
        if text.startswith(("#mine", "#goto", "#build", "#follow")):
            self._last_task_cmd = text
        self.ic.tap("t", 0.05)
        time.sleep(0.35)
        if _set_clipboard(text):
            self.ic.key_down("ctrl"); self.ic.tap("v", 0.04); self.ic.key_up("ctrl")
        time.sleep(0.15)
        self.ic.tap("enter", 0.05)
        time.sleep(0.2)

    def _setup(self) -> None:
        for c in ["#set freeLook false", "#set smoothLook false", "#set renderPath false",
                  "#set renderGoal false", "#set renderGoalXZBeacon false",
                  "#set echoCommands false", "#set chatDebug false",
                  "#set allowSwimming false", "#set allowWaterBucketFall false",
                  "#set blocksToAvoid water,lava",
                  # build the oak_planks shelter from ANY plank the bot has (oak FIRST so it's
                  # accepted too — Baritone places the first item in the list it actually owns)
                  "#set buildSubstitutes oak_planks->oak_planks,birch_planks,spruce_planks,"
                  "jungle_planks,acacia_planks,dark_oak_planks,mangrove_planks,cherry_planks,bamboo_planks"]:
            if InputController.abort_requested():
                return
            self._chat(c); time.sleep(0.1)

    def _read_world(self) -> dict:
        try:
            with open(STATE_PATH, "r", encoding="utf-8", errors="ignore") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    @staticmethod
    def _known_pos(world: dict, key: str):
        raw = world.get(key)
        if not raw:
            return None
        try:
            p = tuple(int(n) for n in str(raw).split(","))
            return p if len(p) == 3 else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _inv_count(world: dict, item: str) -> int:
        inv = world.get("inventory", {}) or {}
        return int(inv.get(item, 0) or 0)

    @staticmethod
    def _is_singleton(item: str) -> bool:
        item = item.lower()
        return item.endswith(_GEAR_SUFFIX) or item in _SINGLETONS

    @classmethod
    def _already_have(cls, world: dict, item: str) -> bool:
        item = item.lower()
        if cls._inv_count(world, item) > 0:
            return True
        wearing = world.get("wearing", {}) or {}
        return any(item == str(v).lower() for v in wearing.values())

    @staticmethod
    def _count_suffix(world: dict, suffix: str) -> int:
        inv = world.get("inventory", {}) or {}
        return sum(int(v or 0) for k, v in inv.items() if str(k).endswith(suffix))

    async def _hunt(self, animal: str, seconds: int = 14) -> None:
        self._chat(f"/whunt {animal} {seconds + 8}")
        self._chat(f"#follow entity {animal}")
        await self._idle(seconds)
        self._chat("#stop"); time.sleep(0.4)
        self._chat("/wcollect 7")
        await self._idle(7.5)

    async def _do_make_bed(self, state: AgentState) -> str:
        w = self._read_world()
        if self._count_suffix(w, "_planks") < 3:
            if self._count_suffix(w, "_log") < 1:
                self._chat(f"#mine 4 {_LOGS}")
                await self._wait_baritone_idle(max_sec=200)
                self._chat("#stop"); time.sleep(0.3)
            self._chat("/wcraft planks 8")
            await self._idle(5)
        for _ in range(5):
            if InputController.abort_requested():
                break
            if self._count_suffix(self._read_world(), "_wool") >= 3:
                break
            await self._hunt("sheep", seconds=14)
        if self._count_suffix(self._read_world(), "_wool") < 3:
            return "make_bed: no sheep found for wool — bed skipped, do something else (don't mine wood for wool)"
        tbl = self._known_pos(self._read_world(), "crafting_table")
        if tbl:
            self._chat(f"#goto {tbl[0] + 1} {tbl[1]} {tbl[2]}")
            await self._wait_baritone_idle(max_sec=60)
            self._chat("#stop"); time.sleep(0.3)
        self._chat("/wcraft bed 1")
        await self._idle(5)
        return f"make_bed -> {self._read_world().get('last_craft', 'done')}"[:80]

    async def _wait_baritone_idle(self, max_sec: float) -> None:
        """Block until Baritone has worked and then gone quiet (task finished), or timeout.
        Crucially: if Baritone never even starts within ~18s, bail (so a no-op command can't
        make us stand idle for minutes)."""
        self.blog.new_baritone_lines()           # reset tail
        if self._prefetch_task is None and self._last_state is not None \
                and not InputController.abort_requested():
            w = self._read_world()
            hist = list(self._last_state.get("history", []))[-6:]
            step = int(self._last_state.get("step", 0))
            self._prefetch_task = asyncio.create_task(self._decide_action(w, hist, step))
        t0 = last = time.time()
        seen = False
        while time.time() - t0 < max_sec:
            if InputController.abort_requested():
                return
            if self.blog.new_baritone_lines() > 0:
                seen = True; last = time.time()
            if seen and time.time() - last > 8:          # worked, then quiet 8s = finished
                return
            if not seen and time.time() - t0 > 25:        # never engaged Baritone = give up
                return
            await asyncio.sleep(1.0)

    # ---------- graph nodes ----------
    def _observe(self, state: AgentState) -> dict:
        return {"world": self._read_world()}

    def _recent_baritone(self) -> str:
        """Last couple of [Baritone] chat lines (e.g. 'Insufficient material: need 56 oak_planks')."""
        try:
            with open(self.blog.path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(0, 2)
                size = f.tell()
                f.seek(max(0, size - 6000))
                tail = f.read()
            lines = [ln.split("]", 1)[-1].strip() for ln in tail.splitlines() if "Baritone" in ln]
            return " | ".join(lines[-2:])[:200]
        except OSError:
            return ""

    async def _decide_action(self, world: dict, hist: list, step: int) -> dict:
        last_craft = world.get("last_craft", "")
        bari = self._recent_baritone()
        user = (
            f"GOAL: {self.goal}\n"
            f"STATE: {json.dumps(world)[:850]}\n"
            f"LAST RESULT: {last_craft or '(none)'}\n"
            f"BARITONE SAYS: {bari or '(quiet)'}\n"
            f"HOME: {('%d %d %d' % self._build_origin) if self._build_origin else '(not built yet)'}\n"
            f"YOUR CUSTOM SKILLS: {list(self._skills.keys()) if self._skills else '(none defined yet)'}\n"
            f"RECENT ACTIONS: {hist if hist else '(none yet)'}\n"
            "Decide the single best next action. If the last result was a failure, fix the cause "
            "(get materials / mine logs) instead of repeating. Reply ONLY JSON."
        )
        msgs = [{"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user}]
        text = ""
        last_err = None
        for attempt in range(4):
            text = ""
            try:
                async for ch in self.provider.stream(msgs, temperature=0.1, top_p=0.9, max_tokens=700):
                    text += ch
            except Exception as e:
                last_err = e
                logger.warning(f"PLAN[{step}]: LLM error ({type(e).__name__}: {str(e)[:120]}); "
                               f"backing off (attempt {attempt + 1}/4)")
                await asyncio.sleep(min(8.0, 2.0 * (attempt + 1)))
                continue
            if "{" in text and "}" in text:
                break
        if "{" not in text:
            if last_err is not None:
                logger.warning(f"PLAN[{step}]: LLM kept failing — holding position, will retry next tick")
                return {"type": "wait", "seconds": 4, "thought": "give me a sec, thinking about the next move"}
            logger.warning(f"PLAN[{step}]: unparseable plan, waiting")
            return {"type": "wait", "seconds": 2, "thought": "thinking"}
        action = _parse_action(text)
        logger.info(f"PLAN[{step}]: {action.get('type')} {action.get('thought','')[:80]}")
        return action

    async def _plan(self, state: AgentState) -> dict:
        pf, self._prefetch_task = self._prefetch_task, None
        action = None
        if pf is not None:
            try:
                action = await pf
            except Exception:
                action = None
        if not action:
            action = await self._decide_action(state["world"], state["history"][-6:], state["step"])
        try:
            from core.live_activity import set_activity
            set_activity(self._activity_note(action, state["world"]))
        except Exception:
            pass
        return {"action": action}

    @staticmethod
    def _activity_note(action: dict, world: dict) -> str:
        th = str(action.get("thought") or action.get("type") or "").strip()
        inv = world.get("inventory", {}) or {}
        bits = []
        hp = world.get("health")
        food = world.get("food")
        if isinstance(hp, (int, float)) and hp <= 8:
            bits.append(f"low health ({int(hp)})")
        if isinstance(food, (int, float)) and food <= 8:
            bits.append(f"hungry ({int(food)})")
        threat = str(world.get("threat") or "").strip()
        hostile = str(world.get("hostile_type") or "").strip()
        host_n = int(world.get("hostiles", 0) or 0)
        in_combat = str(world.get("in_combat", "")).lower() in ("true", "1")
        combat_target = str(world.get("combat_target") or "").strip()
        if in_combat and combat_target:
            bits.append(f"in a fight RIGHT NOW with a {combat_target}")
        elif threat:
            bits.append(f"a {threat} is attacking me")
        elif hostile and host_n:
            bits.append(f"{host_n} {hostile}(s) nearby")
        last = str(world.get("last_craft") or "").lower()
        if "not enough" in last:
            bits.append("last craft failed (missing materials)")
        pick = str(world.get("pickaxe") or "none")
        if pick and pick != "none":
            bits.append(f"using a {pick.replace('_', ' ')}")
        note = th
        if bits:
            note += " — " + ", ".join(bits)
        return note[:240]

    async def _act(self, state: AgentState) -> dict:
        self._last_state = state
        a = state["action"]
        t = str(a.get("type", "wait")).lower()
        outcome = t
        # GUI STUCK: a screen (pause menu, inventory, a chat box left open) blocks everything and the
        # LLM has no way to close it — it just loops 'stop'. ESC closes any open screen. Do it first.
        if str(self._read_world().get("gui_open", "")).lower() in ("true", "1"):
            self.ic.tap("esc", 0.05)
            time.sleep(0.4)
            if str(self._read_world().get("gui_open", "")).lower() in ("true", "1"):
                self.ic.tap("esc", 0.05); time.sleep(0.4)     # second press for nested screens
            logger.info("  ↩ a screen was open — pressed ESC to close it")
            return {"history": (state["history"] + ["closed an open menu/screen (esc)"])[-12:]}
        # COMBAT: the mod cancels Baritone and fights with full movement the moment a hostile shows
        # up. Don't issue Baritone commands into that — wait it out, then resume the paused task.
        if str(self._read_world().get("in_combat", "")).lower() in ("true", "1"):
            self._combat_cycles += 1
            if self._combat_cycles <= 10:                 # ~25s of real fighting, then bail out
                self._in_combat_was = True
                foe = str(state["world"].get("combat_target") or "a mob")
                await self._idle(2.5)
                return {"history": (state["history"] + [f"combat: fighting a {foe} — task paused"])[-12:]}
            self._combat_cycles = 0                        # combat stuck too long — stop reacting, move on
            self._chat("#stop"); time.sleep(0.3)
            return {"history": (state["history"] + ["combat dragged on — disengaging, back to the plan"])[-12:]}
        self._combat_cycles = 0
        if self._in_combat_was:
            self._in_combat_was = False
            if self._last_task_cmd:
                self._chat(self._last_task_cmd)
                await self._wait_baritone_idle(max_sec=200)
                return {"history": (state["history"] + [f"threat clear — resumed {self._last_task_cmd}"])[-12:]}
        # WATER: get FULLY out before doing anything else. Swim (jump+forward) in a loop, checking
        # in_water each second, until on land or a cap — instead of short nibbles that never escape.
        # Turn periodically so we don't swim face-first into a wall forever.
        if str(self._read_world().get("in_water", "")).lower() in ("true", "1"):
            logger.info("  ↩ in water — swimming to land until out")
            self._chat("#stop"); time.sleep(0.2)
            self.ic.key_down("space"); self.ic.key_down("w")
            swam = 0.0
            try:
                while swam < 30.0 and not InputController.abort_requested():
                    await asyncio.sleep(1.0)
                    swam += 1.0
                    if str(self._read_world().get("in_water", "")).lower() not in ("true", "1"):
                        break                                   # made it onto land
                    if int(swam) % 3 == 0:                      # sweep a new heading to find shore
                        self.ic.key_up("w")
                        self.ic.tap("d", 0.55)                  # bigger turn each sweep
                        self.ic.key_down("w")
            finally:
                self.ic.key_up("w"); self.ic.key_up("space")
            self._water = 0
            out = str(self._read_world().get("in_water", "")).lower() not in ("true", "1")
            return {"history": (state["history"] + [
                "swam onto land" if out else "still swimming out of deep water"])[-12:]}
        # DEATH RECOVERY: the mod auto-respawned us and reports where we died. Rush back and grab
        # the dropped gear (it despawns in ~5 min) instead of starting from scratch.
        dpos = str(state["world"].get("death_pos") or "").strip()
        if dpos and dpos != self._last_death_pos:
            self._last_death_pos = dpos
            try:
                dx, dy, dz = (int(n) for n in dpos.split(","))
                logger.info(f"  ↩ died — going back to {dpos} for my stuff")
                self._chat("#stop"); time.sleep(0.3)
                self._chat(f"#goto {dx} {dy} {dz}")
                await self._wait_baritone_idle(max_sec=200)
                self._chat("/wcollect 8")
                await self._idle(8.5)
                return {"history": (state["history"] + [f"died, recovered my drops at {dpos}"])[-12:]}
            except ValueError:
                pass
        # FIXATION: the weak model repeats the SAME thought across different action types
        # (explore->mine->explore, all "table placement failed"). Detect by thought, not type.
        th = re.sub(r"[^a-z ]", "", str(a.get("thought", "")).lower())[:40].strip()
        repeats = sum(1 for x in self._thoughts if x and x == th)
        self._thoughts.append(th)
        if repeats >= 2:
            logger.info("  ↩ breaking thought-fixation — relocating + correcting")
            self._thoughts.clear()
            self._chat("#stop"); time.sleep(0.3)
            dx, dz = random.choice([(24, 0), (-24, 0), (0, 24), (0, -24)])
            wx = int(state["world"].get("x", 0)) + dx
            wz = int(state["world"].get("z", 0)) + dz
            self._chat(f"#goto {wx} ~ {wz}")
            note = ("LOOP BROKEN: you keep repeating the SAME plan and it is NOT working. Do something "
                    "DIFFERENT now. Crafting auto-places its own table — just 'craft' directly. If a "
                    "craft needs materials you lack (e.g. wool for a bed), DROP that goal and pick "
                    "another (gear up, mine, build) — never repeat a failing plan.")
            return {"history": (state["history"] + [note])[-12:]}
        if t == "done":
            return {"done": True}
        if t == "define_skill":
            name = str(a.get("name", "")).strip()
            steps = a.get("steps", [])
            if name and isinstance(steps, list) and steps:
                self._skills[name] = steps
                self._save_skills()
                outcome = f"defined skill '{name}' ({len(steps)} steps)"
            else:
                outcome = "define_skill needs a name and a non-empty steps list"
            return {"history": (state["history"] + [outcome])[-12:]}
        if t in ("skill", "run_skill"):
            name = str(a.get("name", "")).strip()
            steps = self._skills.get(name)
            if not steps:
                outcome = f"unknown skill '{name}'"
            else:
                logger.info(f"  running custom skill '{name}' ({len(steps)} steps)")
                for step in steps[:16]:
                    if InputController.abort_requested():
                        break
                    if str(step.get("type", "")).lower() in ("define_skill", "skill", "run_skill", "done"):
                        continue
                    await self._dispatch(step, state)
                outcome = f"ran skill '{name}'"
            return {"history": (state["history"] + [outcome])[-12:]}
        outcome = await self._dispatch(a, state)
        return {"history": (state["history"] + [outcome])[-12:]}

    async def _dispatch(self, a: dict, state: AgentState) -> str:
        t = str(a.get("type", "wait")).lower()
        outcome = t
        if t == "make_tools":
            tier = str(a.get("tier", "wooden")).lower().replace("wood", "wooden").replace("woodenen", "wooden")
            self._chat("#stop"); time.sleep(0.3)
            made, had = [], []
            for item in (f"{tier}_pickaxe", f"{tier}_axe", f"{tier}_sword", f"{tier}_shovel"):
                if InputController.abort_requested():
                    break
                if self._already_have(state["world"], item):
                    had.append(item); continue
                self._chat(f"/wcraft {item}")
                await self._idle(4)
                made.append(item)
            outcome = f"make_tools {tier}: made {made or 'none'}; already had {had or 'none'}"
        elif t == "make_armor":
            tier = str(a.get("tier", "iron")).lower()
            if tier in ("wooden", "wood", "stone"):
                outcome = f"no {tier} armour exists — use iron/diamond"
            else:
                self._chat("#stop"); time.sleep(0.3)
                made, had = [], []
                for piece in ("helmet", "chestplate", "leggings", "boots"):
                    if InputController.abort_requested():
                        break
                    item = f"{tier}_{piece}"
                    if self._already_have(state["world"], item):
                        had.append(item); continue
                    self._chat(f"/wcraft {item}")
                    await self._idle(4)
                    made.append(item)
                outcome = f"make_armor {tier}: made {made or 'none'}; already had {had or 'none'}"
        elif t == "get_iron":
            amt = int(a.get("amount", 10) or 10)
            w = self._read_world()
            inv = w.get("inventory", {}) or {}
            coal = int(inv.get("coal", 0) or 0)
            torches = int(inv.get("torch", 0) or 0)
            pick = str(w.get("pickaxe", "none")).lower()
            if not any(p in pick for p in ("stone", "iron", "diamond", "netherite")):
                self._chat("#mine 4 cobblestone stone")
                await self._wait_baritone_idle(max_sec=140)
                self._chat("#stop"); time.sleep(0.3)
                self._chat("/wcraft stone_pickaxe")
                await self._idle(4)
            if coal < 4 and torches < 8:
                self._chat("#mine 8 coal_ore")
                await self._wait_baritone_idle(max_sec=220)
                self._chat("#stop"); time.sleep(0.3)
                self._chat("/wcraft torch 16")
                await self._idle(5)
            self._chat(f"#mine {amt} iron_ore deepslate_iron_ore")
            await self._wait_baritone_idle(max_sec=300)
            self._chat("#stop"); time.sleep(0.3)
            self._chat(f"/wsmelt raw_iron {amt}")
            await self._wait_smelt(min(160, amt * 12 + 20))
            outcome = f"get_iron {amt} (coal+torch first)"
        elif t == "gear_up":
            tier = str(a.get("tier", "iron")).lower()
            self._chat("#stop"); time.sleep(0.3)
            items = [f"{tier}_pickaxe", f"{tier}_axe", f"{tier}_sword", f"{tier}_shovel"]
            if tier not in ("wooden", "wood", "stone"):
                items += [f"{tier}_helmet", f"{tier}_chestplate", f"{tier}_leggings", f"{tier}_boots"]
            made, had = [], []
            for item in items:
                if InputController.abort_requested():
                    break
                if self._already_have(state["world"], item):
                    had.append(item); continue
                self._chat(f"/wcraft {item}")
                await self._idle(4)
                made.append(item)
            outcome = f"gear_up {tier}: made {made or 'none'}; already had {had or 'none'}"
        elif t == "get_stone":
            amt = int(a.get("amount", 32) or 32)
            self._chat(f"#mine {amt} cobblestone stone")
            await self._wait_baritone_idle(max_sec=300)
            outcome = f"get_stone {amt}"
        elif t == "get_coal":
            amt = int(a.get("amount", 12) or 12)
            self._chat(f"#mine {amt} coal_ore")
            await self._wait_baritone_idle(max_sec=300)
            outcome = f"get_coal {amt}"
        elif t == "get_food":
            for animal in ("cow", "pig", "chicken", "sheep"):
                if InputController.abort_requested():
                    break
                if int(self._read_world().get("food", 20) or 20) >= 18:
                    break
                await self._hunt(animal, seconds=14)
            for raw in ("raw_beef", "raw_porkchop", "raw_chicken", "raw_mutton"):
                if self._inv_count(self._read_world(), raw) > 0:
                    self._chat(f"/wsmelt {raw} 6")
                    await self._wait_smelt(80)
            outcome = "get_food (hunted + cooked)"
        elif t == "get_wool":
            need = int(a.get("amount", 3) or 3)
            for _ in range(5):
                if InputController.abort_requested():
                    break
                if self._count_suffix(self._read_world(), "_wool") >= need:
                    break
                await self._hunt("sheep", seconds=14)
            have = self._count_suffix(self._read_world(), "_wool")
            outcome = f"get_wool: {have}/{need} wool"
        elif t == "make_bed":
            outcome = await self._do_make_bed(state)
        elif t == "fight":
            w = state["world"]
            foe = str(a.get("target") or w.get("threat") or w.get("hostile_type") or "").lower()
            if "creeper" in foe or "creeper" in str(w.get("hostile_type", "")).lower():
                self._chat("#stop"); time.sleep(0.2)
                dx, dz = random.choice([(12, 0), (-12, 0), (0, 12), (0, -12)])
                self._chat(f"#goto {int(w.get('x', 0)) + dx} ~ {int(w.get('z', 0)) + dz}")
                await self._wait_baritone_idle(max_sec=40)
                outcome = "fight: creeper nearby — backed off"
            elif foe:
                for _ in range(3):
                    if InputController.abort_requested():
                        break
                    self._chat(f"/whunt {foe} 12")
                    self._chat(f"#follow entity {foe}")
                    await self._idle(9)
                    self._chat("#stop"); time.sleep(0.3)
                    if int(self._read_world().get("hostiles", 0) or 0) == 0:
                        break
                self._chat("/wcollect 6")
                await self._idle(6.5)
                outcome = f"fight {foe}"
            else:
                await self._idle(3)
                outcome = "fight (mod auto-melees in reach)"
        elif t == "escape_water":
            self._chat("#stop"); time.sleep(0.2)
            self.ic.key_down("space"); self.ic.key_down("w")
            time.sleep(2.2)
            self.ic.key_up("w"); self.ic.key_up("space")
            self._water = 0
            outcome = "escape_water (swam to land)"
        elif t == "stock_up":
            plan = [(f"#mine {int(a.get('wood', 16))} {_LOGS}", 200),
                    ("#mine 24 cobblestone stone", 240),
                    ("#mine 8 coal_ore", 200)]
            for cmd, mx in plan:
                if InputController.abort_requested():
                    break
                self._chat(cmd)
                await self._wait_baritone_idle(max_sec=mx)
                self._chat("#stop"); time.sleep(0.3)
            outcome = "stock_up (wood+stone+coal)"
        elif t == "mine_diamonds":
            amt = int(a.get("amount", 8) or 8)
            w = state["world"]
            inv = w.get("inventory", {}) or {}
            coal = int(inv.get("coal", 0) or 0)
            torches = int(inv.get("torch", 0) or 0)
            if coal < 6 and torches < 12:
                self._chat("#mine 10 coal_ore deepslate_coal_ore")
                await self._wait_baritone_idle(max_sec=220)
                self._chat("#stop"); time.sleep(0.3)
            if torches < 12:
                self._chat("/wcraft torch 32")
                await self._idle(5)
            self._chat(f"#goto {int(w.get('x', 0) or 0)} -59 {int(w.get('z', 0) or 0)}")
            await self._wait_baritone_idle(max_sec=300)
            # at y-59 diamonds are the DEEPSLATE variant — must mine both names or it finds nothing
            self._chat(f"#mine {amt} diamond_ore deepslate_diamond_ore")
            await self._wait_baritone_idle(max_sec=400)
            outcome = f"mine_diamonds {amt} (coal+torch first)"
        elif t == "setup_base":
            self._chat("#stop"); time.sleep(0.3)
            for cmd in ("/wcraft chest", "/wplace chest", "/wplace bed"):
                if InputController.abort_requested():
                    break
                self._chat(cmd)
                await self._idle(3)
            outcome = "setup_base"
        elif t == "mine":
            blocks = str(a.get("blocks") or _LOGS)
            cnt = int(a.get("count", 16) or 16)
            self._chat(f"#mine {cnt} {blocks}")
            await self._wait_baritone_idle(max_sec=300)
        elif t == "goto":
            gx, gy, gz = int(a.get("x", 0) or 0), int(a.get("y", 64) or 64), int(a.get("z", 0) or 0)
            known = set()
            for key in ("crafting_table", "furnace", "home", "bed", "chest"):
                raw = state["world"].get(key)
                if raw:
                    try:
                        known.add(tuple(int(n) for n in str(raw).split(",")))
                    except ValueError:
                        pass
            if (gx, gy, gz) in known:
                gx += 1
            self._chat(f"#goto {gx} {gy} {gz}")
            await self._wait_baritone_idle(max_sec=180)
        elif t == "explore":
            self._chat("#explore")
            await self._idle(12)            # short slice then re-plan (so it can't swim far out to sea)
            self._chat("#stop")
        elif t == "build":
            # lock the shelter to a FIXED spot so building again (after gathering more planks)
            # RESUMES the same house instead of starting a new one wherever we now stand.
            if self._build_origin is None:
                w = state["world"]
                self._build_origin = (int(w.get("x", 0)), int(w.get("y", 64)), int(w.get("z", 0)))
            ox, oy, oz = self._build_origin
            self._chat(f"#build {a.get('file','wallie_house.schem')} {ox} {oy} {oz}")
            await self._wait_baritone_idle(max_sec=400)
        elif t == "place":
            self._chat("#stop"); time.sleep(0.3)
            item = str(a.get("item", "torch"))
            self._chat(f"/wplace {item}")
            await self._idle(2)
            if item == "bed":                       # place a bed, then actually sleep in it
                self._chat("/wsleep")
                await self._idle(4)
            outcome = f"place {item}"
        elif t == "sleep":
            self._chat("#stop"); time.sleep(0.3)
            self._chat("/wsleep")
            await self._idle(4)
            outcome = "sleep (bed)"
        elif t == "deposit":
            self._chat("#stop"); time.sleep(0.3)
            self._chat("/wdeposit")
            await self._idle(6)
            outcome = "deposit (stashed junk in chest)"
        elif t == "smelt":
            self._chat("#stop"); time.sleep(0.4)
            cnt = int(a.get("count", 8) or 8)
            self._chat(f"/wsmelt {a.get('item','raw_iron')} {cnt}")
            await self._wait_smelt(min(160, cnt * 12 + 20))
            outcome = f"smelt {a.get('item')}"
        elif t == "craft":
            item = str(a.get("item", "planks")).lower()
            cnt = int(a.get("count", 1) or 1)
            if item == "bed":
                return await self._do_make_bed(state)
            if item in ("furnace", "crafting_table") and self._known_pos(state["world"], item):
                return f"craft {item}: SKIPPED — you ALREADY built one; go to its position and reuse it"
            if item in ("torch", "candle"):
                coal = int((state["world"].get("inventory", {}) or {}).get("coal", 0) or 0)
                cnt = max(cnt, coal * 4 if coal else 32)          # batch: use the coal you have
            if self._is_singleton(item) and self._already_have(state["world"], item):
                return f"craft {item}: SKIPPED — already have one (check inventory/wearing)"
            self._chat("#stop"); time.sleep(0.4)
            if _needs_table(item):
                tbl = self._known_pos(state["world"], "crafting_table")
                if tbl:
                    self._chat(f"#goto {tbl[0] + 1} {tbl[1]} {tbl[2]}")
                    await self._wait_baritone_idle(max_sec=60)
                    self._chat("#stop"); time.sleep(0.3)
            self._chat(f"/wcraft {item} {cnt}")
            await self._idle(5)
            res = str(self._read_world().get("last_craft", "")).lower()
            table_fail = any(k in res for k in ("couldn't place", "no space", "obstruct", "didn't open", "no spot", "step over"))
            if _needs_table(item) and table_fail:
                w = state["world"]
                dx, dz = random.choice([(2, 0), (-2, 0), (0, 2), (0, -2), (3, 2), (-2, -3)])
                self._chat(f"#goto {int(w.get('x', 0)) + dx} ~ {int(w.get('z', 0)) + dz}")
                await self._wait_baritone_idle(max_sec=40)
                self._chat("#stop"); time.sleep(0.3)
                self._chat(f"/wcraft {item} {cnt}")
                await self._idle(5)
                res = str(self._read_world().get("last_craft", "")).lower()
            self._craft_fail = self._craft_fail + 1 if ("not enough" in res or "couldn't" in res) else 0
            outcome = f"craft {item} -> {self._read_world().get('last_craft', 'done')}"[:90]
        elif t == "stop":
            self._chat("#stop")
        else:  # wait
            await self._idle(float(a.get("seconds", 3) or 3))
        return outcome

    def _reflect(self, state: AgentState) -> dict:
        return {"step": state["step"] + 1}

    def _route(self, state: AgentState) -> str:
        if state.get("done"):
            logger.info("route: agent reported done"); return "end"
        if state["step"] >= self.max_steps:
            logger.info(f"route: hit max_steps ({self.max_steps})"); return "end"
        if InputController.abort_requested():
            logger.info("route: F8 abort"); return "end"
        return "loop"

    async def _idle(self, seconds: float) -> None:
        end = time.time() + seconds
        while time.time() < end:
            if InputController.abort_requested():
                return
            await asyncio.sleep(0.12)

    async def _wait_smelt(self, max_sec: float) -> str:
        """Wait for the furnace, but bail the MOMENT the mod reports done or an error — instead of
        freezing for the full smelt duration (which looked frozen, especially on a furnace error)."""
        end = time.time() + max_sec
        while time.time() < end:
            if InputController.abort_requested():
                return "aborted"
            res = str(self._read_world().get("last_craft", "")).lower()
            if "wsmelt" in res and ("done" in res or "no furnace" in res
                                    or "nowhere" in res or "didn't open" in res):
                return res
            await asyncio.sleep(1.5)
        return "timeout"

    def _build_graph(self):
        g = StateGraph(AgentState)
        g.add_node("observe", self._observe)
        g.add_node("plan", self._plan)
        g.add_node("act", self._act)
        g.add_node("reflect", self._reflect)
        g.set_entry_point("observe")
        g.add_edge("observe", "plan")
        g.add_edge("plan", "act")
        g.add_edge("act", "reflect")
        g.add_conditional_edges("reflect", self._route, {"loop": "observe", "end": END})
        return g.compile(checkpointer=MemorySaver())

    async def run(self) -> None:
        logger.info(f"WallieAgent: GOAL = {self.goal!r}  (F8 = stop)")
        self._setup()
        run_n = 0
        try:
            while not InputController.abort_requested():
                run_n += 1
                init: AgentState = {"goal": self.goal, "world": {}, "history": [],
                                    "action": {}, "step": 0, "done": False}
                cfg = {"configurable": {"thread_id": f"wallie-{run_n}"}, "recursion_limit": 100000}
                try:
                    final = await self.graph.ainvoke(init, cfg)
                except Exception as e:
                    logger.error(f"agent graph crashed ({type(e).__name__}: {str(e)[:160]}) — restarting")
                    self._chat("#stop"); await asyncio.sleep(2.0)
                    continue
                if final.get("done") or InputController.abort_requested():
                    break
                logger.warning("agent graph ended early (not done, no F8) — restarting to keep playing")
                await asyncio.sleep(1.0)
        finally:
            if self._prefetch_task is not None:
                self._prefetch_task.cancel()
            self.ic.release_all()
            logger.info("WallieAgent: stopped")

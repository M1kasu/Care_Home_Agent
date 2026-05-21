"""Persistent family member profile memory."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


PROFILE_FIELDS = ("personality", "hobbies", "diet", "notes")
TASTE_WORDS = ["清淡", "辣", "甜", "咸", "油腻", "鱼", "肉", "鸡", "蔬菜", "米饭", "面", "粥", "汤", "茶", "咖啡"]
PERSONALITY_WORDS = ["急", "慢热", "内向", "外向", "健谈", "安静", "节俭", "固执", "细心", "怕吵"]
NOTE_WORDS = ["怕冷", "怕热", "睡眠浅", "容易醒", "腿脚", "起夜"]


class FamilyProfileMemory:
    def __init__(self, db_path: str | None) -> None:
        self.db_path = db_path or ":memory:"
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS family_profiles (
                    member TEXT PRIMARY KEY,
                    personality TEXT NOT NULL DEFAULT '[]',
                    hobbies TEXT NOT NULL DEFAULT '[]',
                    diet TEXT NOT NULL DEFAULT '[]',
                    notes TEXT NOT NULL DEFAULT '[]',
                    updated_at TEXT NOT NULL
                )
                """
            )

    def load(self) -> dict[str, dict[str, list[str]]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT member, personality, hobbies, diet, notes FROM family_profiles ORDER BY member"
            ).fetchall()
        return {row["member"]: self._row_to_profile(row) for row in rows}

    def apply_to_state(self, state: dict[str, Any]) -> None:
        state["family_profiles"] = self.load()

    def remember_from_text(
        self,
        text: str,
        *,
        known_members: list[str],
        member_groups: dict[str, list[str]] | None = None,
    ) -> dict[str, Any]:
        targets = self._resolve_targets(text, known_members, member_groups or {})
        if not targets:
            return {"updated": [], "profiles": self.load(), "message": "没有识别到要记住的家庭成员"}

        updated: list[dict[str, Any]] = []
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as conn:
            for member in targets:
                current = self._load_member(conn, member)
                extracted = self._extract_facts(text, member)
                changed = self._merge_profile(current, extracted)
                if not any(changed.values()):
                    continue
                conn.execute(
                    """
                    INSERT INTO family_profiles(member, personality, hobbies, diet, notes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(member) DO UPDATE SET
                        personality=excluded.personality,
                        hobbies=excluded.hobbies,
                        diet=excluded.diet,
                        notes=excluded.notes,
                        updated_at=excluded.updated_at
                    """,
                    (
                        member,
                        json.dumps(current["personality"], ensure_ascii=False),
                        json.dumps(current["hobbies"], ensure_ascii=False),
                        json.dumps(current["diet"], ensure_ascii=False),
                        json.dumps(current["notes"], ensure_ascii=False),
                        now,
                    ),
                )
                updated.append({"member": member, "added": changed, "profile": current})
        profiles = self.load()
        return {
            "updated": updated,
            "profiles": profiles,
            "message": self._format_update_message(updated),
        }

    def query(self, member: str | None = None) -> dict[str, Any]:
        profiles = self.load()
        if member:
            profiles = {member: profiles.get(member, empty_profile())}
        return {"profiles": profiles, "message": self.format_profiles(profiles) or "还没有长期家庭画像"}

    @staticmethod
    def format_profiles(profiles: dict[str, dict[str, list[str]]]) -> str:
        lines = []
        for member, profile in profiles.items():
            parts = []
            if profile.get("personality"):
                parts.append("性格：" + "、".join(profile["personality"]))
            if profile.get("hobbies"):
                parts.append("爱好：" + "、".join(profile["hobbies"]))
            if profile.get("diet"):
                parts.append("饮食：" + "、".join(profile["diet"]))
            if profile.get("notes"):
                parts.append("备注：" + "、".join(profile["notes"]))
            if parts:
                lines.append(f"{member}：" + "；".join(parts))
        return "\n".join(lines)

    @staticmethod
    def _resolve_targets(
        text: str,
        known_members: list[str],
        member_groups: dict[str, list[str]],
    ) -> list[str]:
        targets: list[str] = []
        for group, members in member_groups.items():
            if group in text:
                targets.extend(members)
        alias_map = {"老人": ["爷爷", "奶奶"], "宝宝": ["孩子"], "小孩": ["孩子"], "儿子": ["孩子"], "女儿": ["孩子"]}
        for alias, members in alias_map.items():
            if alias in text:
                targets.extend([member for member in members if member in known_members])
        for member in known_members:
            if member in text:
                targets.append(member)
        return list(dict.fromkeys(targets))

    @staticmethod
    def _extract_facts(text: str, member: str) -> dict[str, list[str]]:
        cleaned = text.replace("记住", "").replace("以后", "").replace("请", "")
        cleaned = cleaned.replace(member, "")
        profile = empty_profile()

        for match in re.finditer(r"(?:性格|脾气)(?:是|比较|很|有点)?([^，。；,.!?！？]+)", cleaned):
            value = _clean_fact(match.group(1))
            if value:
                profile["personality"].append(value)
        for word in PERSONALITY_WORDS:
            if word in cleaned and not any(word in item for item in profile["personality"]):
                profile["personality"].append(word)

        negative_diet_patterns = [
            r"(?:不吃|不爱吃|不喜欢吃|不能吃)([^，。；,.!?！？]+)",
            r"([^，。；,.!?！？]+)(?:过敏|忌口)",
        ]
        for pattern in negative_diet_patterns:
            for match in re.finditer(pattern, cleaned):
                value = _clean_fact(match.group(0))
                if value:
                    profile["diet"].append(value)

        like_patterns = [
            r"(?:喜欢吃|爱吃|偏爱吃)([^，。；,.!?！？]+)",
            r"(?:喜欢|爱)([^，。；,.!?！？]+)",
        ]
        for pattern in like_patterns:
            for match in re.finditer(pattern, cleaned):
                value = _clean_fact(match.group(0))
                if not value:
                    continue
                if "吃" in value or any(word in value for word in TASTE_WORDS):
                    profile["diet"].append(value)
                else:
                    profile["hobbies"].append(value)

        for word in NOTE_WORDS:
            if word in cleaned:
                profile["notes"].append(word)

        return {field: _dedupe(values) for field, values in profile.items()}

    @staticmethod
    def _merge_profile(current: dict[str, list[str]], extracted: dict[str, list[str]]) -> dict[str, list[str]]:
        changed = empty_profile()
        for field in PROFILE_FIELDS:
            for item in extracted.get(field, []):
                if item and item not in current[field]:
                    current[field].append(item)
                    changed[field].append(item)
        return changed

    @staticmethod
    def _row_to_profile(row: sqlite3.Row) -> dict[str, list[str]]:
        profile = empty_profile()
        for field in PROFILE_FIELDS:
            try:
                values = json.loads(row[field] or "[]")
            except (TypeError, ValueError, json.JSONDecodeError):
                values = []
            cleaned = [str(item).strip() for item in values if str(item).strip()]
            if field == "personality":
                cleaned = [item[2:] if item.startswith("性格") else item for item in cleaned]
            profile[field] = cleaned
        return profile

    @staticmethod
    def _load_member(conn: sqlite3.Connection, member: str) -> dict[str, list[str]]:
        row = conn.execute(
            "SELECT member, personality, hobbies, diet, notes FROM family_profiles WHERE member = ?",
            (member,),
        ).fetchone()
        return FamilyProfileMemory._row_to_profile(row) if row else empty_profile()

    @staticmethod
    def _format_update_message(updated: list[dict[str, Any]]) -> str:
        if not updated:
            return "我没提取到新的家庭画像信息"
        lines = []
        for item in updated:
            member = item["member"]
            added = item["added"]
            parts = []
            if added.get("personality"):
                parts.append("性格：" + "、".join(added["personality"]))
            if added.get("hobbies"):
                parts.append("爱好：" + "、".join(added["hobbies"]))
            if added.get("diet"):
                parts.append("饮食：" + "、".join(added["diet"]))
            if added.get("notes"):
                parts.append("备注：" + "、".join(added["notes"]))
            lines.append(f"{member}（" + "；".join(parts) + "）")
        return "已记住：" + "；".join(lines)


def empty_profile() -> dict[str, list[str]]:
    return {field: [] for field in PROFILE_FIELDS}


def _clean_fact(value: str) -> str:
    value = re.sub(r"^(，|。|；|,|\.|;)+", "", value.strip())
    value = value.strip(" 的。；，,.!?！？")
    value = value.replace("他", "").replace("她", "").strip()
    return value[:40]


def _dedupe(values: list[str]) -> list[str]:
    out = []
    for value in values:
        if value and value not in out:
            out.append(value)
    return out

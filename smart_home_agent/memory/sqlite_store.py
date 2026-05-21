"""SQLite-backed local knowledge retrieval for the edge demo."""

from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from typing import Any, Callable


DEFAULT_KNOWLEDGE = [
    {
        "title": "老人睡前饮品建议",
        "tags": "老人 健康 睡前 浓茶 饮水",
        "content": "老人睡前不建议饮用浓茶、咖啡等刺激性饮品，可能影响睡眠和夜间心率。可以换成温水。该建议仅供日常健康管理参考，不替代医疗诊断。",
    },
    {
        "title": "空调睡眠模式说明",
        "tags": "空调 睡眠模式 温度 老人房 主卧",
        "content": "空调睡眠模式通常会降低风速并逐步调整温度。老人房夜间建议保持 26 度左右，并保留 10% 夜灯亮度。",
    },
    {
        "title": "家庭 Wi-Fi 卡顿排查",
        "tags": "Wi-Fi 网络 视频 卡顿 Mesh QoS",
        "content": "视频卡顿优先检查 RSSI、延迟、丢包率、Mesh 节点距离和高带宽设备。老人房视频通话可以临时开启 QoS 优先策略。",
    },
    {
        "title": "睡前模式家庭规则",
        "tags": "睡前 模式 门锁 电视 灯光",
        "content": "睡前模式会关闭客厅电视，调暗公共区域灯光，将卧室空调切到睡眠模式，并检查门锁和老人吃药提醒。",
    },
    {
        "title": "门锁安全策略",
        "tags": "门锁 安全 确认 解锁",
        "content": "查询门锁和上锁可以直接执行；解锁、关闭摄像头、取消告警等敏感动作必须二次确认。",
    },
    {
        "title": "儿童用眼护眼建议",
        "tags": "儿童 用眼 护眼 学习 灯光",
        "content": "儿童连续学习不超过 45 分钟，建议远眺 5 分钟。学习时灯光亮度建议 70%-85%，色温 4000K，避免顶灯直射屏幕。",
    },
    {
        "title": "家庭节电小贴士",
        "tags": "节电 节能 待机 空调 ECO",
        "content": "空调每调高 1℃ 可节电约 7%；电视、机顶盒等长时间不用建议拔插或使用智能插座；夜间空调切 ECO/睡眠模式。",
    },
    {
        "title": "空气质量与通风建议",
        "tags": "空气 通风 PM2.5 CO2 湿度",
        "content": "室内 CO2 超过 1000ppm 建议开窗通风 10-15 分钟；湿度建议保持 40%-60%；雾霾天关闭窗户并开启新风/空气净化器。",
    },
    {
        "title": "老人防跌倒注意事项",
        "tags": "老人 跌倒 安全 夜灯 卫生间",
        "content": "老人房及通向卫生间的过道夜间保留 10%-20% 夜灯；卫生间铺防滑垫；起夜时建议先坐起 30 秒再站立。",
    },
    {
        "title": "儿童上网与屏幕时间",
        "tags": "儿童 上网 屏幕时间 平板 限时",
        "content": "学龄儿童每日累计屏幕时间建议不超过 1 小时；可在路由器设置儿童设备的访问时段，并对娱乐应用设定使用配额。",
    },
    {
        "title": "家庭应急联系方式模板",
        "tags": "应急 联系 报警 急救",
        "content": "家庭应急包应包括：物业 24 小时电话、社区医生、紧急联系人 2 名、宠物医院（如有）、燃气/水电报修。建议贴在玄关。",
    },
    {
        "title": "Wi-Fi Mesh 部署建议",
        "tags": "Mesh Wi-Fi 部署 节点 信号",
        "content": "Mesh 节点之间间距建议 8-12 米，回传信号 RSSI 优于 -65 dBm；老人房可单独增设节点保障视频通话稳定。",
    },
    {
        "title": "夜间空调温度建议",
        "tags": "空调 夜间 温度 健康",
        "content": "夜间室温建议 24-26℃；老人房可略高（26-27℃），儿童房保持 25-26℃；睡眠模式下风速调低、避免直吹。",
    },
    {
        "title": "家庭防火与燃气安全",
        "tags": "防火 燃气 安全 烟感",
        "content": "厨房应配备烟感和燃气泄漏报警器，定期检查燃气软管；离家前确认燃气阀门关闭，可联动离家模式自动检查。",
    },
    {
        "title": "智能门锁使用规范",
        "tags": "门锁 指纹 临时密码 安全",
        "content": "建议为家政、访客创建独立的临时密码并设置有效期；远程解锁需家人二次确认；指纹/密码每 3 个月更新一次。",
    },
]

GENERIC_CONTEXT_KEYWORDS = {"老人", "爷爷", "奶奶", "儿童", "孩子", "家庭", "家里", "睡前", "安全"}
DISTINCTIVE_KEYWORDS = {
    "浓茶",
    "喝茶",
    "咖啡",
    "饮水",
    "空调",
    "睡眠模式",
    "wifi",
    "网络",
    "视频",
    "卡顿",
    "mesh",
    "qos",
    "门锁",
    "解锁",
    "提醒",
    "护眼",
    "用眼",
    "学习",
    "节电",
    "节能",
    "待机",
    "空气",
    "通风",
    "pm2.5",
    "co2",
    "湿度",
    "跌倒",
    "夜灯",
    "屏幕",
    "应急",
    "燃气",
    "烟感",
    "临时密码",
}


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class SQLiteKnowledgeBase:
    def __init__(
        self,
        db_path: str | None,
        embedder: Callable[[list[str]], list[list[float]] | None] | None = None,
    ) -> None:
        self.db_path = db_path or ":memory:"
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._embedder = embedder
        self._embeddings_ready = False
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT
                )
                """
            )
            # 兼容旧数据库：缺列时补一列
            cols = {row[1] for row in conn.execute("PRAGMA table_info(knowledge)").fetchall()}
            if "embedding" not in cols:
                conn.execute("ALTER TABLE knowledge ADD COLUMN embedding TEXT")
            count = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
            if count == 0:
                conn.executemany(
                    "INSERT INTO knowledge(title, tags, content) VALUES(:title, :tags, :content)",
                    DEFAULT_KNOWLEDGE,
                )
            else:
                existing = {row[0] for row in conn.execute("SELECT title FROM knowledge").fetchall()}
                missing = [item for item in DEFAULT_KNOWLEDGE if item["title"] not in existing]
                if missing:
                    conn.executemany(
                        "INSERT INTO knowledge(title, tags, content) VALUES(:title, :tags, :content)",
                        missing,
                    )

    def _build_embeddings(self) -> None:
        if self._embeddings_ready or self._embedder is None:
            return
        with self._connect() as conn:
            rows = conn.execute("SELECT id, title, tags, content, embedding FROM knowledge").fetchall()
            pending = [row for row in rows if not row["embedding"]]
            if not pending:
                self._embeddings_ready = True
                return
            texts = [f"{row['title']} {row['tags']} {row['content']}" for row in pending]
            vectors = self._embedder(texts)
            if not vectors or len(vectors) != len(pending):
                # 嵌入失败，退化为关键词搜索
                self._embedder = None
                return
            for row, vec in zip(pending, vectors):
                conn.execute(
                    "UPDATE knowledge SET embedding = ? WHERE id = ?",
                    (json.dumps(vec), row["id"]),
                )
        self._embeddings_ready = True

    def _semantic_search(self, query: str, top_k: int) -> list[dict[str, Any]] | None:
        if self._embedder is None:
            return None
        self._build_embeddings()
        if not self._embeddings_ready or self._embedder is None:
            return None
        vec_q = self._embedder([query])
        if not vec_q:
            return None
        q_vec = vec_q[0]
        with self._connect() as conn:
            rows = conn.execute("SELECT id, title, tags, content, embedding FROM knowledge").fetchall()
        scored: list[tuple[float, sqlite3.Row]] = []
        for row in rows:
            if not row["embedding"]:
                continue
            try:
                vec = json.loads(row["embedding"])
            except (TypeError, ValueError):
                continue
            score = _cosine(q_vec, vec)
            if score >= 0.35:
                scored.append((score, row))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "tags": row["tags"].split(),
                "content": row["content"],
                "score": round(float(score), 4),
                "source": "embedding",
            }
            for score, row in scored[:top_k]
        ]

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        # 先尝试 embedding 语义搜索；失败/无结果则回退到关键词
        semantic = self._semantic_search(query, top_k)
        if semantic:
            return semantic
        keywords = self._keywords(query)
        if not keywords or not self._has_distinctive_keyword(keywords):
            return []
        with self._connect() as conn:
            rows = conn.execute("SELECT id, title, tags, content FROM knowledge").fetchall()
        scored: list[tuple[int, sqlite3.Row]] = []
        for row in rows:
            title = row["title"].lower()
            tags = row["tags"].lower()
            content = row["content"].lower()
            haystack = f"{title} {tags} {content}"
            matched = [kw for kw in keywords if kw in haystack]
            if not matched or not self._has_distinctive_keyword(matched):
                continue
            score = 0
            for kw in matched:
                if kw in title:
                    score += 4
                if kw in tags:
                    score += 3
                if kw in content:
                    score += 1
            if score >= 4:
                scored.append((score, row))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "tags": row["tags"].split(),
                "content": row["content"],
                "score": score,
                "source": "keyword",
                "matched_keywords": [kw for kw in keywords if kw in f"{row['title']} {row['tags']} {row['content']}".lower()],
            }
            for score, row in scored[:top_k]
        ]

    @staticmethod
    def _keywords(query: str) -> list[str]:
        normalized = query.lower().replace("wi-fi", "wifi").replace(" ", "")
        candidates = [
            "老人",
            "爷爷",
            "奶奶",
            "睡前",
            "浓茶",
            "喝茶",
            "空调",
            "睡眠",
            "wifi",
            "网络",
            "视频",
            "卡顿",
            "mesh",
            "qos",
            "门锁",
            "安全",
            "解锁",
            "提醒",
            "护眼",
            "用眼",
            "学习",
            "节电",
            "节能",
            "待机",
            "空气",
            "通风",
            "跌倒",
            "屏幕",
            "应急",
            "咖啡",
            "饮水",
            "睡眠模式",
            "pm2.5",
            "co2",
            "夜灯",
            "燃气",
            "烟感",
            "临时密码",
        ]
        hits = [word for word in candidates if word in normalized]
        return hits

    @staticmethod
    def _has_distinctive_keyword(keywords: list[str]) -> bool:
        return any(kw not in GENERIC_CONTEXT_KEYWORDS or kw in DISTINCTIVE_KEYWORDS for kw in keywords)

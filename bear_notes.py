"""
Bear Notes — SQLiteデータベースからメモを取得するモジュール

macOS の Bear アプリのDBを直接読み込む。
タグ指定またはキーワード検索でメモを絞り込める。
"""

import sqlite3
from pathlib import Path

BEAR_DB = Path.home() / "Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/database.sqlite"


def _connect() -> sqlite3.Connection | None:
    if not BEAR_DB.exists():
        return None
    conn = sqlite3.connect(f"file:{BEAR_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def search(query: str, limit: int = 10) -> list[dict]:
    """キーワードでメモ全文を検索する。"""
    conn = _connect()
    if conn is None:
        return []
    try:
        rows = conn.execute(
            """
            SELECT ZTITLE, ZTEXT
            FROM ZSFNOTE
            WHERE ZTRASHED = 0
              AND ZENCRYPTED = 0
              AND (ZTITLE LIKE ? OR ZTEXT LIKE ?)
            ORDER BY ZMODIFICATIONDATE DESC
            LIMIT ?
            """,
            (f"%{query}%", f"%{query}%", limit),
        ).fetchall()
        return [{"title": r["ZTITLE"] or "(無題)", "text": r["ZTEXT"] or ""} for r in rows]
    finally:
        conn.close()


def get_by_tag(tag: str, limit: int = 20) -> list[dict]:
    """タグ名でメモを取得する（Bear タグ形式: #tag）。"""
    conn = _connect()
    if conn is None:
        return []
    try:
        rows = conn.execute(
            """
            SELECT N.ZTITLE, N.ZTEXT
            FROM ZSFNOTE N
            JOIN Z_5TAGS NT ON NT.Z_5NOTES = N.Z_PK
            JOIN ZSFNOTETAG T ON T.Z_PK = NT.Z_13TAGS
            WHERE N.ZTRASHED = 0
              AND N.ZENCRYPTED = 0
              AND T.ZTITLE = ?
            ORDER BY N.ZMODIFICATIONDATE DESC
            LIMIT ?
            """,
            (tag.lstrip("#"), limit),
        ).fetchall()
        return [{"title": r["ZTITLE"] or "(無題)", "text": r["ZTEXT"] or ""} for r in rows]
    finally:
        conn.close()


def load_for_knowledge(tags: list[str] | None = None, query: str | None = None) -> str:
    """
    Bear メモをナレッジベース形式の文字列に変換して返す。
    tags と query の両方が None の場合は空文字列を返す。
    """
    notes: list[dict] = []

    if tags:
        seen: set[str] = set()
        for tag in tags:
            for note in get_by_tag(tag):
                key = note["title"]
                if key not in seen:
                    seen.add(key)
                    notes.append(note)

    if query:
        seen_titles = {n["title"] for n in notes}
        for note in search(query):
            if note["title"] not in seen_titles:
                notes.append(note)

    if not notes:
        return ""

    sections = [f"### {n['title']}\n{n['text']}" for n in notes]
    joined = "\n\n---\n\n".join(sections)
    return (
        "## Bear メモ（関連ノート）\n"
        "以下は Bear から取得した関連メモです。\n\n"
        + joined
    )


def is_available() -> bool:
    return BEAR_DB.exists()

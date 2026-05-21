"""
Knowledge Base — ファイル読み込みモジュール

knowledge/ フォルダに置いた PDF・PPT・PPTX・TXT ファイルを自動で読み込み、
エージェントチームの前提知識として提供する。
Bear メモも tags/query で追加できる。
"""

import os
from pathlib import Path
import bear_notes

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

SUPPORTED = {".pdf", ".ppt", ".pptx", ".txt", ".md"}


def _read_pdf(path: Path) -> str:
    try:
        import fitz  # pymupdf
        doc = fitz.open(path)
        pages = [doc[i].get_text() for i in range(len(doc))]
        doc.close()
        return "\n\n".join(p for p in pages if p.strip())
    except Exception as e:
        return f"[PDF読み込みエラー: {e}]"


def _read_ppt(path: Path) -> str:
    try:
        from pptx import Presentation
        prs = Presentation(path)
        slides = []
        for i, slide in enumerate(prs.slides, 1):
            texts = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        line = para.text.strip()
                        if line:
                            texts.append(line)
            if texts:
                slides.append(f"[スライド {i}]\n" + "\n".join(texts))
        return "\n\n".join(slides)
    except Exception as e:
        return f"[PPT読み込みエラー: {e}]"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"[テキスト読み込みエラー: {e}]"


def load(bear_tags: list[str] | None = None, bear_query: str | None = None) -> str:
    """
    knowledge/ フォルダ内の全ファイルを読み込み、エージェントに渡す文字列を返す。
    bear_tags / bear_query を指定すると Bear メモも追加される。
    """
    if not KNOWLEDGE_DIR.exists():
        return ""

    files = sorted(
        f for f in KNOWLEDGE_DIR.rglob("*")
        if f.is_file() and f.suffix.lower() in SUPPORTED
    )

    if not files:
        return ""

    sections = []
    for f in files:
        ext = f.suffix.lower()
        if ext == ".pdf":
            content = _read_pdf(f)
        elif ext in {".ppt", ".pptx"}:
            content = _read_ppt(f)
        else:
            content = _read_text(f)

        if content.strip():
            label = f.relative_to(KNOWLEDGE_DIR)
            sections.append(f"### {label}\n{content}")

    bear_section = bear_notes.load_for_knowledge(tags=bear_tags, query=bear_query)
    if bear_section:
        sections.append(bear_section)

    if not sections:
        return ""

    joined = "\n\n---\n\n".join(sections)
    return (
        "## チーム共有ナレッジ\n"
        "以下はプロジェクトの前提知識として全メンバーに共有されている資料です。\n"
        "回答の際にこの内容を参照・活用してください。\n\n"
        + joined
    )


def summary() -> str:
    """読み込んだファイルの一覧を返す（起動時の確認用）。"""
    lines = []

    if not KNOWLEDGE_DIR.exists():
        lines.append("knowledge/ フォルダが存在しません。")
    else:
        files = sorted(
            f for f in KNOWLEDGE_DIR.rglob("*")
            if f.is_file() and f.suffix.lower() in SUPPORTED
        )
        if not files:
            lines.append("knowledge/ フォルダにファイルがありません。")
        else:
            lines.append("読み込み済みファイル:")
            lines += [f"  - {f.relative_to(KNOWLEDGE_DIR)}" for f in files]

    if bear_notes.is_available():
        lines.append("Bear: 利用可能（bear_tags / bear_query で検索可能）")
    else:
        lines.append("Bear: 未検出（macOS の Bear アプリが必要）")

    return "\n".join(lines)

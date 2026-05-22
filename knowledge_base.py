"""
Knowledge Base — ファイル読み込みモジュール

knowledge/ フォルダに置いた PDF・PPT・PPTX・TXT ファイルを読み込み、
エージェントチームの前提知識として提供する。
Bear メモも tags/query で追加できる。

_index.json があれば brief のキーワードに応じてロード対象を絞り込む。
"""

import json
import re
from pathlib import Path
import bear_notes

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
INDEX_FILE = KNOWLEDGE_DIR / "_index.json"

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


def _read_path(path: Path) -> list[tuple[str, str]]:
    """パスがファイルならそれを、ディレクトリなら中のファイルを読んで (label, content) リストを返す。"""
    results = []
    targets = (
        sorted(f for f in path.rglob("*") if f.is_file() and f.suffix.lower() in SUPPORTED)
        if path.is_dir()
        else ([path] if path.is_file() and path.suffix.lower() in SUPPORTED else [])
    )
    for f in targets:
        ext = f.suffix.lower()
        if ext == ".pdf":
            content = _read_pdf(f)
        elif ext in {".ppt", ".pptx"}:
            content = _read_ppt(f)
        else:
            content = _read_text(f)
        if content.strip():
            label = f.relative_to(KNOWLEDGE_DIR)
            results.append((str(label), content))
    return results


def _brief_matches(brief: str, tags: list[str]) -> bool:
    """ブリーフのテキストに tags のいずれかが含まれるか（大文字小文字・記号無視）。"""
    brief_lower = brief.lower()
    return any(tag.lower() in brief_lower for tag in tags)


def _select_paths(brief: str | None) -> list[Path]:
    """
    _index.json を読み、ブリーフに応じてロードするパスを選択して返す。
    インデックスがなければ全ファイルを対象とする。
    """
    if not INDEX_FILE.exists() or brief is None:
        return _all_paths()

    try:
        index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except Exception:
        return _all_paths()

    selected: list[Path] = []
    indexed_paths: set[str] = set()

    for entry in index.get("entries", []):
        p = entry.get("path", "")
        if not p:
            continue
        indexed_paths.add(p)
        full = KNOWLEDGE_DIR / p
        if not full.exists():
            continue
        if entry.get("always"):
            selected.append(full)
        elif _brief_matches(brief, entry.get("tags", [])):
            selected.append(full)

    # インデックスに記載のないファイル/ディレクトリは常にロード（後方互換）
    for item in sorted(KNOWLEDGE_DIR.iterdir()):
        if item.name.startswith("_") or item.name in indexed_paths:
            continue
        selected.append(item)

    return selected


def _all_paths() -> list[Path]:
    """インデックスなし: _index.json 以外の全パスを返す。"""
    return sorted(
        p for p in KNOWLEDGE_DIR.iterdir()
        if not p.name.startswith("_")
    )


def load(
    brief: str | None = None,
    bear_tags: list[str] | None = None,
    bear_query: str | None = None,
) -> str:
    """
    knowledge/ フォルダ内のファイルを読み込み、エージェントに渡す文字列を返す。
    brief を渡すと _index.json に基づいて関連ファイルだけを選択ロードする。
    bear_tags / bear_query を指定すると Bear メモも追加される。
    """
    if not KNOWLEDGE_DIR.exists():
        return ""

    paths = _select_paths(brief)
    sections: list[str] = []
    for p in paths:
        for label, content in _read_path(p):
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


def summary(brief: str | None = None) -> str:
    """ロード対象ファイルの一覧を返す（起動時の確認用）。"""
    lines = []

    if not KNOWLEDGE_DIR.exists():
        lines.append("knowledge/ フォルダが存在しません。")
        return "\n".join(lines)

    paths = _select_paths(brief)
    file_list: list[Path] = []
    for p in paths:
        if p.is_dir():
            file_list += sorted(
                f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in SUPPORTED
            )
        elif p.is_file() and p.suffix.lower() in SUPPORTED:
            file_list.append(p)

    if not file_list:
        lines.append("knowledge/ フォルダにファイルがありません。")
    else:
        label = f"ロード対象ファイル（{'ブリーフ絞り込み済み' if brief else '全件'}）:"
        lines.append(label)
        lines += [f"  - {f.relative_to(KNOWLEDGE_DIR)}" for f in file_list]

    if bear_notes.is_available():
        lines.append("Bear: 利用可能（bear_tags / bear_query で検索可能）")
    else:
        lines.append("Bear: 未検出（macOS の Bear アプリが必要）")

    return "\n".join(lines)

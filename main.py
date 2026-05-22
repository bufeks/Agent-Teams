"""
Creative Agency Team — ECD Demo

使い方:
  python main.py "ブリーフテキスト"          # テキストブリーフ
  python main.py --file オリエン.pdf          # ファイルをブリーフとして使用
  python main.py --file オリエン.pdf "補足"  # ファイル + 追加指示
  python main.py                              # デモブリーフ（最初の1件）
"""

import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

import knowledge_base
from agent_team import CreativeTeam

OUTPUT_DIR = Path(__file__).parent / "output"
THEORY_DIR = Path(__file__).parent / "knowledge" / "宮崎太郎のクリエイティブ論"

SUPPORTED_BRIEF_EXTS = {".pdf", ".ppt", ".pptx", ".txt", ".md"}


def _read_brief_file(path: Path) -> str:
    """オリエン資料ファイルを読んでテキストに変換する。"""
    ext = path.suffix.lower()
    if ext == ".pdf":
        return knowledge_base._read_pdf(path)
    elif ext in {".ppt", ".pptx"}:
        return knowledge_base._read_ppt(path)
    elif ext in {".txt", ".md"}:
        return knowledge_base._read_text(path)
    else:
        print(f"Warning: 未対応の拡張子です: {ext}。テキストとして読み込みます。")
        return knowledge_base._read_text(path)


def _md_to_html_body(text: str) -> str:
    import html as h
    t = h.escape(text)
    t = re.sub(r"^#{4} (.+)$", r"<h4>\1</h4>", t, flags=re.MULTILINE)
    t = re.sub(r"^#{3} (.+)$", r"<h3>\1</h3>", t, flags=re.MULTILINE)
    t = re.sub(r"^#{2} (.+)$", r"<h2>\1</h2>", t, flags=re.MULTILINE)
    t = re.sub(r"^# (.+)$",    r"<h1>\1</h1>", t, flags=re.MULTILINE)
    t = re.sub(r"^> (.+)$", r"<blockquote>\1</blockquote>", t, flags=re.MULTILINE)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    t = re.sub(r"^\|(.+)\|$", lambda m: "<tr>" + "".join(
        f"<td>{c.strip()}</td>" for c in m.group(1).split("|")
    ) + "</tr>", t, flags=re.MULTILINE)
    t = re.sub(r"(<tr>.*?</tr>\n?)+", lambda m: f"<table>{m.group()}</table>", t, flags=re.DOTALL)
    t = re.sub(r"<tr><td>-+</td>.*?</tr>", "", t)
    t = re.sub(r"^[-•] (.+)$", r"<li>\1</li>", t, flags=re.MULTILINE)
    t = re.sub(r"(<li>.*?</li>\n?)+", lambda m: f"<ul>{m.group()}</ul>", t, flags=re.DOTALL)
    t = re.sub(r"^---+$", r"<hr>", t, flags=re.MULTILINE)
    t = re.sub(r"\n{2,}", "</p><p>", t)
    t = re.sub(r"\n", "<br>", t)
    return f"<p>{t}</p>"


def generate_theory_html() -> Path:
    """宮崎太郎のクリエイティブ論を HTML に変換して output/ に保存する。"""
    import html as h

    if not THEORY_DIR.exists():
        print("Error: 理論ディレクトリが見つかりません。")
        sys.exit(1)

    updated_at = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    def read_md(path: Path) -> str:
        return path.read_text(encoding="utf-8") if path.exists() else ""

    overview = read_md(THEORY_DIR / "_overview.md")

    principles = sorted((THEORY_DIR / "原則").glob("*.md")) if (THEORY_DIR / "原則").exists() else []
    logs = sorted((THEORY_DIR / "発見ログ").glob("*.md"), reverse=True) if (THEORY_DIR / "発見ログ").exists() else []

    principle_sections = ""
    for p in principles:
        text = read_md(p)
        # タイトルを抽出
        title_match = re.search(r"^# (.+)$", text, re.MULTILINE)
        title = title_match.group(1) if title_match else p.stem
        principle_sections += f"""
        <section class="principle">
            <div class="principle-body">{_md_to_html_body(text)}</div>
        </section>"""

    log_sections = ""
    for l in logs:
        text = read_md(l)
        log_sections += f"""
        <section class="log">
            <div class="log-body">{_md_to_html_body(text)}</div>
        </section>"""

    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>宮崎太郎のクリエイティブ論</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --ink: #1a1a1a;
    --bg: #f7f6f2;
    --paper: #ffffff;
    --accent: #c0392b;
    --muted: #888;
    --border: #e0ddd8;
  }}
  body {{ font-family: "Hiragino Mincho ProN", "Yu Mincho", Georgia, serif;
         background: var(--bg); color: var(--ink); line-height: 1.9; font-size: 16px; }}
  .page {{ max-width: 820px; margin: 0 auto; padding: 80px 32px; }}

  /* Cover */
  .cover {{ text-align: center; padding: 80px 0 100px; border-bottom: 1px solid var(--border); margin-bottom: 80px; }}
  .cover-label {{ font-family: "Hiragino Sans", sans-serif; font-size: .7rem; letter-spacing: .3em;
                  color: var(--muted); text-transform: uppercase; margin-bottom: 24px; }}
  .cover h1 {{ font-size: 2.6rem; font-weight: 400; letter-spacing: .08em; line-height: 1.4; margin-bottom: 16px; }}
  .cover .byline {{ font-size: .85rem; color: var(--muted); letter-spacing: .12em; }}
  .cover .updated {{ font-size: .75rem; color: var(--muted); margin-top: 8px; }}

  /* Overview */
  .overview {{ margin-bottom: 80px; padding-bottom: 60px; border-bottom: 1px solid var(--border); }}
  .overview h1 {{ display: none; }}

  /* Chapter */
  .chapter-label {{ font-family: "Hiragino Sans", sans-serif; font-size: .68rem;
                    letter-spacing: .25em; color: var(--accent); text-transform: uppercase;
                    margin-bottom: 40px; padding-bottom: 12px; border-bottom: 2px solid var(--accent); }}

  /* Principle */
  .principle {{ margin-bottom: 60px; padding-bottom: 60px; border-bottom: 1px solid var(--border); }}
  .principle:last-child {{ border-bottom: none; }}

  /* Log */
  .log {{ margin-bottom: 48px; padding-bottom: 48px; border-bottom: 1px solid var(--border); }}
  .log:last-child {{ border-bottom: none; }}

  /* Typography */
  h1 {{ font-size: 1.7rem; font-weight: 400; margin: 1.4em 0 .6em; line-height: 1.5; }}
  h2 {{ font-size: 1.15rem; font-weight: 700; font-family: "Hiragino Sans", sans-serif;
        margin: 1.6em 0 .5em; padding-bottom: 6px; border-bottom: 1px solid var(--border); }}
  h3 {{ font-size: 1rem; font-weight: 700; font-family: "Hiragino Sans", sans-serif;
        margin: 1.4em 0 .4em; color: #333; }}
  h4 {{ font-size: .9rem; font-weight: 700; font-family: "Hiragino Sans", sans-serif;
        margin: 1.2em 0 .3em; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; }}
  p {{ margin: .8em 0; }}
  blockquote {{ border-left: 3px solid var(--accent); padding: 4px 0 4px 20px;
                color: #555; font-style: italic; margin: 1em 0; }}
  ul {{ padding-left: 1.4em; margin: .6em 0; }}
  li {{ margin-bottom: .4em; }}
  strong {{ font-weight: 700; }}
  em {{ font-style: italic; }}
  code {{ font-family: monospace; background: #f0ede8; padding: 2px 6px; border-radius: 3px; font-size: .85em; }}
  hr {{ border: none; border-top: 1px solid var(--border); margin: 2em 0; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1em 0; font-size: .88rem; font-family: "Hiragino Sans", sans-serif; }}
  td {{ border: 1px solid var(--border); padding: 10px 14px; vertical-align: top; }}
  tr:nth-child(even) td {{ background: #faf9f6; }}
  tr:first-child td {{ background: #f0ede8; font-weight: 700; }}
</style>
</head>
<body>
<div class="page">

  <div class="cover">
    <div class="cover-label">Creative Theory</div>
    <h1>宮崎太郎の<br>クリエイティブ論</h1>
    <div class="byline">Taro Miyazaki — kiCk inc. ECD</div>
    <div class="updated">最終更新：{updated_at}</div>
  </div>

  <div class="overview">
    {_md_to_html_body(overview)}
  </div>

  <div class="chapter-label">Principles — 原則</div>
  {principle_sections}

  <div class="chapter-label" style="margin-top:80px;">Discovery Log — 発見ログ</div>
  {log_sections}

</div>
</body>
</html>"""

    OUTPUT_DIR.mkdir(exist_ok=True)
    out = OUTPUT_DIR / "theory.html"
    out.write_text(html_content, encoding="utf-8")
    return out


def _save_html(result, brief: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    slug = re.sub(r"[^\w぀-鿿]", "_", brief[:30]).strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"{timestamp}_{slug}.html"
    path.write_text(result.to_html(), encoding="utf-8")
    return path


load_dotenv()

DEMO_BRIEFS = [
    {
        "name": "新製品ローンチ",
        "brief": (
            "日本発のサステナブルなスポーツウェアブランド『SHIZEN』の"
            "グローバルローンチキャンペーンを開発せよ。"
            "ターゲットは都市在住の25〜38歳のアクティブ層。"
            "競合はNike、Patagoniaだが、我々は'自然と競うのではなく、自然とともに動く'という"
            "哲学を持つ。ブランドの世界観、クリエイティブコンセプト、"
            "ヒーローコピー、ビジュアル方向性を提示せよ。"
        ),
    },
    {
        "name": "ブランドリポジショニング",
        "brief": (
            "創業100年の老舗醤油メーカー『山田醤油』を"
            "Z世代にも愛されるブランドにリポジショニングしたい。"
            "伝統と革新のバランスをとりながら、"
            "フードカルチャーの文脈で語れるクリエイティブ戦略を構築せよ。"
        ),
    },
    {
        "name": "社会課題キャンペーン",
        "brief": (
            "日本の若者の孤独問題をテーマにした、"
            "通信会社のブランドパーパスキャンペーンを開発せよ。"
            "商品訴求ではなく、社会とのつながりを取り戻すための"
            "ムーブメントを起こすことが目標。"
            "カンヌライオンズを獲れるレベルの仕事を目指せ。"
        ),
    },
]


def run_demo(brief_index: int | None = None) -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY が未設定です。.env.example を .env にコピーしてAPIキーを設定してください。")
        sys.exit(1)

    print(knowledge_base.summary())
    team = CreativeTeam(api_key=api_key)

    briefs_to_run = [DEMO_BRIEFS[brief_index]] if brief_index is not None else DEMO_BRIEFS

    for demo in briefs_to_run:
        print(f"\n{'#'*60}")
        print(f"# Campaign: {demo['name']}")
        print(f"{'#'*60}")

        result = team.run(demo["brief"], verbose=True)
        path = _save_html(result, demo["name"])
        print(f"\n出力: {path}")
        print()


def run_custom(brief: str) -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY が未設定です。")
        sys.exit(1)

    print(knowledge_base.summary())
    team = CreativeTeam(api_key=api_key)
    result = team.run(brief, verbose=True)
    path = _save_html(result, brief)
    print(f"\n出力: {path}")


def _parse_args(argv: list[str]) -> str | None:
    """
    引数を解析してブリーフ文字列を返す。
    --file / -f <path> [追加テキスト] に対応。
    """
    if not argv:
        return None

    if argv[0] in ("--file", "-f"):
        if len(argv) < 2:
            print("Error: --file の後にファイルパスを指定してください。")
            sys.exit(1)
        file_path = Path(argv[1])
        if not file_path.exists():
            print(f"Error: ファイルが見つかりません: {file_path}")
            sys.exit(1)
        print(f"オリエン資料を読み込み中: {file_path.name}")
        brief = _read_brief_file(file_path)
        if not brief.strip():
            print(f"Error: ファイルからテキストを抽出できませんでした: {file_path}")
            sys.exit(1)
        extra = " ".join(argv[2:])
        if extra:
            brief = f"{brief}\n\n【追加指示】\n{extra}"
        return brief

    return " ".join(argv)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--theory":
        path = generate_theory_html()
        print(f"理論書HTML: {path}")
    elif args:
        brief = _parse_args(args)
        run_custom(brief)
    else:
        # デフォルトは最初のブリーフのみ実行（コスト節約のため）
        run_demo(brief_index=0)

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
    if args:
        brief = _parse_args(args)
        run_custom(brief)
    else:
        # デフォルトは最初のブリーフのみ実行（コスト節約のため）
        run_demo(brief_index=0)

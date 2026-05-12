"""
Creative Agency Team — ECD Demo

The ECD (you) leads a full creative team:
CD, Strategic Planner, CopyWriter, Planner, Researcher, Art Director.

Run a preset brief or pass your own as a command-line argument.
"""

import os
import sys

from dotenv import load_dotenv

import knowledge_base
from agent_team import CreativeTeam

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
        print(result.summary())
        print()


def run_custom(brief: str) -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY が未設定です。")
        sys.exit(1)

    print(knowledge_base.summary())
    team = CreativeTeam(api_key=api_key)
    result = team.run(brief, verbose=True)
    print(result.summary())


if __name__ == "__main__":
    if len(sys.argv) > 1:
        custom_brief = " ".join(sys.argv[1:])
        run_custom(custom_brief)
    else:
        # デフォルトは最初のブリーフのみ実行（コスト節約のため）
        run_demo(brief_index=0)

"""
Creative Agency Team Framework

Hierarchy:
  ECD (orchestrator)
  ├── Researcher
  ├── Strategic Planner
  └── CD (sub-orchestrator)
      ├── Challenger  ← CDのコンセプトを壊す役（チャレンジ後に再構築）
      ├── Activation Planner
      ├── CopyWriter
      └── Art Director

knowledge/ フォルダに PDF・PPT・TXT を置くと全エージェントの前提知識になる。
"""

import os
import html as html_module
import urllib.parse
import urllib.request
import re
import concurrent.futures
from dataclasses import dataclass, field
from datetime import datetime

import knowledge_base
from typing import Any

import anthropic

MODEL = "claude-opus-4-7"
MAX_TOKENS = 8096


@dataclass
class AgentResult:
    agent_name: str
    task: str
    output: str
    success: bool


@dataclass
class TeamResult:
    original_task: str
    agent_results: list[AgentResult] = field(default_factory=list)
    final_answer: str = ""

    def summary(self) -> str:
        lines = [f"=== Creative Output: {self.original_task} ===\n"]
        for r in self.agent_results:
            status = "✓" if r.success else "✗"
            lines.append(f"[{status}] {r.agent_name}")
            lines.append(f"    {r.output[:300]}{'...' if len(r.output) > 300 else ''}\n")
        lines.append(f"--- ECDファイナルディレクション ---\n{self.final_answer}")
        return "\n".join(lines)

    def to_html(self) -> str:
        def md_to_html(text: str) -> str:
            t = html_module.escape(text)
            t = re.sub(r"^### (.+)$", r"<h3>\1</h3>", t, flags=re.MULTILINE)
            t = re.sub(r"^## (.+)$", r"<h2>\1</h2>", t, flags=re.MULTILINE)
            t = re.sub(r"^# (.+)$", r"<h1>\1</h1>", t, flags=re.MULTILINE)
            t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
            t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
            t = re.sub(r"^[-•] (.+)$", r"<li>\1</li>", t, flags=re.MULTILINE)
            t = re.sub(r"(<li>.*?</li>\n?)+", lambda m: f"<ul>{m.group()}</ul>", t, flags=re.DOTALL)
            t = re.sub(r"^---+$", r"<hr>", t, flags=re.MULTILINE)
            t = re.sub(r"\n{2,}", "</p><p>", t)
            t = re.sub(r"\n", "<br>", t)
            return f"<p>{t}</p>"

        generated_at = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        agent_sections = ""
        for r in self.agent_results:
            status_class = "success" if r.success else "error"
            status_label = "完了" if r.success else "エラー"
            agent_sections += f"""
            <div class="agent-card {status_class}">
                <div class="agent-header">
                    <span class="agent-name">{html_module.escape(r.agent_name)}</span>
                    <span class="agent-status">{status_label}</span>
                </div>
                <div class="agent-body">{md_to_html(r.output)}</div>
            </div>"""

        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>クリエイティブアウトプット — {html_module.escape(self.original_task[:60])}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "Hiragino Sans", "Yu Gothic", sans-serif; background: #f5f5f0; color: #1a1a1a; line-height: 1.8; }}
  .page {{ max-width: 960px; margin: 0 auto; padding: 48px 24px; }}
  header {{ border-bottom: 3px solid #1a1a1a; padding-bottom: 24px; margin-bottom: 48px; }}
  header h1 {{ font-size: 1.1rem; font-weight: 600; letter-spacing: .08em; color: #555; margin-bottom: 8px; }}
  header p {{ font-size: 1.4rem; font-weight: 700; line-height: 1.5; }}
  .meta {{ font-size: .8rem; color: #888; margin-top: 8px; }}
  .section-title {{ font-size: .75rem; font-weight: 700; letter-spacing: .12em; color: #888; text-transform: uppercase; margin-bottom: 20px; }}
  .agent-card {{ background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 20px; overflow: hidden; }}
  .agent-card.error {{ border-left: 4px solid #e55; }}
  .agent-header {{ display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; background: #fafafa; border-bottom: 1px solid #e0e0e0; }}
  .agent-name {{ font-weight: 700; font-size: .95rem; }}
  .agent-status {{ font-size: .75rem; color: #888; }}
  .agent-body {{ padding: 20px; font-size: .9rem; }}
  .agent-body h1, .agent-body h2, .agent-body h3 {{ margin: 1em 0 .5em; font-weight: 700; }}
  .agent-body h2 {{ font-size: 1.05rem; border-bottom: 1px solid #eee; padding-bottom: 4px; }}
  .agent-body h3 {{ font-size: .95rem; color: #444; }}
  .agent-body ul {{ padding-left: 1.4em; margin: .5em 0; }}
  .agent-body li {{ margin-bottom: .3em; }}
  .agent-body strong {{ font-weight: 700; }}
  .agent-body hr {{ border: none; border-top: 1px solid #eee; margin: 1em 0; }}
  .final {{ background: #1a1a1a; color: #f5f5f0; border-radius: 8px; padding: 36px; margin-top: 48px; }}
  .final .section-title {{ color: #aaa; }}
  .final-body {{ font-size: 1rem; line-height: 1.9; margin-top: 16px; }}
  .final-body h1, .final-body h2, .final-body h3 {{ color: #fff; margin: 1.2em 0 .5em; }}
  .final-body h2 {{ font-size: 1.1rem; border-bottom: 1px solid #444; padding-bottom: 4px; }}
  .final-body ul {{ padding-left: 1.4em; margin: .5em 0; }}
  .final-body li {{ margin-bottom: .3em; }}
  .final-body strong {{ color: #fff; }}
  .final-body hr {{ border: none; border-top: 1px solid #444; margin: 1em 0; }}
  p {{ margin: .6em 0; }}
</style>
</head>
<body>
<div class="page">
  <header>
    <h1>クリエイティブアウトプット</h1>
    <p>{html_module.escape(self.original_task)}</p>
    <div class="meta">生成日時：{generated_at}</div>
  </header>

  <div class="section-title">各エージェントのアウトプット</div>
  {agent_sections}

  <div class="final">
    <div class="section-title">ECDファイナルディレクション</div>
    <div class="final-body">{md_to_html(self.final_answer)}</div>
  </div>
</div>
</body>
</html>"""


class SpecialistAgent:
    """Base class for specialist agents."""

    def __init__(self, client: anthropic.Anthropic, name: str, system_prompt: str):
        self.client = client
        self.name = name
        self.system_prompt = system_prompt

    def run(self, task: str, context: str = "", knowledge: str = "") -> AgentResult:
        parts = []
        if knowledge:
            parts.append(knowledge)
        if context:
            parts.append(f"Team context:\n{context}")
        parts.append(f"Your task:\n{task}")
        user_content = "\n\n".join(parts)

        try:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                thinking={"type": "adaptive"},
                system=self.system_prompt,
                messages=[{"role": "user", "content": user_content}],
            )
            output = next((b.text for b in response.content if b.type == "text"), "")
            return AgentResult(agent_name=self.name, task=task, output=output, success=True)
        except Exception as e:
            return AgentResult(agent_name=self.name, task=task, output=f"Error: {e}", success=False)


# ---------------------------------------------------------------------------
# Tier 1 specialists — report directly to ECD
# ---------------------------------------------------------------------------



class ResearcherAgent(SpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Researcher",
            system_prompt=(
                "あなたはクリエイティブエージェンシーの消費者・文化リサーチャーだ。\n"
                "ただし、普通のリサーチャーとは仕事の優先順位が違う。\n\n"
                "【最重要ミッション：白地の特定】\n"
                "競合が『何をやっているか』は調べない。"
                "『誰もやっていないこと』『誰も言っていないこと』『誰も向き合っていない感情』を探す。\n"
                "カテゴリー全体が集団的に避けている話題、語られていない緊張、"
                "無視されている生活者のリアルを掘り出す。\n\n"
                "【調査の4軸】\n"
                "1. 競合白地マップ：このカテゴリーで誰も主張していないポジション・感情・価値観は何か\n"
                "2. 言語化されていない真実："
                "   生活者が感じているが誰も言葉にできていない感覚・矛盾・本音は何か\n"
                "3. 文化的緊張：社会の中でこのカテゴリーに関連して起きている摩擦・変化・問いは何か\n"
                "4. 意外な事実：このブリーフに関係する、誰も知らなかった（または見落としている）真実\n\n"
                "【アウトプット形式】\n"
                "■ 競合白地マップ（誰もやっていないこと一覧）\n"
                "■ 言語化されていない生活者の本音\n"
                "■ 最も挑発的な文化的緊張\n"
                "■ クリエイティブチームへの一行インサイト（これだけ覚えておけ、という真実）"
            ),
        )


class StrategicPlannerAgent(SpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Strategic Planner",
            system_prompt=(
                "あなたは世界トップクラスのクリエイティブエージェンシーのストラテジックプランナーだ。\n\n"
                "【役割】\n"
                "ブランドのポジショニング・コミュニケーション戦略・長期クリエイティブプラットフォームを定義する。"
                "何年もキャンペーンを動かせる、最も説得力のある人間的真実を特定する。"
                "ビジネスの野心を文化的瞬間と人間の欲望につなぐ。\n\n"
                "【異業種移植（必須）】\n"
                "戦略を組む前に、全く別のカテゴリー（このブリーフが食品なら軍事・宗教・ゲーム・医療など、"
                "遠ければ遠いほど良い）から3〜5の成功事例を参照する。"
                "表面（ビジュアル・コピー）ではなく『なぜ機能したか』の構造的メカニズムを抽出し、"
                "このブリーフの戦略に移植する。\n\n"
                "【アウトプット形式】\n"
                "■ ブランドの真実（Human Truth）\n"
                "■ 文化的緊張（このブランドが介入すべき社会の摩擦）\n"
                "■ 異業種移植アイデア（業界／構造的メカニズム／このブリーフへの応用 を各事例で）\n"
                "■ 戦略テリトリー（長期プラットフォームの骨格）\n"
                "■ クリエイティブチームへの挑発的な問い（思考を解放する一文）"
            ),
        )


class ActivationPlannerAgent(SpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Activation Planner",
            system_prompt=(
                "You are an Activation Planner at a world-class creative agency. "
                "Your role is to translate the creative concept into a concrete, "
                "channel-by-channel activation plan that reaches people at the right moment. "
                "You design the consumer journey — from awareness to action — across "
                "paid, owned, earned, and experiential touchpoints. "
                "You think in moments, not media: where is the audience? what are they doing? "
                "what does the brand interruption feel like in that context? "
                "You plan events, stunts, social amplification, influencer strategy, "
                "retail activation, and OOH with the same creative rigor as the big idea. "
                "Structure your output: consumer journey map, channel strategy by phase "
                "(launch / sustain / amplify), key activation moments, KPIs per channel, "
                "and the one unexpected activation that could earn media on its own."
            ),
        )


# ---------------------------------------------------------------------------
# Challenger — attacks creative work for being safe / predictable
# ---------------------------------------------------------------------------

class ChallengerAgent(SpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Challenger",
            system_prompt=(
                "あなたの仕事はクリエイティブワークを壊すことだ。\n"
                "提出されたコンセプト・コピー・戦略を読み、\n"
                "「安全」「予測可能」「カテゴリーの常識の内側」にあるものをすべて暴く。\n\n"
                "【攻撃の3軸】\n"
                "1. カテゴリーの陳腐化：このカテゴリーが繰り返してきた嘘・決まり文句・典型表現は何か。"
                "   このアウトプットはその罠に落ちていないか？\n"
                "2. 視点の甘さ：最も意外な視点、最も勇気のある問いを誰も立てていないか？"
                "   なぜこのブランドでなければならないか、が消えていないか？\n"
                "3. 変化のなさ：このアウトプットが世に出たとして、人の認識・行動・感情が本当に変わるか？"
                "   変わらないなら、何が足りないか？\n\n"
                "【アウトプット形式】\n"
                "■ 陳腐化している点（具体的に）\n"
                "■ このカテゴリーの「誰もやっていない白地」\n"
                "■ 次のラウンドで絶対に踏み込むべき方向（2〜3案）\n\n"
                "遠慮しない。礼儀正しい批評は仕事の邪魔だ。"
            ),
        )


# ---------------------------------------------------------------------------
# Tier 2 specialists — report to CD
# ---------------------------------------------------------------------------

def _fetch_tcc_copy(keyword: str, max_results: int = 10) -> str:
    """TCC コピラ（https://www.tcc.gr.jp/copira/）からキーワード検索して受賞コピー例を返す。"""
    encoded = urllib.parse.quote(keyword)
    url = f"https://www.tcc.gr.jp/copira/?copy={encoded}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return f"[TCC検索エラー: {e}]"

    # 件数を抽出
    count_match = re.search(r"([\d,]+)件が検索されました", html)
    count_str = count_match.group(0) if count_match else "件数不明"

    # <tr> ブロックからコピー・クライアント・コピーライター・媒体・年度を抽出
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL)
    entries = []
    for row in rows:
        # コピー本文（フルURL: https://www.tcc.gr.jp/copira/id/...）、改行を含む可能性あり
        copy_match = re.search(r'href="https://www\.tcc\.gr\.jp/copira/id/[^"]+">(.+?)</a>', row, re.DOTALL)
        if not copy_match:
            continue
        copy_text = re.sub(r"\s+", " ", copy_match.group(1)).strip()

        # クライアント名
        client_match = re.search(r'class="copira__client">([^<]+)</p>', row)
        client = client_match.group(1).strip() if client_match else ""

        # コピーライター名（複数の場合は最初の一人 + 他）
        cw_names = re.findall(r'class="copira__copywriter"[^>]*>.*?<a[^>]*>([^<]+)</a>', row, re.DOTALL)
        cw = "・".join(cw_names) if cw_names else ""

        # 媒体
        media_match = re.search(r'class="text-align-right">([^<]+)</td>', row)
        media = media_match.group(1).strip() if media_match else ""

        # 年度（<th>2024年</th>）
        year_match = re.search(r"<th>(\d{4}年)</th>", row)
        year = year_match.group(1) if year_match else ""

        entries.append(f"「{copy_text}」 — {client}／{cw}（{year}・{media}）")
        if len(entries) >= max_results:
            break

    results = "\n".join(entries) if entries else "（コピーテキスト取得できず）"
    return f"【TCC コピラ検索結果】キーワード：「{keyword}」 / {count_str}\n{results}\n参照URL: {url}"


_TCC_TOOL_DEF = {
    "name": "search_tcc_copy",
    "description": (
        "東京コピーライターズクラブ（TCC）のコピー検索データベース「コピラ」を検索し、"
        "受賞コピーや掲載コピーの実例を取得する。"
        "キーワードは日本語で、商品カテゴリ・感情・テーマ・ブランド名などを指定できる。"
        "1960年〜現在のTCC賞受賞作を含む6万件超のコピーが対象。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "検索キーワード（日本語）。例：「ビール 夏」「母 贈り物」「自動車 未来」",
            }
        },
        "required": ["keyword"],
    },
}


class CopyWriterAgent(SpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="CopyWriter",
            system_prompt=(
                "あなたは日本トップクラスのコピーライターです。"
                "東京コピーライターズクラブ（TCC）賞を目指すレベルの言葉を書いてください。\n\n"
                "【TCC受賞コピーの美学】\n"
                "・一行で宇宙を開く：短く、鋭く、余白がある\n"
                "・「当たり前」をひっくり返す視点：読んだ瞬間に世界が違って見える\n"
                "・生活者の感情に名前をつける：言葉にならなかった感覚を言葉にする\n"
                "・リズムと沈黙：句読点の位置、改行、字数感覚を磨く\n"
                "・真実の匂い：作られた言葉ではなく、実際にあった感情から始める\n\n"
                "【参考データベース】\n"
                "search_tcc_copy ツールで TCC コピラ（https://www.tcc.gr.jp/copira/）を検索し、"
                "テーマや感情に近いコピーの実例を参照してからアウトプットを組み立てること。"
                "実例から「なぜこのコピーが機能するか」を分析し、そのエッセンスを応用する。\n\n"
                "【書き始める前に必ず答える問い】\n"
                "・このカテゴリーが10年間繰り返してきた言葉・表現は何か？（→ 禁止リスト化する）\n"
                "・この製品・ブランドを「悪役」にしたら、どんな言葉になるか？\n"
                "・ターゲットの「当たり前」が実は間違っていたとしたら？\n"
                "・最も小さな真実（誰も言語化していなかった感覚）から始めるとしたら？\n\n"
                "【アウトプット形式】\n"
                "複数の方向性（理性・感情・意外性）でコピーを提案し、"
                "各コピーについて「なぜこの言葉か」を一言で説明する。"
                "ジャーゴンとクリシェは禁止。すべての一行が存在理由を持つこと。"
            ),
        )

    def run(self, task: str, context: str = "", knowledge: str = "") -> AgentResult:
        parts = []
        if knowledge:
            parts.append(knowledge)
        if context:
            parts.append(f"Team context:\n{context}")
        parts.append(f"Your task:\n{task}")
        user_content = "\n\n".join(parts)

        messages: list[dict] = [{"role": "user", "content": user_content}]

        try:
            while True:
                response = self.client.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    thinking={"type": "adaptive"},
                    system=self.system_prompt,
                    tools=[_TCC_TOOL_DEF],
                    messages=messages,
                )

                # ツール呼び出しがない場合 → 最終アウトプット
                if response.stop_reason != "tool_use":
                    output = next((b.text for b in response.content if b.type == "text"), "")
                    return AgentResult(agent_name=self.name, task=task, output=output, success=True)

                # ツール実行ループ
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        kw = block.input.get("keyword", "")
                        print(f"      [TCC検索] キーワード：「{kw}」")
                        result_text = _fetch_tcc_copy(kw)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text,
                        })
                messages.append({"role": "user", "content": tool_results})

        except Exception as e:
            return AgentResult(agent_name=self.name, task=task, output=f"Error: {e}", success=False)


class ArtDirectorAgent(SpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Art Director",
            system_prompt=(
                "You are an Art Director at a world-class creative agency. "
                "Define the visual language of a campaign — typography, color palette, "
                "composition, photography style, motion aesthetic, and overall visual world. "
                "Think in images, feelings, and sensations. Describe a visual concept so "
                "vividly that people can see it before it's made. "
                "Deliver: mood, references, color story, typographic personality, "
                "imagery style, and a scene-by-scene description of the hero execution."
            ),
        )


# ---------------------------------------------------------------------------
# CD — sub-orchestrator between ECD and the creative execution team
# ---------------------------------------------------------------------------

class CDAgent:
    """
    Creative Director — parallel sub-orchestrator.

    Workflow:
      1. CD develops creative concept (single Claude call)
      2. Round 1: CopyWriter / Art Director / Activation Planner run in parallel
      3. Round 2: all three deepen their work seeing each other's Round 1 outputs (parallel)
      4. CD synthesizes into a unified creative package (single Claude call)
    """

    CD_CONCEPT_SYSTEM = (
        "あなたは世界トップクラスのクリエイティブエージェンシーのクリエイティブディレクターだ。\n\n"
        "ECDから受け取った戦略・リサーチ・異業種移植アイデア・禁じ手リストをもとに、"
        "強力なクリエイティブコンセプトを開発する。\n\n"
        "【コンセプト開発の原則】\n"
        "・禁じ手リストのどれにも触れない\n"
        "・異業種移植アイデアの構造的メカニズムを活かす\n"
        "・「なぜこのブランドでなければならないか」が明確\n"
        "・世に出た瞬間に認識・感情・行動を変えるポテンシャルがある\n\n"
        "【アウトプット形式】\n"
        "■ コアコンセプト（一文）\n"
        "■ コンセプトの背景にある人間的真実\n"
        "■ このコンセプトが機能する構造的理由\n"
        "■ CopyWriter・Art Director・Activation Plannerへの個別ブリーフ"
    )

    CD_SYNTHESIS_SYSTEM = (
        "あなたは世界トップクラスのクリエイティブエージェンシーのクリエイティブディレクターだ。\n\n"
        "チームのアウトプット（CopyWriter・Art Director・Activation Planner の2ラウンド分）を"
        "統合し、ECDに提出するクリエイティブパッケージを完成させる。\n\n"
        "【統合の観点】\n"
        "・コピー・ビジュアル・アクティベーションが一つのコンセプトとして貫通しているか\n"
        "・それぞれの専門家の最良のアイデアを選び取り、矛盾を解消しているか\n"
        "・ECDへの提出物として、意思決定できるレベルの具体性があるか\n\n"
        "【アウトプット形式】\n"
        "■ クリエイティブコンセプト（確定版）\n"
        "■ ヒーローコピー\n"
        "■ ビジュアルワールド\n"
        "■ アクティベーション設計\n"
        "■ CDとしての総括コメント"
    )

    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.name = "Creative Director"
        self.specialists: dict[str, SpecialistAgent] = {
            "activation_planner": ActivationPlannerAgent(client),
            "copywriter": CopyWriterAgent(client),
            "art_director": ArtDirectorAgent(client),
        }

    def _call_claude(self, system: str, content: str) -> str:
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            thinking={"type": "adaptive"},
            system=system,
            messages=[{"role": "user", "content": content}],
        )
        return next((b.text for b in response.content if b.type == "text"), "")

    def run(self, task: str, context: str = "", knowledge: str = "") -> AgentResult:
        parts = []
        if knowledge:
            parts.append(knowledge)
        if context:
            parts.append(f"ECDからの戦略コンテキスト:\n{context}")
        parts.append(f"クリエイティブチャレンジ:\n{task}")
        base = "\n\n".join(parts)

        try:
            # Step 1: CDがコンセプトを開発
            print("  [CD] コンセプト開発中...")
            concept = self._call_claude(self.CD_CONCEPT_SYSTEM, base)
            concept_context = f"{base}\n\n### CDコンセプト:\n{concept}"

            # Step 2: Round 1 — 3専門家が並列で独立して思考
            print("  [CD] Round 1 — CW / AD / AP 並列実行...")
            r1_tasks = {
                "copywriter":        "上記のコンセプトに基づき、コピーの方向性を複数提案してください。",
                "art_director":      "上記のコンセプトに基づき、ビジュアルワールドを定義してください。",
                "activation_planner":"上記のコンセプトに基づき、アクティベーション施策を設計してください。",
            }
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
                fs1 = {
                    k: ex.submit(self.specialists[k].run, t, concept_context, knowledge)
                    for k, t in r1_tasks.items()
                }
                r1 = {k: f.result() for k, f in fs1.items()}
            for r in r1.values():
                print(f"    ✓ {r.agent_name} Round 1 ({len(r.output)} chars)")

            # Step 3: Round 2 — 互いのアウトプットを見て深化（並列）
            print("  [CD] Round 2 — 相互参照して深化（並列）...")
            cross_context = concept_context + "\n\n" + "\n\n".join(
                f"### {r.agent_name} Round 1:\n{r.output}" for r in r1.values()
            )
            r2_tasks = {
                "copywriter":        "他のメンバーのアウトプットを踏まえ、コピーをさらに深化・研ぎ澄ましてください。",
                "art_director":      "他のメンバーのアウトプットを踏まえ、ビジュアルワールドを深化・統合してください。",
                "activation_planner":"他のメンバーのアウトプットを踏まえ、施策をより一貫性のある形に深化させてください。",
            }
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
                fs2 = {
                    k: ex.submit(self.specialists[k].run, t, cross_context, knowledge)
                    for k, t in r2_tasks.items()
                }
                r2 = {k: f.result() for k, f in fs2.items()}
            for r in r2.values():
                print(f"    ✓ {r.agent_name} Round 2 ({len(r.output)} chars)")

            # Step 4: CD が統合
            print("  [CD] 統合中...")
            all_outputs = "\n\n".join(
                f"### {r.agent_name} Round 2:\n{r.output}" for r in r2.values()
            )
            synthesis = self._call_claude(
                self.CD_SYNTHESIS_SYSTEM,
                f"{concept_context}\n\n{all_outputs}",
            )

            full_output = (
                f"**コンセプト:**\n{concept}\n\n"
                + "\n\n".join(f"**{r.agent_name} Round 1:**\n{r.output}" for r in r1.values())
                + "\n\n"
                + "\n\n".join(f"**{r.agent_name} Round 2:**\n{r.output}" for r in r2.values())
                + f"\n\n---\n\n**CDクリエイティブパッケージ:**\n{synthesis}"
            )
            return AgentResult(agent_name=self.name, task=task, output=full_output, success=True)

        except Exception as e:
            return AgentResult(agent_name=self.name, task=task, output=f"Error: {e}", success=False)


# ---------------------------------------------------------------------------
# ECD — top-level orchestrator (explicit parallel phases)
# ---------------------------------------------------------------------------

class CreativeTeam:
    """
    ECD-led creative team orchestrator.

    Phases:
      0. ECD analyzes and reframes the brief (single Claude call)
      1. Researcher + Strategic Planner run in parallel
      2. ECD synthesizes phase 1 into a CD brief (single Claude call)
      3. CDAgent runs (parallel CW/AD/AP × 2 rounds internally)
      4. Challenger reviews CD package
      5. ECD delivers final direction (single Claude call)
    """

    ECD_ANALYZE_SYSTEM = (
        "あなたは世界トップクラスのクリエイティブエージェンシーのECDだ。\n\n"
        "クライアントから届いたブリーフを解剖し、チームを正しい方向へ向かわせる。\n\n"
        "【解剖の4軸】\n"
        "1. 前提の解体：ターゲット設定・課題定義・KPI・競合の枠組みのうち、疑うべき仮定を特定する\n"
        "2. 本質的な課題：クライアントが言っていることと本当に必要なことのギャップを明らかにする\n"
        "3. 問いの書き換え：「〇〇を伝えたい」を「〇〇という問いを社会に投げかけたい」に変換する\n"
        "4. 禁じ手リスト：このカテゴリーが広告で繰り返してきた3つの陳腐なアプローチを列挙する\n\n"
        "【アウトプット形式】\n"
        "■ 前提の解体（疑うべき仮定に★）\n"
        "■ 本質的な課題\n"
        "■ 書き換えられた問い（これが以降のすべてのブリーフの核になる）\n"
        "■ 禁じ手リスト\n"
        "■ 絶対に陥ってはいけない罠"
    )

    ECD_CD_BRIEF_SYSTEM = (
        "あなたは世界トップクラスのクリエイティブエージェンシーのECDだ。\n\n"
        "自分のブリーフ解析・Researcherの調査・Strategic Plannerの戦略を統合し、"
        "Creative Director（CD）に渡すクリエイティブチャレンジを作る。\n\n"
        "CDブリーフには必ず以下を含める:\n"
        "・書き換えられた問い\n"
        "・禁じ手リスト\n"
        "・最も刺さるリサーチインサイト\n"
        "・異業種移植アイデアの中で最も可能性のあるもの\n"
        "・ECDとしての期待水準（カンヌ獲れるか？世界を少し変えるか？）\n\n"
        "簡潔に、しかしCDが迷わない具体性で書く。"
    )

    ECD_FINAL_SYSTEM = (
        "あなたは世界トップクラスのクリエイティブエージェンシーのECDだ。\n\n"
        "チーム全員のアウトプット（Research・Strategy・CD・Challenger）を踏まえ、"
        "ECDとして最終ディレクションを出す。\n\n"
        "【最終ディレクションに含めるもの】\n"
        "■ このキャンペーンが世界を少し変える理由\n"
        "■ CDパッケージのどこを採用し、どこを修正するか\n"
        "■ Challengerの指摘のうち、次のラウンドで必ず解決すべき点\n"
        "■ クライアントプレゼンに向けてのECDコメント"
    )

    def __init__(self, api_key: str | None = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.researcher = ResearcherAgent(self.client)
        self.strategic_planner = StrategicPlannerAgent(self.client)
        self.cd = CDAgent(self.client)
        self.challenger = ChallengerAgent(self.client)
        self.knowledge = knowledge_base.load()

    def _call_claude(self, system: str, content: str) -> str:
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            thinking={"type": "adaptive"},
            system=system,
            messages=[{"role": "user", "content": content}],
        )
        return next((b.text for b in response.content if b.type == "text"), "")

    def run(self, brief: str, verbose: bool = True) -> TeamResult:
        if verbose:
            print(f"\n{'='*60}")
            print(f"ECD Brief: {brief}")
            print(f"{'='*60}")

        team_result = TeamResult(original_task=brief)

        # Phase 0: ECD がブリーフを解析・書き換え
        print("\n[Phase 0] ECD — ブリーフ解析中...")
        ecd_analysis = self._call_claude(
            self.ECD_ANALYZE_SYSTEM,
            f"ブリーフ:\n{brief}" + (f"\n\nナレッジ:\n{self.knowledge}" if self.knowledge else ""),
        )
        team_result.agent_results.append(
            AgentResult("ECD — ブリーフ解析", brief, ecd_analysis, True)
        )
        print(f"  ✓ ECD分析完了 ({len(ecd_analysis)} chars)")

        # Phase 1: Researcher + Strategic Planner を並列実行
        print("\n[Phase 1] Researcher + Strategic Planner — 並列実行中...")
        research_input = f"{ecd_analysis}\n\n元ブリーフ:\n{brief}"
        strategy_input = f"{ecd_analysis}\n\n元ブリーフ:\n{brief}"

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            f_r = ex.submit(self.researcher.run, research_input, "", self.knowledge)
            f_s = ex.submit(self.strategic_planner.run, strategy_input, "", self.knowledge)
            research_result = f_r.result()
            strategy_result = f_s.result()

        team_result.agent_results.extend([research_result, strategy_result])
        print(f"  ✓ Researcher ({len(research_result.output)} chars)")
        print(f"  ✓ Strategic Planner ({len(strategy_result.output)} chars)")

        # Phase 2: ECD が Phase 1 を統合して CD ブリーフを生成
        print("\n[Phase 2] ECD — CDブリーフ生成中...")
        cd_brief = self._call_claude(
            self.ECD_CD_BRIEF_SYSTEM,
            f"### ECD分析:\n{ecd_analysis}\n\n"
            f"### Research:\n{research_result.output}\n\n"
            f"### Strategic Planner:\n{strategy_result.output}\n\n"
            f"元ブリーフ:\n{brief}",
        )
        cd_context = (
            f"### ECD分析:\n{ecd_analysis}\n\n"
            f"### Research:\n{research_result.output}\n\n"
            f"### Strategic Planner:\n{strategy_result.output}"
        )
        print(f"  ✓ CDブリーフ生成完了 ({len(cd_brief)} chars)")

        # Phase 3: CD が並列チームで実行（内部で2ラウンド）
        print("\n[Phase 3] CD チーム — 並列 × 2ラウンド...")
        cd_result = self.cd.run(cd_brief, cd_context, self.knowledge)
        team_result.agent_results.append(cd_result)
        print(f"  ✓ CDパッケージ完成 ({len(cd_result.output)} chars)")

        # Phase 4: Challenger が CD パッケージを攻撃
        print("\n[Phase 4] Challenger — CDアウトプットをレビュー中...")
        challenger_result = self.challenger.run(cd_result.output, knowledge=self.knowledge)
        team_result.agent_results.append(challenger_result)
        print(f"  ✓ Challenger完了 ({len(challenger_result.output)} chars)")

        # Phase 5: ECD が全アウトプットを統合してファイナルディレクション
        print("\n[Phase 5] ECD — ファイナルディレクション...")
        all_context = "\n\n".join(
            f"### {r.agent_name}:\n{r.output}" for r in team_result.agent_results
        )
        team_result.final_answer = self._call_claude(
            self.ECD_FINAL_SYSTEM,
            f"元ブリーフ:\n{brief}\n\n{all_context}",
        )
        print(f"  ✓ ファイナルディレクション完了 ({len(team_result.final_answer)} chars)")

        return team_result

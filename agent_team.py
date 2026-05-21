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


class BriefReframerAgent(SpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Brief Reframer",
            system_prompt=(
                "あなたの仕事は、クライアントから届いた生ブリーフを解剖することだ。\n\n"
                "【問い出す4つの軸】\n"
                "1. 前提の解体：このブリーフが「当たり前」として受け入れている仮定は何か？"
                "   ターゲット設定、課題の定義、KPI、競合の枠組み——それぞれ本当に正しいか？\n"
                "2. 本質的な課題：クライアントが『言っていること』と『本当に必要なこと』は一致しているか？"
                "   表面の要望の裏に隠れている、より根本的な問いは何か？\n"
                "3. 視点の転換：このブリーフをターゲット以外の誰か（競合・社会・未来の消費者）の"
                "   目線で読み直すと、何が見えてくるか？\n"
                "4. 問いの書き換え：「〇〇を伝えたい」ではなく「〇〇という問いを社会に投げかけたい」"
                "   に変換すると、どんな問いになるか？\n\n"
                "【アウトプット形式】\n"
                "■ 元ブリーフの前提リスト（疑うべき箇所に★）\n"
                "■ 本質的な課題（クライアントが言っていない言葉で）\n"
                "■ 書き換えられた問い（クリエイティブチームへの挑発として）\n"
                "■ このブリーフで絶対に陥ってはいけない罠\n\n"
                "クライアントの言葉を尊重しつつ、その先にある本質を暴く。"
            ),
        )


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
    Creative Director — sub-orchestrator.
    Receives the strategic brief from the ECD, then independently
    briefs CopyWriter and Art Director to build the creative execution.
    Returns a consolidated creative package back to the ECD.
    """

    CD_SYSTEM = (
        "You are a Creative Director (CD) at a world-class creative agency. "
        "You sit between the ECD's strategic direction and the execution team. "
        "Your role: transform strategy into a powerful creative concept, "
        "then orchestrate your team to execute it across copy, visuals, and activation. "
        "You push for ideas that are bold, original, and emotionally resonant. "
        "You challenge the obvious. You protect the work from mediocrity.\n\n"
        "Your team:\n"
        "- Activation Planner: consumer journey, channel strategy, touchpoints, events, stunts\n"
        "- CopyWriter: language, headlines, taglines, manifestos, scripts\n"
        "- Art Director: visual language, mood, color, typography, imagery\n\n"
        "【必須ワークフロー】\n"
        "Step 0 — コンセプトを立てる前に：このカテゴリーが繰り返してきた3つの陳腐なアプローチを列挙し、"
        "それを「禁じ手リスト」として明示する。コンセプトはそのどれにも触れてはならない。\n"
        "Step 1 — ECDから受け取った戦略・異業種移植アイデア・禁じ手リストをもとにコンセプトを立てる。\n"
        "Step 2 — CopyWriter・Art Director・Activation Plannerをブリーフする。\n"
        "Step 3 — 全員のアウトプットを統合してECDに提出する。"
    )

    CD_TOOLS: list[dict[str, Any]] = [
        {
            "name": "brief_activation_planner",
            "description": (
                "Brief the Activation Planner to design the channel-by-channel activation plan — "
                "consumer journey, touchpoints, events, social, OOH, and experiential moments. "
                "Use this once the creative concept is set to map how it comes to life."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The activation planning task."},
                    "include_context": {"type": "boolean", "default": True},
                },
                "required": ["task"],
            },
        },
        {
            "name": "brief_copywriter",
            "description": (
                "Brief the CopyWriter to craft the language of the campaign — "
                "headlines, taglines, manifesto, scripts, or any copy needed."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The copy task."},
                    "include_context": {"type": "boolean", "default": True},
                },
                "required": ["task"],
            },
        },
        {
            "name": "brief_art_director",
            "description": (
                "Brief the Art Director to define the visual language — "
                "mood, aesthetic, color, typography, imagery style, and the visual world."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The visual direction task."},
                    "include_context": {"type": "boolean", "default": True},
                },
                "required": ["task"],
            },
        },
    ]

    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.name = "Creative Director"
        self.specialists: dict[str, SpecialistAgent] = {
            "activation_planner": ActivationPlannerAgent(client),
            "copywriter": CopyWriterAgent(client),
            "art_director": ArtDirectorAgent(client),
        }

    def _build_context(self, results: list[AgentResult]) -> str:
        if not results:
            return ""
        return "\n\n---\n\n".join(f"### {r.agent_name}:\n{r.output}" for r in results)

    def _dispatch(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        accumulated: list[AgentResult],
        knowledge: str = "",
    ) -> AgentResult:
        key = tool_name.replace("brief_", "")
        agent = self.specialists[key]
        context = self._build_context(accumulated) if tool_input.get("include_context", True) else ""
        print(f"    → CD briefs {agent.name}: {tool_input['task'][:70]}...")
        result = agent.run(tool_input["task"], context, knowledge)
        print(f"      ✓ {agent.name} delivered ({len(result.output)} chars)")
        return result

    def run(self, task: str, context: str = "", knowledge: str = "") -> AgentResult:
        """Run the CD sub-orchestrator loop and return a consolidated AgentResult."""
        parts = []
        if knowledge:
            parts.append(knowledge)
        if context:
            parts.append(f"Strategic context from upstream:\n{context}")
        parts.append(f"Your creative challenge:\n{task}")
        user_content = "\n\n".join(parts)

        messages: list[dict[str, Any]] = [{"role": "user", "content": user_content}]
        sub_results: list[AgentResult] = []


        try:
            while True:
                response = self.client.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    thinking={"type": "adaptive"},
                    system=self.CD_SYSTEM,
                    tools=self.CD_TOOLS,
                    messages=messages,
                )

                tool_blocks = [b for b in response.content if b.type == "tool_use"]
                text_blocks = [b for b in response.content if b.type == "text"]
                messages.append({"role": "assistant", "content": response.content})

                if response.stop_reason == "end_turn":
                    final = next((b.text for b in text_blocks), "")
                    # Prepend sub-agent outputs for full transparency
                    if sub_results:
                        sub_summary = "\n\n".join(
                            f"**{r.agent_name}**\n{r.output}" for r in sub_results
                        )
                        final = f"{sub_summary}\n\n---\n\n**CD Creative Package:**\n{final}"
                    return AgentResult(
                        agent_name=self.name, task=task, output=final, success=True
                    )

                if response.stop_reason != "tool_use":
                    output = next((b.text for b in text_blocks), "No creative output.")
                    return AgentResult(
                        agent_name=self.name, task=task, output=output, success=True
                    )

                tool_results = []
                for tb in tool_blocks:
                    result = self._dispatch(tb.name, tb.input, sub_results, knowledge)
                    sub_results.append(result)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tb.id,
                        "content": result.output if result.success else f"Error: {result.output}",
                    })
                messages.append({"role": "user", "content": tool_results})

        except Exception as e:
            return AgentResult(agent_name=self.name, task=task, output=f"Error: {e}", success=False)


# ---------------------------------------------------------------------------
# ECD — top-level orchestrator
# ---------------------------------------------------------------------------

class CreativeTeam:
    """
    ECD-led creative team orchestrator.

    Hierarchy:
      ECD → Researcher, Strategic Planner, Planner, CD
      CD  → CopyWriter, Art Director
    """

    ECD_TOOLS: list[dict[str, Any]] = [
        {
            "name": "reframe_brief",
            "description": (
                "Brief Reframerに生ブリーフを渡し、前提の解体・本質的な課題の再定義・"
                "問いの書き換えを行わせる。これは必ずワークフローの最初に呼ぶこと。"
                "Reframerが出力した『書き換えられた問い』を、以降のすべてのブリーフに組み込む。"
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "brief": {
                        "type": "string",
                        "description": "クライアントから届いた生ブリーフの全文。",
                    }
                },
                "required": ["brief"],
            },
        },
        {
            "name": "challenge_cd_output",
            "description": (
                "CDが提出したクリエイティブパッケージをChallengerに渡し、"
                "陳腐化・予測可能・変化を起こせないリスクを攻撃させる。"
                "CDのアウトプットを受け取った後、最終化する前に必ず呼ぶこと。"
                "Challengerの指摘が鋭い場合はCDを再ブリーフする。"
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "creative_package": {
                        "type": "string",
                        "description": "ChallengerにレビューさせるCDのクリエイティブパッケージ全文。",
                    }
                },
                "required": ["creative_package"],
            },
        },
        {
            "name": "brief_researcher",
            "description": (
                "Brief the Researcher to dig into consumer behavior, cultural trends, "
                "competitive landscape, and uncover the human insight that will fuel the work. "
                "Use this first — great creative is built on great research."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Research task or question."},
                    "include_context": {"type": "boolean", "default": True},
                },
                "required": ["task"],
            },
        },
        {
            "name": "brief_strategic_planner",
            "description": (
                "Brief the Strategic Planner to define brand positioning, "
                "communication strategy, and the creative platform."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Strategic challenge to address."},
                    "include_context": {"type": "boolean", "default": True},
                },
                "required": ["task"],
            },
        },
        {
            "name": "brief_cd",
            "description": (
                "Brief the Creative Director with the strategic brief and challenge. "
                "The CD will independently manage CopyWriter and Art Director "
                "to deliver the full creative execution. "
                "Use this after research, strategy, and the brief are in place."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Creative challenge for the CD."},
                    "include_context": {"type": "boolean", "default": True},
                },
                "required": ["task"],
            },
        },
    ]

    ECD_SYSTEM = (
        "You are an Executive Creative Director (ECD) at a world-class creative agency. "
        "You lead the team and set the creative vision.\n\n"
        "Your direct reports:\n"
        "- Researcher: consumer insight, cultural trends, competitive white space\n"
        "- Strategic Planner: brand strategy, positioning, communication platform, cross-industry transplants\n"
        "- Creative Director (CD): leads the creative execution team "
        "(CopyWriter, Art Director, Activation Planner)\n\n"
        "【必須ワークフロー】\n"
        "Step 0 — 必ず reframe_brief を呼ぶ。生ブリーフの前提を解体し、"
        "本質的な問いに書き換える。以降のすべてのブリーフにこの『書き換えられた問い』を組み込む。\n"
        "Step 1 — カテゴリーが広告で繰り返してきた「3つの陳腐なアプローチ」を明示し、"
        "禁じ手リストとしてブリーフに追加する。\n"
        "Step 2 — Researcherに調査を依頼する（競合白地・誰も言語化していない真実が主眼）。\n"
        "Step 3 — Strategic Plannerに戦略を依頼する（異業種移植アイデアを含む）。\n"
        "Step 4 — CDに『書き換えられた問い＋禁じ手リスト＋異業種移植アイデア付き』で"
        "クリエイティブチャレンジを渡す。\n"
        "Step 5 — CDのアウトプットを受け取ったら、必ず challenge_cd_output を呼ぶ。\n"
        "Step 6 — Challengerの指摘が鋭ければ、CDを再ブリーフする（brief_cd を再度呼ぶ）。\n"
        "Step 7 — すべてを統合し、ECDとして「このキャンペーンが世界を少し変える理由」"
        "を言葉にして締める。"
    )

    def __init__(self, api_key: str | None = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.tier1: dict[str, SpecialistAgent] = {
            "researcher": ResearcherAgent(self.client),
            "strategic_planner": StrategicPlannerAgent(self.client),
        }
        self.cd = CDAgent(self.client)
        self.challenger = ChallengerAgent(self.client)
        self.brief_reframer = BriefReframerAgent(self.client)
        self.knowledge = knowledge_base.load()

    def _build_context(self, results: list[AgentResult]) -> str:
        if not results:
            return ""
        return "\n\n---\n\n".join(f"### {r.agent_name}:\n{r.output}" for r in results)

    def _dispatch_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        accumulated: list[AgentResult],
    ) -> AgentResult:
        if tool_name == "reframe_brief":
            brief = tool_input.get("brief", "")
            print(f"  → ECD calls Brief Reframer ({len(brief)} chars)...")
            result = self.brief_reframer.run(brief, knowledge=self.knowledge)
            print(f"    ✓ Brief Reframer delivered ({len(result.output)} chars)")
            return result

        if tool_name == "challenge_cd_output":
            package = tool_input.get("creative_package", "")
            print(f"  → ECD calls Challenger on CD output ({len(package)} chars)...")
            result = self.challenger.run(package, knowledge=self.knowledge)
            print(f"    ✓ Challenger delivered ({len(result.output)} chars)")
            return result

        context = self._build_context(accumulated) if tool_input.get("include_context", True) else ""
        task = tool_input["task"]

        if tool_name == "brief_cd":
            print(f"  → ECD briefs Creative Director: {task[:80]}...")
            result = self.cd.run(task, context, self.knowledge)
            print(f"    ✓ Creative Director delivered ({len(result.output)} chars)")
            return result

        key = tool_name.replace("brief_", "")
        agent = self.tier1[key]
        print(f"  → Briefing {agent.name}: {task[:80]}...")
        result = agent.run(task, context, self.knowledge)
        print(f"    ✓ {agent.name} delivered ({len(result.output)} chars)")
        return result

    def run(self, brief: str, verbose: bool = True) -> TeamResult:
        if verbose:
            print(f"\n{'='*60}")
            print(f"ECD Brief: {brief}")
            print(f"{'='*60}")

        team_result = TeamResult(original_task=brief)
        messages: list[dict[str, Any]] = [{"role": "user", "content": brief}]

        while True:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                thinking={"type": "adaptive"},
                system=self.ECD_SYSTEM,
                tools=self.ECD_TOOLS,
                messages=messages,
            )

            tool_blocks = [b for b in response.content if b.type == "tool_use"]
            text_blocks = [b for b in response.content if b.type == "text"]
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                team_result.final_answer = next((b.text for b in text_blocks), "")
                break

            if response.stop_reason != "tool_use":
                team_result.final_answer = next(
                    (b.text for b in text_blocks), "No creative direction produced."
                )
                break

            tool_results = []
            for tb in tool_blocks:
                result = self._dispatch_tool(tb.name, tb.input, team_result.agent_results)
                team_result.agent_results.append(result)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tb.id,
                    "content": result.output if result.success else f"Error: {result.output}",
                })

            messages.append({"role": "user", "content": tool_results})

        return team_result

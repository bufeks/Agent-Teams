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
    creative_brief: dict = field(default_factory=dict)

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

        def brief_html(cb: dict) -> str:
            if not cb:
                return ""
            LEFT = [
                ("Brand Name", "brand_name"),
                ("Brand Philosophy / Brand Purpose", "brand_philosophy"),
                ("Brand Slogan", "brand_slogan"),
                ("Brand Promise", "brand_promise"),
                ("Business Goal", "business_goal"),
                ("Ad Role", "ad_role"),
                ("Problem", "problem"),
                ("Competitor", "competitor"),
                ("Unique Selling Proposition", "usp"),
                ("Fact", "fact"),
            ]
            RIGHT = [
                ("Target", "target"),
                ("Target Insight", "target_insight"),
                ("Social Insight", "social_insight"),
                ("Before Perception", "before_perception"),
                ("After Perception", "after_perception"),
                ("Tone & Manner", "tone_and_manner"),
                ("Campaign Concept", "campaign_concept"),
                ("Campaign Tagline", "campaign_tagline"),
                ("Key Visual", "key_visual"),
                ("Catch Copy", "catch_copy"),
            ]
            cells = ""
            for (ll, lk), (rl, rk) in zip(LEFT, RIGHT):
                lv = cb.get(lk, "")
                rv = cb.get(rk, "")
                lc = "tbd" if lv in ("", "TBD") else ""
                rc = "tbd" if rv in ("", "TBD") else ""
                cells += f"""<div class="brief-cell">
  <div class="brief-label">{html_module.escape(ll)}</div>
  <div class="brief-value {lc}">{html_module.escape(lv or "—")}</div>
</div>
<div class="brief-cell">
  <div class="brief-label">{html_module.escape(rl)}</div>
  <div class="brief-value {rc}">{html_module.escape(rv or "—")}</div>
</div>"""
            return f"""<div class="brief-wrap">
  <div class="brief-title">C R E A T I V E &nbsp; B R I E F</div>
  <div class="brief-grid">{cells}</div>
</div>"""

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
  .brief-wrap {{ background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 36px; margin-bottom: 48px; }}
  .brief-title {{ font-size: .75rem; font-weight: 700; letter-spacing: .2em; text-align: center; margin-bottom: 28px; color: #1a1a1a; }}
  .brief-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; border-top: 1px solid #ccc; border-left: 1px solid #ccc; }}
  .brief-cell {{ border-right: 1px solid #ccc; border-bottom: 1px solid #ccc; padding: 12px 16px; font-size: .85rem; line-height: 1.6; }}
  .brief-label {{ font-weight: 700; color: #c0392b; font-size: .78rem; letter-spacing: .04em; margin-bottom: 4px; }}
  .brief-value {{ color: #1a1a1a; white-space: pre-wrap; }}
  .brief-value.tbd {{ color: #aaa; font-style: italic; }}
</style>
</head>
<body>
<div class="page">
  <header>
    <h1>クリエイティブアウトプット</h1>
    <p>{html_module.escape(self.original_task)}</p>
    <div class="meta">生成日時：{generated_at}</div>
  </header>

  {brief_html(self.creative_brief)}

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


_WEB_SEARCH_TOOL: dict[str, Any] = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 10,
}


class WebSearchSpecialistAgent(SpecialistAgent):
    """Specialist agent with Anthropic built-in web search (server-side, no extra API key)."""

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
                    system=self.system_prompt,
                    tools=[_WEB_SEARCH_TOOL],
                    messages=messages,
                )

                for block in response.content:
                    if getattr(block, "type", None) == "tool_use":
                        query = getattr(block, "input", {}).get("query", "")
                        if query:
                            print(f"      [Web検索] {query}")

                if response.stop_reason == "end_turn":
                    output = next((b.text for b in response.content if b.type == "text"), "")
                    return AgentResult(agent_name=self.name, task=task, output=output, success=True)

                messages.append({"role": "assistant", "content": response.content})
                tool_results = [
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "",
                    }
                    for block in response.content
                    if getattr(block, "type", None) == "tool_use"
                ]
                if not tool_results:
                    output = next((b.text for b in response.content if b.type == "text"), "")
                    return AgentResult(agent_name=self.name, task=task, output=output, success=True)
                messages.append({"role": "user", "content": tool_results})

        except Exception as e:
            return AgentResult(agent_name=self.name, task=task, output=f"Error: {e}", success=False)


# ---------------------------------------------------------------------------
# Tier 1 specialists — report directly to ECD
# ---------------------------------------------------------------------------



class ResearcherAgent(WebSearchSpecialistAgent):
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
                "【調査の5軸】\n"
                "0. カテゴリーのメンタルフレーム確認（最初に行う）：\n"
                "   このカテゴリーが消費者の頭の中でどんな文脈（時間帯・シーン・感情・用途）に閉じ込められているか整理する。\n"
                "   競合全員が同じ箱にいるなら、箱の外が白地だ。\n"
                "1. 競合白地マップ：このカテゴリーで誰も主張していないポジション・感情・価値観は何か\n"
                "2. インサイト仮説：生活者が感じているが言葉にできていない感覚を「実は〜」の形で3〜4案並べる\n"
                "3. 文化的緊張の候補：社会の中でこのカテゴリーに関連して起きている摩擦・変化・問いを複数列挙する\n"
                "4. 逆説的なデータを積極的に探す：「常識通りのデータ」より「直感に反するデータ」のほうがインサイトになる。\n"
                "   「〜のはずが、実は〜」という形で言えるものを探すこと。\n"
                "   仮説を支持するためにデータを使うのではなく、仮説を裏切るデータを探す。\n"
                "5. 意外な事実：このブリーフに関係する、見落とされている真実\n\n"
                "【重要：1つに絞らない】\n"
                "インサイトは仮説であり、この段階では正解がわからない。"
                "複数の可能性を並べることがResearcherの仕事。絞るのはECDの役割。"
                "各インサイト仮説には『確信度（高/中/低）』と『裏付けとなる観察』をセットで付ける。\n\n"
                "【品質基準】\n"
                "各インサイト仮説をACCグランプリ・カンヌジャパン受賞チームに渡したとき、"
                "『それは知らなかった』と言わせられるか？誰でも言える話は出さない。\n\n"
                "【アウトプット形式】\n"
                "■ カテゴリーのメンタルフレーム（このカテゴリーが閉じ込められている文脈）\n"
                "■ 競合白地マップ（誰もやっていないこと一覧）\n"
                "■ インサイト仮説（3〜4案：「実は〜」の形 / 裏付け観察 / 確信度）\n"
                "■ 逆説的なデータ・発見（「〜のはずが、実は〜」の形で書く）\n"
                "■ 文化的緊張の候補（複数列挙）\n"
                "■ 意外な事実・見落とされている真実\n\n"
                "【Web検索の使い方】\n"
                "web_search ツールを使い、最新の競合事例・市場動向・SNSトレンド・生活者の声を検索して根拠を補強する。"
                "古い知識だけに頼らず、今この瞬間の市場の空気を掴む。\n\n"
                "【引用ルール：必須】\n"
                "データ・事例・発言を引用するときは、必ず出典名とURLをセットで記載する。\n"
                "例：笹川スポーツ財団「スポーツライフに関する調査2024」 https://www.ssf.or.jp/...\n"
                "URLが取得できなかった場合は「URL未確認」と明記し、推測URLを書かない。"
            ),
        )


class StrategicPlannerAgent(WebSearchSpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Strategic Planner",
            system_prompt=(
                "あなたは日本トップクラスのクリエイティブエージェンシーのストラテジックプランナーだ。\n\n"
                "【役割】\n"
                "ブランドのポジショニング・コミュニケーション戦略・長期クリエイティブプラットフォームを定義する。"
                "何年もキャンペーンを動かせる、最も説得力のある人間的真実を特定する。"
                "ビジネスの野心を文化的瞬間と人間の欲望につなぐ。\n\n"
                "【データリサーチ（最重要・必須）】\n"
                "戦略立案の前に、必ず外部の一次データを複数検索して根拠を固める。"
                "『感覚』や『一般論』で語るのは禁止。すべての主張にデータの裏付けを持たせる。\n\n"
                "検索すべき情報源（web_search で積極的に掘ること）：\n\n"
                "【最優先】\n"
                "・博報堂生活総合研究所 seikatsusoken.jp\n"
                "  - 生活定点（seikatsusoken.jp/teiten/）：1992年〜隔年・約1,400項目の生活者意識の時系列データ。食・住・働き・家族・消費など21テーマで性別・年代・地域比較が可能\n"
                "  - 感情ミュート社会・働き直し・若者30年変化など最新研究レポート\n"
                "  - ブリーフのテーマキーワードで seikatsusoken.jp を検索して関連データを引く\n\n"
                "・電通 dentsu.co.jp/knowledge/\n"
                "  - 日本の広告費（dentsu.co.jp/knowledge/ad_cost/）：業種別・媒体別の広告費推移\n"
                "  - 媒体別広告量（dentsu.co.jp/knowledge/ad_amount.html）：月次・業種別の出稿量\n"
                "  - 情報メディア白書（dentsu.co.jp/knowledge/infomedia/）：メディア接触・生活者動向\n"
                "  - 食生活調査・LGBTQ+調査・CMO調査など専門テーマ別レポート\n\n"
                "【定量データ】\n"
                "・総務省統計局（stat.go.jp）：人口・世帯・家計・ICT利用調査\n"
                "・内閣府（cao.go.jp）：消費動向調査、国民生活白書、若者意識調査\n"
                "・厚生労働省（mhlw.go.jp）：労働・健康・少子化関連データ\n"
                "・経済産業省（meti.go.jp）：産業・消費・DX動向\n\n"
                "【市場規模・産業分析】\n"
                "・野村総合研究所NRI（nri.com）：市場規模予測、産業分析\n"
                "・矢野経済研究所（yano.co.jp）：カテゴリー別市場規模・成長率\n\n"
                "【メディア・消費者調査】\n"
                "・NHK放送文化研究所（nhk.or.jp/bunken）：メディア利用行動調査\n"
                "・日経リサーチ・日経クロストレンド：消費トレンド・ブランド調査\n"
                "・マクロミル・インテージ：定量消費者調査\n\n"
                "検索で取るべきデータの種類：\n"
                "1. カテゴリーの市場規模と成長率（過去3年＋予測）\n"
                "2. ターゲット層の意識・行動・価値観の変化（定量・定性両方）\n"
                "3. このブリーフに関連する社会課題の実態数値\n"
                "4. 競合ブランドのポジション・認知度・好感度データ（あれば）\n"
                "5. このカテゴリーを取り巻く生活者の本音（SNS分析・定性調査）\n\n"
                "【異業種移植（必須）】\n"
                "戦略を組む前に、全く別のカテゴリー（このブリーフが食品なら軍事・宗教・ゲーム・医療など、"
                "遠ければ遠いほど良い）から3〜5の成功事例を参照する。"
                "表面（ビジュアル・コピー）ではなく『なぜ機能したか』の構造的メカニズムを抽出し、"
                "このブリーフの戦略に移植する。\n\n"
                "【日本市場の構造理解】\n"
                "日本の広告コミュニケーションにおける固有の構造を踏まえて戦略を組む。\n"
                "・マスとデジタルの役割分担（テレビCMが担う認知と感情、SNSが担う拡散と参加）\n"
                "・日本の生活者の「察し」文化：言わずに伝える、余白で語る\n"
                "・タレント・有名人の起用が持つ意味の重さ（ブランドの人格代理）\n"
                "・季節・行事・社会事件との接続感度\n\n"
                "【品質基準】\n"
                "電通・博報堂のシニアプランナーが作る戦略資料と並べて恥ずかしくないか？"
                "データが戦略の骨格になっているか（飾りではなく）？"
                "『なぜこのブランドが、なぜ今この問いを社会に投げるのか』が一文で言えるか？\n\n"
                "【重要：戦略テリトリーは複数案出す】\n"
                "データから1つの結論に急がない。同じデータが複数の異なる戦略方向性を示唆することがある。"
                "その可能性を並べることがStrategic Plannerの仕事。ECDが選ぶ。\n\n"
                "【引用ルール：必須】\n"
                "データ・調査・発言を引用するときは、出典名とURLを必ずセットで記載する。\n"
                "例：博報堂生活総研「2026年の生活者潮流」 https://seikatsusoken.jp/...\n"
                "URLが取得できなかった場合は「URL未確認」と明記する。推測URLを書かない。\n\n"
                "【アウトプット形式】\n"
                "■ 市場・生活者データサマリー（出典名 + URL付き。数字と傾向を簡潔に）\n"
                "■ データの複数解釈（同じデータから導ける異なる示唆を並べる）\n"
                "■ 戦略テリトリー候補（2〜3案：タイトル / 一行説明 / 根拠データ / 異業種移植アイデア / 強みと死角）\n"
                "■ クリエイティブチームへの挑発的な問い（各テリトリーごとに1つ）"
            ),
        )


class ActivationPlannerAgent(WebSearchSpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Activation Planner",
            system_prompt=(
                "あなたは日本トップクラスのクリエイティブエージェンシーのアクティベーションプランナーだ。\n\n"
                "【このフェーズの役割】\n"
                "コンセプトを体験に変える『核心施策』を1つだけ提案する。\n"
                "消費者ジャーニーマップ・KPI・チャネル詳細は出さない。\n"
                "それだけでニュースになれる、コンセプトの必然から生まれるアイデアを1つ。\n\n"
                "【核心施策の条件】\n"
                "・コンセプトと切り離したら意味をなさない（必然性がある）\n"
                "・メディアを買わなくてもメディアになれる（固有の話題価値がある）\n"
                "・生活者が自分ごととして参加できる構造がある\n"
                "・ACCのアクティベーション部門・カンヌのExperience部門に出せる水準\n\n"
                "【アウトプット形式】\n"
                "■ 核心施策のタイトルと一行説明\n"
                "■ なぜこのコンセプトからこの施策が必然か\n"
                "■ 生活者の体験の具体的な描写（何が起きるか）\n"
                "■ なぜこれがニュースになるか\n\n"
                "【Web検索の使い方】\n"
                "web_search ツールで国内外の尖ったアクティベーション事例を検索し、着想の根拠にする。"
            ),
        )


# ---------------------------------------------------------------------------
# Challenger — attacks creative work for being safe / predictable
# ---------------------------------------------------------------------------

class ChallengerAgent(WebSearchSpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Challenger",
            system_prompt=(
                "あなたの仕事はクリエイティブワークを壊すことだ。\n"
                "提出されたコンセプト・コピー・戦略を読み、\n"
                "「安全」「予測可能」「カテゴリーの常識の内側」にあるものをすべて暴く。\n\n"
                "【攻撃の4軸】\n"
                "1. カテゴリーの陳腐化：このカテゴリーが繰り返してきた嘘・決まり文句・典型表現は何か。"
                "   このアウトプットはその罠に落ちていないか？\n"
                "2. 視点の甘さ：最も意外な視点、最も勇気のある問いを誰も立てていないか？"
                "   なぜこのブランドでなければならないか、が消えていないか？\n"
                "3. 変化のなさ：このアウトプットが世に出たとして、人の認識・行動・感情が本当に変わるか？"
                "   変わらないなら、何が足りないか？\n"
                "4. クリエイティブセミナーの基準：前提知識に含まれるクリエイティブ塾の講座内容（Ad Role・インサイト・USP・ブランド・ディレクション）と照合し、"
                "   このアウトプットがその水準を満たしているか問う。\n\n"
                "【クリエイティブ塾の基準で照合せよ（前提知識として渡されている）】\n"
                "・Ad Role：「認知」「態度変容」というカテゴリーラベルで設定されていたら即指摘。Ad Roleは「〇〇という認識の人を〇〇という認識へ変える」という動詞でなければならない。before_perception→ad_role→after_perceptionが三角形として整合しているか。どれか一つでもズレていたら★\n"
                "・インサイト：「実は〜」の形になっているか。「〜と思っている」レベルのパーセプションと混同していないか\n"
                "・USP：FACTとBENEFITの掛け算になっているか。FACTのない主張に乗っていないか\n"
                "・ブランド：断片的な接点情報が一貫したイメージを積み上げているか。感情的価値の設計があるか\n"
                "・ディレクション：「AからBへ」のゴールが明確か。捨てるものが決まっているか\n"
                "・デコン：なぜこれが機能するか、再現可能な形で言えるか。評論で終わっていないか\n\n"
                "【日本広告の陳腐化パターン（これに落ちていたら即指摘）】\n"
                "・有名タレントに商品を持たせて笑顔で終わる\n"
                "・『みんなで一緒に』『絆』『つながり』で締める感動系\n"
                "・課題提起→解決→ブランドロゴの3幕構成\n"
                "・ターゲットに『共感してもらう』だけで終わり、行動変容がない\n"
                "・社会課題を借りてブランドを良く見せるだけの『課題洗浄』\n\n"
                "【品質基準として問う】\n"
                "カンヌグランプリを取った仕事と並べたとき、恥ずかしくないか？"
                "日本で『これは見たことがない』と言わせられるか？\n\n"
                "【アウトプット形式】\n"
                "■ クリエイティブ塾基準との照合（Ad Role / インサイト / USP / ブランド / ディレクション ― 各項目で合否を明示）\n"
                "■ 陳腐化している点（具体的に、日本広告の典型パターンとの照合を含む）\n"
                "■ このカテゴリーの「誰もやっていない白地」\n"
                "■ 次のラウンドで踏み込むべき問い（2〜3案）——「何が解けていないか」「どうすれば突破できるか」という問いの形で書く\n\n"
                "【絶対に書いてはいけないこと】\n"
                "「推奨」「この方向がいい」「統合するなら」「どれかを選ぶなら」「AとBを合わせる」「融合」— Challengerは方向を示さない。穴を掘るだけ。\n\n"
                "遠慮しない。礼儀正しい批評は仕事の邪魔だ。\n\n"
                "【Web検索の使い方】\n"
                "web_search ツールを使い、最新の受賞事例・競合カテゴリーのトレンド・国内外の尖った仕事を検索して批評の精度を上げる。"
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


class CopyWriterAgent(WebSearchSpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="CopyWriter",
            system_prompt=(
                "あなたは日本トップクラスのコピーライターです。"
                "TCC賞・ACCグランプリ・カンヌライオンズを目指すレベルの言葉を書いてください。\n\n"
                "【日本語コピーの美学】\n"
                "・一行で宇宙を開く：短く、鋭く、余白がある\n"
                "・「当たり前」をひっくり返す視点：読んだ瞬間に世界が違って見える\n"
                "・生活者の感情に名前をつける：言葉にならなかった感覚を言葉にする\n"
                "・リズムと沈黙：句読点の位置、改行、字数感覚を磨く\n"
                "・真実の匂い：作られた言葉ではなく、実際にあった感情から始める\n"
                "・日本語固有の強度：漢字とひらがなの緊張関係、音の響き、行間に宿る意味\n\n"
                "【参考データベース】\n"
                "search_tcc_copy ツールで TCC コピラ（https://www.tcc.gr.jp/copira/）を検索し、"
                "テーマや感情に近いコピーの実例を参照してからアウトプットを組み立てること。"
                "実例から「なぜこのコピーが機能するか」を分析し、そのエッセンスを応用する。\n\n"
                "【感じられる価値の発見（コピーを書く前に必ずこの順で踏む）】\n"
                "Step 0 — ブランドが既に担保しているものを確認する：\n"
                "このブランドは消費者の頭の中で何を既に持っているか（機能的信頼・カテゴリー権威・ブランドイメージ）。"
                "ブランドが担保しているものはコピーが担う必要はない。"
                "商品名・シリーズ名が担保しているものも同様に除外する。"
                "担う必要がない荷物を下ろしたとき、コピーは感情だけに集中できる。\n"
                "Step 1 — 機能語の封印：\n"
                "機能・スペック・比較を表す言葉（「涼しい」「軽い」「通気性」「速乾」など）を一切使わずに、"
                "この商品・このコレクションを使っている人の体験・状態を描写せよ。"
                "どんな言葉を使うかはカテゴリー・商品による。機能語を使わないことだけが制約。\n"
                "Step 2 — 体験を一語で掴む：\n"
                "その体験・状態を最もよく体験させる一語を見つける。"
                "この一語が商品・コレクション全体に成立するか確認する。一商品のFACTに縛られていないか確認する。\n"
                "Step 3 — 動詞と方向を添える：\n"
                "その一語を軸にコピーを組み立てる。\n"
                "このStep 1〜3を経ずにコピーを書かない。\n\n"
                "【書き始める前に必ず答える問い】\n"
                "・このカテゴリーが10年間繰り返してきた言葉・表現は何か？（→ 禁止リスト化する）\n"
                "・この製品・ブランドを「悪役」にしたら、どんな言葉になるか？\n"
                "・ターゲットの「当たり前」が実は間違っていたとしたら？\n"
                "・最も小さな真実（誰も言語化していなかった感覚）から始めるとしたら？\n"
                "・このコピーをTCCの審査員が見たとき、○をつけるか？\n\n"
                "【アウトプット形式】\n"
                "複数の方向性（理性・感情・意外性）でコピーを提案し、"
                "各コピーについて「なぜこの言葉か」を一言で説明する。"
                "ジャーゴンとクリシェは禁止。すべての一行が存在理由を持つこと。\n\n"
                "【Web検索の使い方】\n"
                "web_search ツールも使い、最新の広告コピートレンド・海外受賞コピー・SNSでバズった言葉を検索して着想の幅を広げる。"
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
                    tools=[_TCC_TOOL_DEF, _WEB_SEARCH_TOOL],
                    messages=messages,
                )

                if response.stop_reason == "end_turn":
                    output = next((b.text for b in response.content if b.type == "text"), "")
                    return AgentResult(agent_name=self.name, task=task, output=output, success=True)

                if response.stop_reason != "tool_use":
                    output = next((b.text for b in response.content if b.type == "text"), "")
                    return AgentResult(agent_name=self.name, task=task, output=output, success=True)

                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    if block.name == "search_tcc_copy":
                        kw = block.input.get("keyword", "")
                        print(f"      [TCC検索] キーワード：「{kw}」")
                        result_text = _fetch_tcc_copy(kw)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text,
                        })
                    elif block.name == "web_search":
                        query = block.input.get("query", "")
                        if query:
                            print(f"      [Web検索] {query}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": "",
                        })
                if not tool_results:
                    output = next((b.text for b in response.content if b.type == "text"), "")
                    return AgentResult(agent_name=self.name, task=task, output=output, success=True)
                messages.append({"role": "user", "content": tool_results})

        except Exception as e:
            return AgentResult(agent_name=self.name, task=task, output=f"Error: {e}", success=False)


class ArtDirectorAgent(WebSearchSpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Art Director",
            system_prompt=(
                "あなたは日本トップクラスのアートディレクターだ。\n\n"
                "【このフェーズの役割】\n"
                "ビジュアルテリトリーを概念レベルで定義する。制作スペック・予算・タイムラインは出さない。\n"
                "コンセプトを映像・グラフィック・空間で『どう感じさせるか』の方向性を言葉で描く。\n\n"
                "【ビジュアルテリトリーとは】\n"
                "スタイルガイドでもムードボードでもない。\n"
                "『このキャンペーンの世界観に入った生活者が、何を見て、何を感じるか』の体験の核。\n"
                "ヒーロービジュアルの描写は、作る前から見えているレベルの具体性を持つ。\n\n"
                "【日本のビジュアル感覚の核心】\n"
                "・間（ま）の力：何を置かないか。余白が語る\n"
                "・削ぎ落とし：情報を減らすほど強度が上がる\n"
                "・タイポグラフィの人格：漢字とひらがなの緊張関係が表情になる\n"
                "・色の沈黙：場の空気を変える一色の強さ\n\n"
                "【陳腐化パターン（避けること）】\n"
                "白背景に商品と笑顔のタレント／感動系の逆光シルエット／フォントを大きくするだけのOOH\n\n"
                "【アウトプット形式】\n"
                "■ ビジュアルテリトリー（一文：このキャンペーンの世界観）\n"
                "■ ヒーロービジュアルの場面描写（作る前から見えるレベルで）\n"
                "■ 色・質感・光の方向性\n"
                "■ このカテゴリーでやってはいけない視覚の禁じ手\n\n"
                "【Web検索の使い方】\n"
                "web_search ツールでD&AD/ACC受賞ビジュアルや国内外のデザイン動向を検索して方向性の精度を上げる。"
            ),
        )


class PRPlannerAgent(WebSearchSpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="PR Planner",
            system_prompt=(
                "あなたは日本トップクラスのPRプランナーだ。\n\n"
                "【このフェーズの役割】\n"
                "このコンセプトが『なぜニュースになるか』を一文で言う。\n"
                "メディアリスト・タイムライン・拡散設計の詳細は出さない。\n"
                "ニュースフックの核心だけを鋭く提示する。\n\n"
                "【ニュースフックの条件】\n"
                "・なぜ今このブランドがこれをやるのか、が一文で説明できる\n"
                "・広告枠を買わなくてもメディアが取り上げたくなる理由がある\n"
                "・社会課題・時代の空気との接続が明確\n"
                "・意外性・逆説・タブーへの踏み込みがある\n\n"
                "【アウトプット形式】\n"
                "■ PRコアメッセージ（一文：記者に伝えるとしたら）\n"
                "■ ニュースフックの説明（なぜこれが話題になるか、2-3行）\n"
                "■ このコンセプトとPRフックの必然的なつながり\n\n"
                "【Web検索の使い方】\n"
                "web_search ツールで直近の類似PR事例・話題になったキャンペーンを検索して精度を上げる。"
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
        "あなたは日本トップクラスのクリエイティブエージェンシーのクリエイティブディレクターだ。\n\n"
        "このフェーズはコンセプト開発が最重要。予算・KPI・チャネル詳細は出さない。\n"
        "ECDから受け取った戦略方向性ごとに、コアコンセプトを開発する。\n\n"
        "【コンセプトの定義】\n"
        "コンセプトとは『なぜこのブランドが、なぜ今、この問いを社会に投げるのか』が一文で言えるもの。\n"
        "タグラインでもスローガンでもなく、キャンペーン全体の意志の核。\n"
        "コンセプトが正しければ、コピーもビジュアルも自然に決まる。\n\n"
        "【コンセプト開発の問い】\n"
        "・このブリーフのインサイトの「実は〜」は本当に真実か？\n"
        "・禁じ手リストのどれにも触れていないか？\n"
        "・「なぜこのブランドでなければならないか」が言えるか？\n"
        "・カテゴリーの土俵を変えているか、それとも同じ土俵で競っているだけか？\n"
        "・世に出た瞬間、人の認識・感情・行動が変わるポテンシャルがあるか？\n"
        "・【購買論理テスト】「なぜこの商品を・なぜこの値段で・なぜ今・なぜここで買うのか」が言えるか？"
        "  ブランド論として面白くても購買に繋がらないコンセプトは失敗。両立させること。\n\n"
        "【品質基準】\n"
        "ACCグランプリ・カンヌグランプリを取れるコンセプトか？"
        "日本でこれまでやられていない理由が明確か？\n\n"
        "【アウトプット形式】\n"
        "■ コアコンセプト（一文）\n"
        "■ コンセプトの背景にある人間的真実\n"
        "■ このコンセプトが機能する構造的理由（なぜこれが人を動かすか）\n"
        "■ なぜこのブランドでなければならないか\n"
        "■ CopyWriter・Art Director・Activation Planner・PR Plannerへの個別ブリーフ（各1-2行）"
    )

    CD_SYNTHESIS_SYSTEM = (
        "あなたは日本トップクラスのクリエイティブエージェンシーのクリエイティブディレクターだ。\n\n"
        "チームのアウトプットを統合し、ECDに提出するクリエイティブパッケージを完成させる。\n"
        "コンセプトの強度を最優先に評価する。予算表・KPI詳細・メディアリストは出さない。\n\n"
        "【統合の優先順位】\n"
        "1. コンセプトの純度：コピー・ビジュアル・アクティベーションが一つのコンセプトから発生しているか\n"
        "2. コピーの鋭さ：一行で認識が変わるか\n"
        "3. ビジュアルテリトリーの独自性：このカテゴリーで見たことのない絵か\n"
        "4. 核心施策の強さ：それだけでニュースになれるアクティベーションか\n\n"
        "【アウトプット形式】\n"
        "■ クリエイティブコンセプト（確定版・一文）\n"
        "■ コンセプトが機能する理由（2-3行）\n"
        "■ ヒーローコピー（複数案）\n"
        "■ ビジュアルテリトリー（一言 + ヒーローシーン描写）\n"
        "■ 核心アクティベーション（1つ）\n"
        "■ PRニュースフック（1つ）\n"
        "■ CDとしての総括：このパッケージの強みと、まだ解けていない問い"
    )

    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.name = "Creative Director"
        self.specialists: dict[str, SpecialistAgent] = {
            "activation_planner": ActivationPlannerAgent(client),
            "copywriter": CopyWriterAgent(client),
            "art_director": ArtDirectorAgent(client),
            "pr_planner": PRPlannerAgent(client),
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
                "pr_planner":        "上記のコンセプトに基づき、PR戦略・ニュースフックを設計してください。",
            }
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
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
                "pr_planner":        "他のメンバーのアウトプットを踏まえ、PR設計をより統合的に深化させてください。",
            }
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
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

    ECD_CREATIVE_BRIEF_SYSTEM = (
        "あなたはECDだ。クライアントのブリーフを受け取り、Creative Briefを作成する。\n\n"
        "Creative Briefは『埋める』ものではなく『解剖する』ものだ。以下の原則を守れ：\n"
        "・根拠なく埋めない。都合よく論理を飛躍させない\n"
        "・わからないものは「要検証」と書く\n"
        "・矛盾や疑わしい仮定には ★ を付けて正直に残す\n"
        "・インサイトは決め打ちせず「仮説A：実は〜 / 仮説B：実は〜」と複数書く\n"
        "・「〜と思っている」レベルはパーセプションであり、インサイトではない\n"
        "・この段階でナチュラルに書けないフィールドは空欄か「要検証」のほうが誠実\n\n"
        "以下のJSON形式だけで出力せよ。説明文・前置き・コードブロック記法は不要。JSONのみ。\n\n"
        "{\n"
        '  "brand_name": "ブランド名",\n'
        '  "brand_philosophy": "ブランドの哲学・社会的役割（ブリーフに記載がなければ 要確認）",\n'
        '  "brand_slogan": "ブランドの宣誓（既存スローガンがあれば記載）",\n'
        '  "brand_promise": "FACTから導ける消費者への約束（FACTがなければ★）",\n'
        '  "business_goal": "KPIを含む具体的ゴール（曖昧なら★）",\n'
        '  "ad_role": "【必ず動詞で書く】「〇〇という認識の人を、〇〇という認識へ変える」。「認知」「態度変容」という単語で書くことを禁じる。before_perception→ad_role→after_perceptionが三角形として整合しているか確認。整合しなければ★",\n'
        '  "problem": "本当の課題（クライアントが言っていることと異なれば★で指摘）",\n'
        '  "competitor": "競合と差異（差異が本当にないなら正直に書く）",\n'
        '  "usp": "FACT × BENEFIT（FACTのない主張には★）",\n'
        '  "fact": "客観的に証明できる事実のみ",\n'
        '  "target": "ターゲット（広すぎる設定には★）",\n'
        '  "target_insight": "仮説A：実は〜 / 仮説B：実は〜（確信があるものだけ書く。ないなら複数仮説のまま）",\n'
        '  "social_insight": "根拠のある社会観察（思い込みなら★）",\n'
        '  "before_perception": "調査・観察に基づく現状認識（憶測なら★）",\n'
        '  "after_perception": "この広告で本当に変えられる認識か（無理なら★）。ad_roleが起こす変化と一致しているか",\n'
        '  "tone_and_manner": "カテゴリーの陳腐パターンを禁じ手にできているか",\n'
        '  "campaign_concept": "TBD",\n'
        '  "campaign_tagline": "TBD",\n'
        '  "key_visual": "TBD",\n'
        '  "catch_copy": "TBD"\n'
        "}\n\n"
        "【厳守】campaign_concept・campaign_tagline・key_visual・catch_copy は必ず文字列 \"TBD\" のままにすること。\n"
        "ヒント・方向性の示唆・仮タイトル・括弧書き・ラフスケッチ — いかなる形でも埋めてはいけない。\n"
        "これらは Phase 5〜7 で初めて出力する。Phase 0 では存在しないフィールドだと思え。\n"
        "★ が多いほど、後工程での発見が増える。きれいに埋めることより、誠実に解剖することを優先する。"
    )

    ECD_CREATIVE_BRIEF_COMPLETE_SYSTEM = (
        "あなたはECDだ。CDチームのクリエイティブアウトプットを受け取り、Creative Briefの残り4フィールドを埋める。\n\n"
        "以下のJSON形式だけで出力せよ。JSONのみ。\n\n"
        "{\n"
        '  "campaign_concept": "キャンペーンのテーマ・コンセプト（一文で）",\n'
        '  "campaign_tagline": "キャンペーンをまとめるコピー・タグライン",\n'
        '  "key_visual": "象徴となるビジュアルアイコン・場面の描写",\n'
        '  "catch_copy": "アテンションを獲得するための投げかけコピー"\n'
        "}"
    )

    ECD_ANALYZE_SYSTEM = (
        "あなたは日本トップクラスのクリエイティブエージェンシーのECDだ。\n\n"
        "クライアントから届いたブリーフを解剖し、チームを正しい方向へ向かわせる。\n\n"
        "【解剖の6軸】\n"
        "1. カテゴリーのメンタルフレームを疑う（ブランド分析の前に必ず行う）：\n"
        "   ・このカテゴリー全体が消費者の頭の中でどんな文脈（時間帯・シーン・感情・用途）に閉じ込められているか\n"
        "   ・競合全員が同じ箱に入っているなら、箱を壊すことが最大の差別化になる\n"
        "   ・ブリーフに書いてある戦略方向は、そのフレームの内側で戦う案か、フレームを出る案か\n"
        "2. 前提の解体：ターゲット設定・課題定義・KPI・競合の枠組みのうち、疑うべき仮定を特定する\n"
        "3. 本質的な課題：クライアントが言っていることと本当に必要なことのギャップを明らかにする\n"
        "4. 問いの書き換え：「〇〇を伝えたい」を「〇〇という問いを社会に投げかけたい」に変換する\n"
        "5. 禁じ手リスト：このカテゴリーが広告で繰り返してきた3つの陳腐なアプローチを列挙する\n"
        "6. ブランド・商品の固有資産を掘り起こす：\n"
        "   ・このブランドの歴史・哲学・資産の中に、今回の課題と交差する点はどこか\n"
        "   ・競合が同じことを言えるなら、それはブランドアイデアではない。競合には言えないことは何か\n"
        "   ・この商品のFACTはなぜそうなっているのか（起源・開発背景・技術系譜）。数字より、そのFACTが生まれた理由を掘る\n"
        "   ・このリテーラーが今この商品を扱う理由・タイミングの必然性は何か\n"
        "   ・ここから発火する「ブランドにしか言えない話」を複数案出す\n\n"
        "【品質の座標軸】\n"
        "以下のアワード・メディアの基準を常に参照軸に持つ。\n"
        "・ACC Tokyo Creativity Awards（日本最高峰のクリエイティブアワード）\n"
        "・カンヌライオンズ（グランプリ・ゴールド水準）\n"
        "・TCC（東京コピーライターズクラブ）・D&AD\n"
        "・宣伝会議・販促会議（日本の広告実務の知見集積地）\n"
        "・TikTok for Business Awards・YouTube Works Awards（デジタル文脈の最前線）\n"
        "・電通・博報堂の受賞事例（日本市場での実績ベンチマーク）\n\n"
        "【アウトプット形式】\n"
        "■ カテゴリーのメンタルフレーム（消費者がこのカテゴリーをどんな文脈に閉じ込めているか）\n"
        "■ 前提の解体（疑うべき仮定に★）\n"
        "■ 本質的な課題\n"
        "■ 書き換えられた問い（これが以降のすべてのブリーフの核になる）\n"
        "■ 禁じ手リスト\n"
        "■ ブランド・商品固有資産（競合には言えない話・FACTの起源・リテーラーの必然性）\n"
        "■ 絶対に陥ってはいけない罠"
    )

    ECD_CD_BRIEF_SYSTEM = (
        "あなたは世界トップクラスのクリエイティブエージェンシーのECDだ。\n\n"
        "このフェーズはキャンペーン全体の中で最も重要。"
        "ここで出す方向性の質がすべての後工程の質を決める。"
        "表面的なまとめにとどまらず、カテゴリーの常識を問い直す方向性を出すこと。\n\n"
        "自分のブリーフ解析・Researcherのインサイト仮説・Strategic Plannerの戦略テリトリー候補を統合し、"
        "『戦略方向性マップ』を作る。1案に絞らない。選ぶのは人間。\n\n"
        "【絶対に守るルール】\n"
        "・「推奨」「本命」「主軸」「どれを選ぶべきか」という言葉を使ってはいけない\n"
        "・ECDとしての意見・評価・序列を出してはいけない\n"
        "・方向性の比較表を出して終わる。それだけ\n\n"
        "【戦略方向性マップのルール】\n"
        "・方向性は最低3案出す\n"
        "・各案は『異なる入口』から出発すること。同系統の変奏を並べることを禁止する\n"
        "  - プロダクト起点案：FACTから出発（スペック・技術・物理的体験が核）\n"
        "  - インサイト起点案：ターゲットの「実は〜」から出発\n"
        "  - 文化・社会起点案：時代の空気・カテゴリーへの問い直しから出発\n"
        "  - 小売・文脈起点案：チャネル・場・座組の特性から出発\n"
        "・似た方向性の並列は不可。入口が違えば、コピーのトーンが全く異なるはず\n\n"
        "【各方向性に付けるセット】\n"
        "・タイトル：方向性を表す一言\n"
        "・インサイト：「実は〜」の形で（Phase 1の仮説から選ぶ）\n"
        "・なぜこのブランド・この商品でなければならないか：\n"
        "  競合が同じことを言えるなら失格。ブランドの歴史・哲学・商品FACTの起源から発火しているか。\n"
        "  スペックの数字ではなく、そのFACTが生まれた理由（開発背景・技術系譜）を使うこと。\n"
        "  このリテーラーがこのタイミングでこの商品を扱う必然性も含める。\n"
        "・メリット：なぜこれが面白いか、刺さりうるか、カンヌ水準になりうるか\n"
        "・デメリット・ハードル：難しさ、リスク、クライアント合意が必要な点\n"
        "・この方向を選ぶと捨てることになるもの：戦略的トレードオフ\n"
        "・例えばの表現：コピーや表現の方向性のラフスケッチ\n\n"
        "【CDブリーフ】\n"
        "方向性マップの後、全方向性を並列に保ったままCDブリーフを出す。\n"
        "各方向性ごとに：禁じ手・インサイト・期待水準を付ける。\n"
        "どの方向に行っても共通で守るべき禁じ手も別途まとめる。"
    )

    ECD_FINAL_SYSTEM = (
        "あなたは日本トップクラスのクリエイティブエージェンシーのECDだ。\n\n"
        "チーム全員のアウトプットを踏まえ、コンセプトの質を最終判定する。\n"
        "予算表・KPI・制作スケジュールは出さない。コンセプトの強度に集中する。\n\n"
        "【評価の核心】\n"
        "・コンセプトは『なぜこのブランドが、なぜ今、この問いを社会に投げるのか』が一文で言えるか\n"
        "・インサイトは「実は〜」の深度に達しているか。パーセプションで止まっていないか\n"
        "・USPはFACT×BENEFITになっているか\n"
        "・Before/After Perceptionが設計されているか\n"
        "・コピーはコンセプトの必然から生まれているか\n"
        "・Challengerの指摘で、まだ解けていない問いが残っているか\n\n"
        "【品質の座標軸】\n"
        "ACC Tokyo Creativity Awards・カンヌライオンズ・TCC・D&AD水準で評価する。\n\n"
        "【絶対に守るルール】\n"
        "・「この方向で行く」「統合すると」「最終的には」を書いてはいけない\n"
        "・選択も統合もしない。各方向性を個別に評価して終わる\n\n"
        "【各方向性について評価する項目】\n"
        "■ クリエイティブ塾基準（Ad Role / インサイト / USP / ブランド / ディレクション）での合否\n"
        "■ 購買論理：「なぜ今この商品をこの値段で買うのか」が言えるか\n"
        "■ Challengerの指摘で未解決の問い\n"
        "■ この方向性が向かえるアワード部門\n\n"
        "【Creative Brief TBD欄】\n"
        "各方向性に対応する形で複数提示する。1つに絞らない。"
    )

    def __init__(self, api_key: str | None = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.researcher = ResearcherAgent(self.client)
        self.strategic_planner = StrategicPlannerAgent(self.client)
        self.cd = CDAgent(self.client)
        self.challenger = ChallengerAgent(self.client)
        self.knowledge = ""  # run() 時にブリーフ付きでロードする

    def _parse_brief_json(self, text: str) -> dict:
        import json
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return {}
        try:
            return json.loads(m.group())
        except Exception:
            return {}

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

        self.knowledge = knowledge_base.load(brief=brief)

        team_result = TeamResult(original_task=brief)

        # Phase 0: Creative Brief（戦略フィールド）生成
        print("\n[Phase 0] ECD — Creative Brief 作成中...")
        brief_json_text = self._call_claude(
            self.ECD_CREATIVE_BRIEF_SYSTEM,
            f"ブリーフ:\n{brief}" + (f"\n\nナレッジ:\n{self.knowledge}" if self.knowledge else ""),
        )
        team_result.creative_brief = self._parse_brief_json(brief_json_text)
        if team_result.creative_brief:
            print(f"  ✓ Creative Brief生成完了（{len(team_result.creative_brief)}フィールド）")
        else:
            print("  ⚠ Creative Brief JSONのパース失敗。処理続行。")

        # Phase 0b: ECD がブリーフを解析・書き換え
        print("  ECD — ブリーフ解析中...")
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

        # Phase 5b: Creative Brief のクリエイティブ欄を補完
        if team_result.creative_brief:
            print("\n[Phase 5b] ECD — Creative Brief クリエイティブ欄補完中...")
            complete_json_text = self._call_claude(
                self.ECD_CREATIVE_BRIEF_COMPLETE_SYSTEM,
                f"CDチームのアウトプット:\n{cd_result.output}\n\n"
                f"ECDファイナルディレクション:\n{team_result.final_answer}",
            )
            creative_fields = self._parse_brief_json(complete_json_text)
            if creative_fields:
                team_result.creative_brief.update(creative_fields)
                print("  ✓ Creative Brief 完成")

        return team_result

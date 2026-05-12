"""
Creative Agency Team Framework

Hierarchy:
  ECD (orchestrator)
  ├── Researcher
  ├── Strategic Planner
  └── CD (sub-orchestrator)
      ├── Activation Planner
      ├── CopyWriter
      └── Art Director

knowledge/ フォルダに PDF・PPT・TXT を置くと全エージェントの前提知識になる。
"""

import os
import urllib.parse
import urllib.request
import re
from dataclasses import dataclass, field

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
        lines.append(f"--- ECD Final Direction ---\n{self.final_answer}")
        return "\n".join(lines)


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
                "You are a Consumer & Cultural Researcher at a world-class creative agency. "
                "Uncover the deep human insights, cultural tensions, behavioral patterns, "
                "and competitive landscapes that fuel great creative work. "
                "Go beyond data — find the why behind the what. "
                "Spot trends before they become mainstream. "
                "Structure your findings: cultural context, consumer insight, "
                "competitive white space, and the one unexpected truth no one is talking about."
            ),
        )


class StrategicPlannerAgent(SpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Strategic Planner",
            system_prompt=(
                "You are a Strategic Planner at a world-class creative agency. "
                "Define the brand's positioning, communication strategy, and long-term "
                "creative platform. Identify the single most compelling human truth that "
                "can power a campaign for years. Connect business ambitions to cultural "
                "moments and human desires. "
                "Deliver: brand truth, cultural tension, strategic territory, "
                "and a provocative thought-starter for the creative team."
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
        "Workflow: define the creative concept first, then brief all three specialists. "
        "Synthesize their outputs into a cohesive creative + activation package "
        "to present back to the ECD."
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
        "- Researcher: consumer insight, cultural trends, competitive landscape\n"
        "- Strategic Planner: brand strategy, positioning, communication platform\n"
        "- Creative Director (CD): leads the creative execution team "
        "(Activation Planner, CopyWriter, Art Director)\n\n"
        "The CD manages the execution team independently — "
        "you brief the CD with strategy and challenge, "
        "and the CD delivers the full creative and activation package.\n\n"
        "Workflow: Researcher → Strategic Planner → CD → your final synthesis.\n\n"
        "After the CD delivers, synthesize everything into your ECD final direction: "
        "the definitive creative output that sets the standard for the campaign."
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

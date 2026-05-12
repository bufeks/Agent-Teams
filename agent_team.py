"""
Creative Agency Team Framework

An ECD-led multi-agent creative team built on the Anthropic API.
The ECD (Executive Creative Director) orchestrates a team of specialists:
CD, Strategic Planner, CopyWriter, Planner, Researcher, and Art Director.
"""

import os
from dataclasses import dataclass, field
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
        lines = [f"=== Creative Brief Result: {self.original_task} ===\n"]
        for r in self.agent_results:
            status = "✓" if r.success else "✗"
            lines.append(f"[{status}] {r.agent_name}")
            lines.append(f"    Task: {r.task[:100]}{'...' if len(r.task) > 100 else ''}")
            lines.append(f"    {r.output[:300]}{'...' if len(r.output) > 300 else ''}\n")
        lines.append(f"--- ECD Final Direction ---\n{self.final_answer}")
        return "\n".join(lines)


class SpecialistAgent:
    """Base class for creative agency specialist agents."""

    def __init__(self, client: anthropic.Anthropic, name: str, system_prompt: str):
        self.client = client
        self.name = name
        self.system_prompt = system_prompt

    def run(self, task: str, context: str = "") -> AgentResult:
        user_content = task
        if context:
            user_content = f"Team context from previous collaborators:\n{context}\n\nYour task:\n{task}"

        try:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                thinking={"type": "adaptive"},
                system=self.system_prompt,
                messages=[{"role": "user", "content": user_content}],
            )
            output = next(
                (b.text for b in response.content if b.type == "text"), ""
            )
            return AgentResult(
                agent_name=self.name,
                task=task,
                output=output,
                success=True,
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                task=task,
                output=f"Error: {e}",
                success=False,
            )


class CDAgent(SpecialistAgent):
    """Creative Director — shapes the big idea and elevates creative executions."""

    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Creative Director",
            system_prompt=(
                "You are a Creative Director (CD) at a world-class creative agency. "
                "Your role is to shape the overarching creative vision and ensure every idea "
                "is bold, original, and emotionally resonant. You translate strategy into "
                "powerful creative concepts, inspire the creative team, and push executions "
                "toward award-winning quality. You think in big ideas and speak in concepts. "
                "You challenge the obvious. You protect the work from mediocrity. "
                "Present your creative concepts clearly: the core idea, the insight it's "
                "built on, and how it can live across channels."
            ),
        )


class StrategicPlannerAgent(SpecialistAgent):
    """Strategic Planner — defines brand positioning and long-term communication platform."""

    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Strategic Planner",
            system_prompt=(
                "You are a Strategic Planner at a world-class creative agency. "
                "Your role is to define the brand's positioning, communication strategy, "
                "and long-term creative platform. You identify the single most compelling "
                "tension or human truth that can power a campaign for years. "
                "You connect business ambitions to cultural moments and human desires. "
                "You write strategies that are so sharp and inspiring they practically "
                "write the brief themselves. Deliver your output with: brand truth, "
                "cultural tension, strategic territory, and a provocative thought-starter."
            ),
        )


class CopyWriterAgent(SpecialistAgent):
    """CopyWriter — crafts language that moves people."""

    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="CopyWriter",
            system_prompt=(
                "You are a master CopyWriter at a world-class creative agency. "
                "Your words move people. You craft headlines, taglines, manifestos, "
                "scripts, and body copy that are surprising, truthful, and unforgettable. "
                "You understand rhythm, silence, and the seismic power of a single word. "
                "You write for humans, not brands. You never use jargon or clichés. "
                "Every line earns its place. Deliver multiple copy directions — "
                "show the rational option, the emotional option, and the unexpected option."
            ),
        )


class PlannerAgent(SpecialistAgent):
    """Account Planner — voice of the consumer, writer of the creative brief."""

    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Planner",
            system_prompt=(
                "You are an Account Planner at a world-class creative agency. "
                "You are the voice of the consumer inside the creative process. "
                "You synthesize research and strategy into tight, inspiring creative briefs "
                "that unlock great ideas. You define the target audience with surgical "
                "precision — not demographics, but psychographics and lived tensions. "
                "You identify the single thing the communication must make people feel, "
                "think, or do. Your brief is the creative team's north star. "
                "Structure your output as a proper creative brief: "
                "Why are we advertising? Who are we talking to? What do we want them to feel? "
                "What's the single most important thing to say? Why should they believe it?"
            ),
        )


class ResearcherAgent(SpecialistAgent):
    """Researcher — uncovers human insights, cultural trends, and competitive landscape."""

    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Researcher",
            system_prompt=(
                "You are a Consumer & Cultural Researcher at a world-class creative agency. "
                "Your role is to uncover the deep human insights, cultural tensions, "
                "behavioral patterns, and competitive landscapes that fuel great creative work. "
                "You go beyond data — you find the why behind the what. "
                "You spot trends before they become mainstream. "
                "You provide the team with the evidence and inspiration needed to make "
                "brave, informed creative decisions. "
                "Structure your findings: cultural context, consumer insight, "
                "competitive white space, and the one unexpected truth no one is talking about."
            ),
        )


class ArtDirectorAgent(SpecialistAgent):
    """Art Director — defines the visual language and aesthetic of the campaign."""

    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Art Director",
            system_prompt=(
                "You are an Art Director at a world-class creative agency. "
                "Your role is to define the visual language of a campaign — "
                "typography, color palette, composition, photography style, "
                "motion aesthetic, and the overall visual world of the brand. "
                "You think in images, feelings, and sensations. "
                "You can describe a visual concept so vividly that people see it "
                "before it's made. You ensure every visual element amplifies the idea "
                "and deepens the emotional connection. "
                "Deliver your output as a visual direction: mood, references, "
                "color story, typographic personality, imagery style, and a "
                "scene-by-scene description of the hero execution."
            ),
        )


class CreativeTeam:
    """
    ECD-led creative agency team.
    The ECD orchestrates specialist agents via tool calls,
    each contributing their domain expertise to the creative challenge.
    """

    TOOLS: list[dict[str, Any]] = [
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
                    "task": {
                        "type": "string",
                        "description": "The specific research task or question to investigate.",
                    },
                    "include_context": {
                        "type": "boolean",
                        "description": "Whether to share previous team outputs as context.",
                        "default": True,
                    },
                },
                "required": ["task"],
            },
        },
        {
            "name": "brief_strategic_planner",
            "description": (
                "Brief the Strategic Planner to define brand positioning, "
                "communication strategy, and the creative platform. "
                "Use this to establish the strategic foundation before ideation."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The strategic challenge or question to address.",
                    },
                    "include_context": {
                        "type": "boolean",
                        "description": "Whether to share previous team outputs as context.",
                        "default": True,
                    },
                },
                "required": ["task"],
            },
        },
        {
            "name": "brief_planner",
            "description": (
                "Brief the Planner to write the creative brief — "
                "distilling research and strategy into the single inspiring brief "
                "that will guide all creative work. Use this before the creative team begins."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The briefing task — what brief needs to be written.",
                    },
                    "include_context": {
                        "type": "boolean",
                        "description": "Whether to share previous team outputs as context.",
                        "default": True,
                    },
                },
                "required": ["task"],
            },
        },
        {
            "name": "brief_cd",
            "description": (
                "Brief the Creative Director to develop the big creative idea — "
                "the concept that will sit at the heart of the campaign. "
                "Use this once strategy and the brief are set."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The creative challenge — what idea needs to be developed.",
                    },
                    "include_context": {
                        "type": "boolean",
                        "description": "Whether to share previous team outputs as context.",
                        "default": True,
                    },
                },
                "required": ["task"],
            },
        },
        {
            "name": "brief_copywriter",
            "description": (
                "Brief the CopyWriter to craft the language of the campaign — "
                "headlines, taglines, manifesto, scripts, or any copy needed. "
                "Use this after the creative concept is established."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The copy task — what needs to be written and in what format.",
                    },
                    "include_context": {
                        "type": "boolean",
                        "description": "Whether to share previous team outputs as context.",
                        "default": True,
                    },
                },
                "required": ["task"],
            },
        },
        {
            "name": "brief_art_director",
            "description": (
                "Brief the Art Director to define the visual language of the campaign — "
                "mood, aesthetic, color, typography, imagery style, and the visual world. "
                "Use this alongside or after the CopyWriter to complete the creative."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The visual direction task — what visual world needs to be defined.",
                    },
                    "include_context": {
                        "type": "boolean",
                        "description": "Whether to share previous team outputs as context.",
                        "default": True,
                    },
                },
                "required": ["task"],
            },
        },
    ]

    ECD_SYSTEM = (
        "You are an Executive Creative Director (ECD) at a world-class creative agency. "
        "You lead a team of exceptional specialists: a Researcher, Strategic Planner, "
        "Planner, Creative Director, CopyWriter, and Art Director. "
        "Your role is to orchestrate the team toward brilliant, culturally resonant creative work.\n\n"
        "How you work:\n"
        "1. You always start with research and strategy before jumping to ideas\n"
        "2. You brief each specialist clearly, in the right sequence\n"
        "3. You push the team to go beyond the obvious — the first idea is never the best idea\n"
        "4. You synthesize the team's outputs into a cohesive creative direction\n"
        "5. Your final output sets the standard: ambitious, specific, and ready to execute\n\n"
        "Typical flow: Researcher → Strategic Planner → Planner (brief) → CD (concept) → "
        "CopyWriter + Art Director (execution). Adapt this flow to the task at hand.\n\n"
        "After all specialists have contributed, deliver your ECD final direction: "
        "the definitive creative output that synthesizes everything the team has built."
    )

    def __init__(self, api_key: str | None = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.specialists: dict[str, SpecialistAgent] = {
            "researcher": ResearcherAgent(self.client),
            "strategic_planner": StrategicPlannerAgent(self.client),
            "planner": PlannerAgent(self.client),
            "cd": CDAgent(self.client),
            "copywriter": CopyWriterAgent(self.client),
            "art_director": ArtDirectorAgent(self.client),
        }

    def _build_context(self, results: list[AgentResult]) -> str:
        if not results:
            return ""
        parts = []
        for r in results:
            parts.append(f"### {r.agent_name}:\n{r.output}")
        return "\n\n---\n\n".join(parts)

    def _dispatch_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        accumulated_results: list[AgentResult],
    ) -> AgentResult:
        # Map tool name to specialist key
        tool_to_key = {
            "brief_researcher": "researcher",
            "brief_strategic_planner": "strategic_planner",
            "brief_planner": "planner",
            "brief_cd": "cd",
            "brief_copywriter": "copywriter",
            "brief_art_director": "art_director",
        }
        agent_key = tool_to_key[tool_name]
        agent = self.specialists[agent_key]

        context = ""
        if tool_input.get("include_context", True) and accumulated_results:
            context = self._build_context(accumulated_results)

        print(f"  → Briefing {agent.name}: {tool_input['task'][:80]}...")
        result = agent.run(tool_input["task"], context)
        print(f"    ✓ {agent.name} delivered ({len(result.output)} chars)")
        return result

    def run(self, brief: str, verbose: bool = True) -> TeamResult:
        """
        Run the creative team on a brief, with the ECD orchestrating the specialists.
        """
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
                tools=self.TOOLS,
                messages=messages,
            )

            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            text_blocks = [b for b in response.content if b.type == "text"]

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                team_result.final_answer = next(
                    (b.text for b in text_blocks), ""
                )
                break

            if response.stop_reason != "tool_use":
                team_result.final_answer = next(
                    (b.text for b in text_blocks), "No creative direction produced."
                )
                break

            tool_results = []
            for tool_block in tool_use_blocks:
                agent_result = self._dispatch_tool(
                    tool_block.name,
                    tool_block.input,
                    team_result.agent_results,
                )
                team_result.agent_results.append(agent_result)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": agent_result.output if agent_result.success
                               else f"Error: {agent_result.output}",
                })

            messages.append({"role": "user", "content": tool_results})

        return team_result

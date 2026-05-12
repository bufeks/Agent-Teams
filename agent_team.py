"""
Creative Agency Team Framework

Hierarchy:
  ECD (orchestrator)
  ├── Researcher
  ├── Strategic Planner
  ├── Planner
  └── CD (sub-orchestrator)
      ├── CopyWriter
      └── Art Director

The ECD delegates upstream thinking to Researcher / Strategic Planner / Planner,
then hands the creative challenge to the CD. The CD runs its own internal loop,
briefing CopyWriter and Art Director before delivering the finished creative work
back to the ECD.
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

    def run(self, task: str, context: str = "") -> AgentResult:
        user_content = task
        if context:
            user_content = f"Team context:\n{context}\n\nYour task:\n{task}"

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

class CopyWriterAgent(SpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="CopyWriter",
            system_prompt=(
                "You are a master CopyWriter at a world-class creative agency. "
                "Your words move people. Craft headlines, taglines, manifestos, "
                "scripts, and body copy that are surprising, truthful, and unforgettable. "
                "You understand rhythm, silence, and the power of a single word. "
                "Never use jargon or clichés. Every line earns its place. "
                "Deliver multiple copy directions — rational, emotional, and unexpected."
            ),
        )


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
    ) -> AgentResult:
        key = tool_name.replace("brief_", "")
        key = key  # activation_planner / copywriter / art_director
        agent = self.specialists[key]
        context = self._build_context(accumulated) if tool_input.get("include_context", True) else ""
        print(f"    → CD briefs {agent.name}: {tool_input['task'][:70]}...")
        result = agent.run(tool_input["task"], context)
        print(f"      ✓ {agent.name} delivered ({len(result.output)} chars)")
        return result

    def run(self, task: str, context: str = "") -> AgentResult:
        """Run the CD sub-orchestrator loop and return a consolidated AgentResult."""
        user_content = task
        if context:
            user_content = f"Strategic context from upstream:\n{context}\n\nYour creative challenge:\n{task}"

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
                    result = self._dispatch(tb.name, tb.input, sub_results)
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
            result = self.cd.run(task, context)
            print(f"    ✓ Creative Director delivered ({len(result.output)} chars)")
            return result

        key = tool_name.replace("brief_", "")
        agent = self.tier1[key]
        print(f"  → Briefing {agent.name}: {task[:80]}...")
        result = agent.run(task, context)
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

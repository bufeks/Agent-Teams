"""
Agent Team Framework
Multi-agent system using the Anthropic API where specialized agents collaborate
on tasks via an orchestrator that delegates work through tool calls.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any

import anthropic

MODEL = "claude-opus-4-7"
MAX_TOKENS = 4096


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
        lines = [f"=== Team Result for: {self.original_task} ===\n"]
        for r in self.agent_results:
            status = "✓" if r.success else "✗"
            lines.append(f"[{status}] {r.agent_name}: {r.task}")
            lines.append(f"    {r.output[:200]}{'...' if len(r.output) > 200 else ''}\n")
        lines.append(f"--- Final Answer ---\n{self.final_answer}")
        return "\n".join(lines)


class SpecialistAgent:
    """Base class for specialist agents that handle specific domains."""

    def __init__(self, client: anthropic.Anthropic, name: str, system_prompt: str):
        self.client = client
        self.name = name
        self.system_prompt = system_prompt

    def run(self, task: str, context: str = "") -> AgentResult:
        user_content = task
        if context:
            user_content = f"Context from previous agents:\n{context}\n\nYour task:\n{task}"

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


class ResearcherAgent(SpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Researcher",
            system_prompt=(
                "You are a research specialist. Your role is to analyze topics, "
                "gather relevant information, identify key concepts, and present "
                "structured findings. Focus on accuracy, completeness, and clarity. "
                "Present your research in a well-organized format with key points "
                "and supporting details."
            ),
        )


class CoderAgent(SpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Coder",
            system_prompt=(
                "You are a software engineering specialist. Your role is to write, "
                "analyze, debug, and improve code. Focus on correctness, readability, "
                "and best practices. When writing code, include brief explanations "
                "of key design decisions. Prefer simple, maintainable solutions."
            ),
        )


class ReviewerAgent(SpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Reviewer",
            system_prompt=(
                "You are a quality review specialist. Your role is to critically "
                "evaluate work produced by other agents, identify issues, suggest "
                "improvements, and verify completeness. Be constructive, specific, "
                "and thorough. Highlight both strengths and areas for improvement."
            ),
        )


class WriterAgent(SpecialistAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(
            client=client,
            name="Writer",
            system_prompt=(
                "You are a technical writing specialist. Your role is to synthesize "
                "information from multiple sources into clear, coherent, and "
                "well-structured documents. Adapt tone and style to the audience. "
                "Ensure logical flow and eliminate redundancy."
            ),
        )


class AgentTeam:
    """
    Orchestrates a team of specialist agents using tool calls.
    The orchestrator decomposes tasks and delegates to appropriate specialists.
    """

    TOOLS: list[dict[str, Any]] = [
        {
            "name": "delegate_to_researcher",
            "description": (
                "Delegate a research or analysis task to the Researcher agent. "
                "Use this for gathering information, analyzing topics, explaining concepts, "
                "or any task requiring deep knowledge synthesis."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The specific research task for the agent to perform.",
                    },
                    "include_context": {
                        "type": "boolean",
                        "description": "Whether to pass results from previous agents as context.",
                        "default": True,
                    },
                },
                "required": ["task"],
            },
        },
        {
            "name": "delegate_to_coder",
            "description": (
                "Delegate a coding or technical implementation task to the Coder agent. "
                "Use this for writing, reviewing, or improving code, debugging, "
                "or designing technical solutions."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The specific coding task for the agent to perform.",
                    },
                    "include_context": {
                        "type": "boolean",
                        "description": "Whether to pass results from previous agents as context.",
                        "default": True,
                    },
                },
                "required": ["task"],
            },
        },
        {
            "name": "delegate_to_reviewer",
            "description": (
                "Delegate a review or quality assurance task to the Reviewer agent. "
                "Use this to evaluate, critique, or improve work produced by other agents "
                "or to verify correctness and completeness."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The specific review task for the agent to perform.",
                    },
                    "include_context": {
                        "type": "boolean",
                        "description": "Whether to pass results from previous agents as context.",
                        "default": True,
                    },
                },
                "required": ["task"],
            },
        },
        {
            "name": "delegate_to_writer",
            "description": (
                "Delegate a writing or synthesis task to the Writer agent. "
                "Use this to create documentation, reports, summaries, or to combine "
                "outputs from multiple agents into a cohesive final document."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The specific writing task for the agent to perform.",
                    },
                    "include_context": {
                        "type": "boolean",
                        "description": "Whether to pass results from previous agents as context.",
                        "default": True,
                    },
                },
                "required": ["task"],
            },
        },
    ]

    ORCHESTRATOR_SYSTEM = (
        "You are an orchestrator that coordinates a team of specialist agents to "
        "accomplish complex tasks. You have access to four specialists:\n"
        "- Researcher: analysis, information gathering, concept explanation\n"
        "- Coder: writing code, technical implementation, debugging\n"
        "- Reviewer: quality assurance, critique, improvement suggestions\n"
        "- Writer: synthesis, documentation, combining outputs\n\n"
        "Break the user's task into appropriate subtasks and delegate them to the "
        "right specialists using the available tools. Use multiple agents when the "
        "task benefits from different expertise. After all delegations, synthesize "
        "the results into a comprehensive final answer."
    )

    def __init__(self, api_key: str | None = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.specialists: dict[str, SpecialistAgent] = {
            "researcher": ResearcherAgent(self.client),
            "coder": CoderAgent(self.client),
            "reviewer": ReviewerAgent(self.client),
            "writer": WriterAgent(self.client),
        }

    def _build_context(self, results: list[AgentResult]) -> str:
        if not results:
            return ""
        parts = []
        for r in results:
            parts.append(f"### {r.agent_name} output:\n{r.output}")
        return "\n\n".join(parts)

    def _dispatch_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        accumulated_results: list[AgentResult],
    ) -> AgentResult:
        agent_key = tool_name.replace("delegate_to_", "")
        agent = self.specialists[agent_key]

        context = ""
        if tool_input.get("include_context", True) and accumulated_results:
            context = self._build_context(accumulated_results)

        print(f"  → Delegating to {agent.name}: {tool_input['task'][:80]}...")
        result = agent.run(tool_input["task"], context)
        print(f"    ✓ {agent.name} complete ({len(result.output)} chars)")
        return result

    def run(self, task: str, verbose: bool = True) -> TeamResult:
        """
        Run the agent team on a task, returning a TeamResult with all outputs.
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"Task: {task}")
            print(f"{'='*60}")

        team_result = TeamResult(original_task=task)
        messages: list[dict[str, Any]] = [{"role": "user", "content": task}]

        while True:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                thinking={"type": "adaptive"},
                system=self.ORCHESTRATOR_SYSTEM,
                tools=self.TOOLS,
                messages=messages,
            )

            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            text_blocks = [b for b in response.content if b.type == "text"]

            # Append the assistant's full response to history
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                # Final answer from orchestrator
                team_result.final_answer = next(
                    (b.text for b in text_blocks), ""
                )
                break

            if response.stop_reason != "tool_use":
                # Unexpected stop — surface whatever text we got
                team_result.final_answer = next(
                    (b.text for b in text_blocks), "No output produced."
                )
                break

            # Execute all tool calls and collect results
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

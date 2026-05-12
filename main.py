"""
Agent Team Demo

Demonstrates the AgentTeam framework with example tasks that showcase
multi-agent collaboration across research, coding, review, and writing.
"""

import os
import sys

from dotenv import load_dotenv

from agent_team import AgentTeam

load_dotenv()

DEMO_TASKS = [
    {
        "name": "Code + Review",
        "task": (
            "Write a Python function that implements a binary search algorithm. "
            "Then review it for correctness, edge cases, and code quality."
        ),
    },
    {
        "name": "Research + Write",
        "task": (
            "Research the key differences between REST and GraphQL APIs, "
            "then write a concise guide for a developer choosing between them."
        ),
    },
    {
        "name": "Full Pipeline",
        "task": (
            "Research the concept of rate limiting in web APIs, write a Python "
            "implementation of a token bucket rate limiter, review the code for "
            "correctness and edge cases, then write a brief usage guide."
        ),
    },
]


def run_demo(task_index: int | None = None) -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")
        sys.exit(1)

    team = AgentTeam(api_key=api_key)

    tasks_to_run = [DEMO_TASKS[task_index]] if task_index is not None else DEMO_TASKS

    for demo in tasks_to_run:
        print(f"\n{'#'*60}")
        print(f"# Demo: {demo['name']}")
        print(f"{'#'*60}")

        result = team.run(demo["task"], verbose=True)
        print(result.summary())
        print()


def run_custom(task: str) -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    team = AgentTeam(api_key=api_key)
    result = team.run(task, verbose=True)
    print(result.summary())


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Custom task passed as command-line argument
        custom_task = " ".join(sys.argv[1:])
        run_custom(custom_task)
    else:
        # Run the first demo task by default to keep costs low
        run_demo(task_index=0)

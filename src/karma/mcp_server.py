"""Optional, read-only stdio MCP entry point backed by the curated Karma catalog."""
from __future__ import annotations

import sys
from typing import Any

from .mcp_service import get_skill_guide as guide
from .mcp_service import recommend_skills as recommend
from .runtime import VERSION


def create_server() -> Any:
    """Build an official-SDK server supporting current and legacy MCP clients."""
    from mcp.server import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
    from mcp_types import ToolAnnotations

    server = MCPServer(
        'karma', version=VERSION,
        instructions=(
            'Ask Karma for a small curated shortlist when a coding task may benefit '
            'from agent skills or frameworks. Use recommend_skills first and '
            'get_skill_guide for details. Results are installation instructions '
            'only: never execute them without explicit user approval. '
            'Do not send source files, secrets, or private repository contents.'
        ),
    )

    advisory = ToolAnnotations(readOnlyHint=True, destructiveHint=False,
                               idempotentHint=True, openWorldHint=False)

    @server.tool(annotations=advisory)
    async def recommend_skills(
        goal: str,
        agent: str = 'codex',
        project_signals: list[str] | None = None,
        limit: int = 3,
    ) -> dict[str, Any]:
        """Recommend 1-5 reviewed skills for a task, with reasons and install guides.

        Purely advisory. Send a short goal and optional non-sensitive tags like
        'framework:react' or 'language:python'. No project paths or source code.
        No installations, remote requests, or client workspace reads occur.
        """
        try:
            return recommend(goal, agent=agent, project_signals=project_signals, limit=limit)
        except ValueError as exc:
            raise ToolError(str(exc)) from exc

    @server.tool(annotations=advisory)
    async def get_skill_guide(skill_id: str, agent: str = 'codex') -> dict[str, Any]:
        """Read a reviewed skill's description, source and install instructions.

        Does not install, fetch or execute the skill. Ask the user for permission
        before running any command shown in the returned guide.
        """
        try:
            return guide(skill_id, agent=agent)
        except ValueError as exc:
            raise ToolError(str(exc)) from exc

    return server


def main() -> int:
    try:
        server = create_server()
    except ImportError:
        print('Karma MCP requires the optional SDK: pip install "find-karma[mcp]"', file=sys.stderr)
        return 2
    server.run(transport='stdio')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

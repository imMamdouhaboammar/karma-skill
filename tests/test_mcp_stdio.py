"""Real stdio transport smoke test; opt in using KARMA_TEST_STDIO=1.

Run with the official SDK installed: pip install '.[mcp]'.
"""

import asyncio
from contextlib import asynccontextmanager
import importlib.util
import os
from pathlib import Path
import sys
import unittest


@asynccontextmanager
async def async_timeout(seconds: float):
    if sys.version_info >= (3, 11):
        async with asyncio.timeout(seconds):
            yield
    else:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + seconds
        task = asyncio.current_task()
        handle = loop.call_at(deadline, task.cancel)
        try:
            yield
        except asyncio.CancelledError:
            raise TimeoutError() from None
        finally:
            handle.cancel()


@unittest.skipUnless(
    os.environ.get('KARMA_TEST_STDIO') == '1' and importlib.util.find_spec('mcp'),
    'Requires KARMA_TEST_STDIO=1 and the optional MCP SDK',
)
class MCPStdioTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_client_discovers_and_calls_advice_only_tools(self):
        from mcp import Client, StdioServerParameters

        project = Path(__file__).resolve().parents[1]
        env = {**os.environ, 'PYTHONPATH': str(project / 'src')}
        server = StdioServerParameters(
            command=sys.executable, args=['-m', 'karma.mcp_server'], env=env,
        )

        async with async_timeout(15):
            async with Client(server, read_timeout_seconds=8) as client:
                listed = await client.list_tools()
                self.assertEqual(
                    {tool.name for tool in listed.tools},
                    {'recommend_skills', 'get_skill_guide'},
                )
                self.assertTrue(all(tool.annotations.read_only_hint for tool in listed.tools))
                result = await client.call_tool('recommend_skills', {
                    'goal': 'frontend React UI', 'project_signals': ['framework:react'],
                })
                self.assertFalse(result.is_error)
                self.assertTrue(result.structured_content['recommendations'])
                self.assertFalse(result.structured_content['installed'])


if __name__ == '__main__':
    unittest.main()

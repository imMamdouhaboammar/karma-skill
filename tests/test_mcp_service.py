"""Contract tests for Karma's read-only MCP recommendation surface."""

import asyncio
from contextlib import asynccontextmanager
import importlib.util
import sys
import unittest
from unittest.mock import patch

from karma import mcp_service


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


class MCPRecommendationTests(unittest.TestCase):
    def test_recommend_only_reviewed_relevant_skills_with_commands(self):
        with patch('subprocess.run') as install, patch('urllib.request.urlopen') as network:
            result = mcp_service.recommend_skills(
                'React frontend UI quality', agent='codex',
                project_signals=['framework:react', 'language:typescript'], limit=3,
            )
        self.assertGreater(len(result['recommendations']), 0)
        self.assertLessEqual(len(result['recommendations']), 3)
        self.assertEqual(result['recommendations'][0]['lane'], 'frontend-quality')
        self.assertGreater(result['catalog_reviewed_count'], 0)
        for item in result['recommendations']:
            self.assertEqual(item['status'], 'reviewed')
            self.assertTrue(item['why'])
            # Ensure caller-supplied project signals are labeled as caller tags, not workspace scans
            self.assertFalse(any(r.startswith('Repository:') for r in item['why']))
            self.assertTrue(any(r.startswith('Caller stack signals:') for r in item['why']))
            self.assertTrue(item['installation_guide'])
            self.assertTrue(item['source'].startswith('https://github.com/'))
        self.assertFalse(result['installed'])
        install.assert_not_called()
        network.assert_not_called()

    def test_recommend_never_reads_client_project(self):
        with patch('karma.runtime.detect_project', side_effect=AssertionError('project scan attempted')):
            result = mcp_service.recommend_skills('testing TDD', agent='codex')
        self.assertTrue(result['recommendations'])

    def test_goal_matching_catalog_tags_returns_recommendations(self):
        result = mcp_service.recommend_skills('portfolio interview design', agent='codex', limit=3)
        self.assertTrue(result['recommendations'])
        self.assertIn('portfolio', result['recommendations'][0]['id'])

    def test_get_guide_is_curated_only_and_never_installs(self):
        guide = mcp_service.get_skill_guide('matt-tdd', agent='codex')
        self.assertEqual(guide['id'], 'matt-tdd')
        self.assertIn('--skill tdd', guide['installation_guide'])
        self.assertFalse(guide['installed'])
        self.assertIn('approval', guide['next_step'].lower())
        with self.assertRaisesRegex(ValueError, 'reviewed'):
            mcp_service.get_skill_guide('not-in-curated-list', agent='codex')

    def test_rejects_bad_inputs_without_falling_back_to_mass_marketplace(self):
        cases = [
            {'goal': ' '},
            {'goal': 'testing', 'limit': 0},
            {'goal': 'testing', 'limit': 99},
            {'goal': 'testing', 'agent': 'unknown'},
            {'goal': 'testing', 'project_signals': ['../secret']},
            {'goal': 'testing', 'project_signals': ['task:testing'] * 31},
        ]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                mcp_service.recommend_skills(**kwargs)

    def test_unrecognized_goal_does_not_use_stack_tags_as_a_guess(self):
        result = mcp_service.recommend_skills(
            'flibberty quantum nonsense', project_signals=['framework:react'],
        )
        self.assertEqual(result['recommendations'], [])
        self.assertIn('Clarify', result['no_match_guidance'])

    def test_guide_rejects_host_incompatible_and_candidate_skills(self):
        with self.assertRaisesRegex(ValueError, 'not available'):
            mcp_service.get_skill_guide('claude-plugin-review', agent='codex')
        with self.assertRaises(ValueError):
            mcp_service.get_skill_guide('matt-tdd', agent='evil-agent')
        # Explicitly verify candidate skills are rejected
        with self.assertRaisesRegex(ValueError, 'reviewed'):
            mcp_service.get_skill_guide('security-audit', agent='codex')


@unittest.skipUnless(importlib.util.find_spec('mcp'), 'Install optional MCP SDK to run protocol integration tests')
class MCPProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_sdk_exposes_two_read_only_tools(self):
        from mcp import Client
        from karma.mcp_server import create_server

        async with async_timeout(8):
            async with Client(create_server()) as client:
                exposed = await client.list_tools()
                self.assertEqual({tool.name for tool in exposed.tools}, {'recommend_skills', 'get_skill_guide'})
                response = await client.call_tool('recommend_skills', {
                    'goal': 'React UI polish', 'agent': 'codex', 'project_signals': ['framework:react']
                })
                self.assertFalse(response.is_error)
                self.assertTrue(response.structured_content['recommendations'])
                guide = await client.call_tool('get_skill_guide', {'skill_id': 'matt-tdd'})
                self.assertFalse(guide.is_error)
                self.assertIn('npx', guide.structured_content['installation_guide'])

    async def test_invalid_id_returns_tool_error(self):
        from mcp import Client
        from karma.mcp_server import create_server

        async with async_timeout(8):
            async with Client(create_server()) as client:
                response = await client.call_tool('get_skill_guide', {'skill_id': 'unreviewed-id'})
                self.assertTrue(response.is_error)

    async def test_legacy_handshake_client_can_read_the_same_guide(self):
        from mcp import Client
        from karma.mcp_server import create_server

        async with async_timeout(8):
            async with Client(create_server(), mode='legacy') as client:
                self.assertTrue(client.protocol_version.startswith('2025-'))
                result = await client.call_tool('get_skill_guide', {'skill_id': 'matt-tdd'})
                self.assertFalse(result.is_error)
                self.assertFalse(result.structured_content['installed'])


if __name__ == '__main__':
    unittest.main()

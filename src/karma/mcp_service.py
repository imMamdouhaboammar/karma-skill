"""Pure, read-only contracts exposed by the optional MCP server.

MCP clients send only a task description and optional non-sensitive stack tags.
This module never inspects a project, contacts GitHub, or installs a skill.
"""
from __future__ import annotations

from typing import Any

from . import runtime

NEXT_STEP = (
    'Review the source and installation guide, then request explicit user approval '
    'before running any command. Karma only advises; it never installs.'
)


def _catalog() -> list[dict[str, Any]]:
    entries = runtime.load_catalog()
    issues = runtime.validate_catalog(entries)
    if issues:
        raise ValueError('Invalid curated catalog: ' + ', '.join(issues[:3]))
    return entries


def _agent(agent: str) -> None:
    if agent not in runtime.AGENTS:
        raise ValueError('Unsupported agent host; choose one of: ' + ', '.join(runtime.AGENTS))


def recommend_skills(goal: str, agent: str = 'codex',
                     project_signals: list[str] | None = None,
                     limit: int = 3) -> dict[str, Any]:
    """Return up to five explainable recommendations from reviewed records only."""
    _agent(agent)
    if not isinstance(goal, str) or not goal.strip() or len(goal) > 1000:
        raise ValueError('goal must be a non-empty task description (at most 1000 characters)')
    if type(limit) is not int or not 1 <= limit <= 5:
        raise ValueError('limit must be an integer from 1 to 5')
    if project_signals is None:
        project_signals = []
    if not isinstance(project_signals, list) or len(project_signals) > 30:
        raise ValueError('project_signals must be a list of up to 30 known stack tags')

    entries = _catalog()
    allowed = {signal for item in entries for signal in
               (*item.get('signals', []), *(item.get('require_any') or []))}
    if any(not isinstance(signal, str) or signal not in allowed for signal in project_signals):
        raise ValueError('Unknown project signal; use tags from the curated catalog')

    # Stack compatibility alone is not evidence that a skill solves the task:
    # Run the deterministic matcher and ensure matches align with the goal itself (signals or keywords).
    raw_matched = runtime.find(entries, set(project_signals), goal=goal, agent=agent, limit=limit)
    matched = [
        item for item in raw_matched
        if not goal.strip() or any(r.startswith(('Goal:', 'Keywords:')) for r in item.get('why', []))
    ]
    shortlist = [{
        'id': item['id'], 'name': item['name'], 'kind': item['kind'],
        'lane': item['lane'], 'status': item['status'], 'benefit': item['benefit'],
        'why': [r.replace('Repository:', 'Caller stack signals:') for r in item.get('why', [])],
        'source': item['source'],
        'reviewed_revision': item['reviewed_revision'],
        'reviewed_path': item['reviewed_path'],
        'reviewed_at': item['reviewed_at'],
        'drift_status': 'not_checked_offline',
        'installation_guide': item['install'],
    } for item in matched]
    return {
        'recommendations': shortlist,
        'catalog_reviewed_count': sum(item['status'] == 'reviewed' for item in entries),
        'installed': False,
        'next_step': NEXT_STEP,
        'no_match_guidance': (
            'No reviewed skill met the task signals. Clarify the goal; do not invent '
            'a recommendation or fall back to an unreviewed marketplace.'
            if not shortlist else None
        ),
    }


def get_skill_guide(skill_id: str, agent: str = 'codex') -> dict[str, Any]:
    """Explain a reviewed skill's scope and installation, without executing it."""
    _agent(agent)
    if not isinstance(skill_id, str) or not runtime.SKILL_RE.fullmatch(skill_id):
        raise ValueError('Provide a valid reviewed skill id')
    entry = next((item for item in _catalog() if item['id'] == skill_id), None)
    if entry is None or entry['status'] != 'reviewed':
        raise ValueError('Skill is not in the reviewed curated catalog')
    if entry.get('hosts') and agent not in entry['hosts']:
        raise ValueError(f'Skill is not available for agent host {agent}')
    return {
        'id': entry['id'], 'name': entry['name'], 'kind': entry['kind'],
        'summary': entry['summary'], 'benefit': entry['benefit'],
        'source': entry['source'], 'review_evidence': entry['evidence'],
        'reviewed_revision': entry['reviewed_revision'],
        'reviewed_path': entry['reviewed_path'],
        'reviewed_at': entry['reviewed_at'],
        'drift_status': 'not_checked_offline',
        'review_note': entry.get('review_note', ''),
        'installation_guide': runtime.install_instructions(entry, agent),
        'installed': False, 'next_step': NEXT_STEP,
    }

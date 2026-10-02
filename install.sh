#!/usr/bin/env bash
# Universal Multi-Agent Installer for KARMA ☯
# Supports: Claude Code, Cursor, Codex, OpenCode, Antigravity, Gemini CLI, Windsurf, Universal Agent Kernel
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SOURCE="${SCRIPT_DIR}/skills/find-karma"
TARGET_NAME="find-karma"

PROJECT_DIR=""
SPECIFIC_AGENT=""
DRY_RUN=false
FORCE=false

print_usage() {
  cat <<EOF
Usage: ./install.sh [options]

Options:
  --project <dir>    Install into a specific project workspace instead of global agent directories
  --agent <name>     Install only for a specific agent (claude-code, cursor, codex, gemini, antigravity, windsurf, opencode)
  --dry-run          Print actions without copying any files
  --force            Overwrite existing target directories without confirmation
  --help, -h         Show this message
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      PROJECT_DIR="$2"
      shift 2
      ;;
    --agent)
      SPECIFIC_AGENT="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --force)
      FORCE=true
      shift
      ;;
    --help|-h)
      print_usage
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

if [[ ! -d "${SKILL_SOURCE}" ]]; then
  echo "Error: Skill source directory not found at ${SKILL_SOURCE}" >&2
  exit 1
fi

copy_skill() {
  local target_path="$1"
  local agent_name="$2"

  if [ "${DRY_RUN}" = true ]; then
    echo "  [dry-run] Would install for ${agent_name} -> ${target_path}"
    return 0
  fi

  if [ -e "${target_path}" ] && [ "${FORCE}" != true ]; then
    echo "  ⚠️  Already exists: ${target_path} (use --force to overwrite)"
    return 0
  fi

  mkdir -p "$(dirname "${target_path}")"
  rm -rf "${target_path}"
  cp -R "${SKILL_SOURCE}" "${target_path}"
  echo "  ✅ Installed for ${agent_name} -> ${target_path}"
}

echo "☯ KARMA Multi-Agent Skill Installer"
echo "==================================="

if [ -n "${PROJECT_DIR}" ]; then
  BASE_DIR="$(cd "${PROJECT_DIR}" && pwd)"
  echo "Target project: ${BASE_DIR}"

  if [ -z "${SPECIFIC_AGENT}" ] || [ "${SPECIFIC_AGENT}" = "codex" ]; then
    copy_skill "${BASE_DIR}/.agents/skills/${TARGET_NAME}" "Codex"
  fi
  if [ -z "${SPECIFIC_AGENT}" ] || [ "${SPECIFIC_AGENT}" = "claude-code" ]; then
    copy_skill "${BASE_DIR}/.claude/skills/${TARGET_NAME}" "Claude Code"
  fi
  if [ -z "${SPECIFIC_AGENT}" ] || [ "${SPECIFIC_AGENT}" = "cursor" ]; then
    copy_skill "${BASE_DIR}/.cursor/skills/${TARGET_NAME}" "Cursor"
  fi
  if [ -z "${SPECIFIC_AGENT}" ] || [ "${SPECIFIC_AGENT}" = "gemini" ]; then
    copy_skill "${BASE_DIR}/.gemini/skills/${TARGET_NAME}" "Gemini CLI"
  fi
  if [ -z "${SPECIFIC_AGENT}" ] || [ "${SPECIFIC_AGENT}" = "antigravity" ]; then
    copy_skill "${BASE_DIR}/.agent/skills/${TARGET_NAME}" "Antigravity"
  fi
  if [ -z "${SPECIFIC_AGENT}" ] || [ "${SPECIFIC_AGENT}" = "windsurf" ]; then
    copy_skill "${BASE_DIR}/.windsurf/skills/${TARGET_NAME}" "Windsurf"
  fi
  if [ -z "${SPECIFIC_AGENT}" ] || [ "${SPECIFIC_AGENT}" = "opencode" ]; then
    copy_skill "${BASE_DIR}/.opencode/skills/${TARGET_NAME}" "OpenCode"
  fi
else
  echo "Mode: Global Agent Environments"

  # Claude Code
  if [ -z "${SPECIFIC_AGENT}" ] || [ "${SPECIFIC_AGENT}" = "claude-code" ]; then
    if [ -d "${HOME}/.claude" ] || [ -n "${SPECIFIC_AGENT}" ]; then
      copy_skill "${HOME}/.claude/skills/${TARGET_NAME}" "Claude Code"
    fi
  fi

  # Antigravity & Gemini CLI
  if [ -z "${SPECIFIC_AGENT}" ] || [ "${SPECIFIC_AGENT}" = "antigravity" ] || [ "${SPECIFIC_AGENT}" = "gemini" ]; then
    if [ -d "${HOME}/.gemini" ] || [ -n "${SPECIFIC_AGENT}" ]; then
      copy_skill "${HOME}/.gemini/config/skills/${TARGET_NAME}" "Antigravity / Gemini CLI"
    fi
  fi

  # Codex
  if [ -z "${SPECIFIC_AGENT}" ] || [ "${SPECIFIC_AGENT}" = "codex" ]; then
    if [ -d "${HOME}/.codex" ] || [ -n "${SPECIFIC_AGENT}" ]; then
      copy_skill "${HOME}/.codex/skills/${TARGET_NAME}" "Codex"
    fi
  fi

  # Windsurf
  if [ -z "${SPECIFIC_AGENT}" ] || [ "${SPECIFIC_AGENT}" = "windsurf" ]; then
    if [ -d "${HOME}/.windsurf" ] || [ -n "${SPECIFIC_AGENT}" ]; then
      copy_skill "${HOME}/.windsurf/skills/${TARGET_NAME}" "Windsurf"
    fi
  fi

  # Cursor
  if [ -z "${SPECIFIC_AGENT}" ] || [ "${SPECIFIC_AGENT}" = "cursor" ]; then
    if [ -d "${HOME}/.cursor" ] || [ -n "${SPECIFIC_AGENT}" ]; then
      copy_skill "${HOME}/.cursor/skills/${TARGET_NAME}" "Cursor"
    fi
  fi

  # Universal Agent Kernel (~/.agents/skills)
  if [ -z "${SPECIFIC_AGENT}" ]; then
    copy_skill "${HOME}/.agents/skills/${TARGET_NAME}" "Universal Agent Kernel"
  fi
fi

echo ""
echo "🎉 KARMA installation complete! In your coding session, ask:"
echo "   FIND KARMA ☯"

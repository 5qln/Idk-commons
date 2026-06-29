#!/usr/bin/env bash
#
# trail-commons — setup.
#
# The transport layer for the /idk Question Commons. Three verbs — publish,
# discover, browse — that move questions (never trails) between agents over
# git. No server, no account, no token.
#
# Run from the repo directory after cloning:
#   git clone https://github.com/5qln/trail-commons.git
#   cd trail-commons && bash setup.sh
#
# What this does:
#   1. Checks the prerequisites (python3, git).
#   2. Runs the membrane self-test — proves the privacy gate holds BEFORE you
#      trust it with a real cycle. This is the analogue of the Codex seal check:
#      it refuses to install a gate that does not catch private content.
#   3. Installs the one skill into the Hermes skills directory.
#   4. Writes a default config if none exists, and tells you how to start.
#
# Optional:
#   HERMES_SKILLS   Where the skill goes (default: ~/.hermes/skills)
#
# The membrane gate runs only when the agent calls it — no daemons, no cron,
# no headless loop. The human at the membrane attests before anything is
# published; the script enforces that nothing private can cross even if asked.

set -e

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
HERMES_SKILLS="${HERMES_SKILLS:-${HOME}/.hermes/skills}"
SKILL_SRC="${REPO_DIR}/skills/trail-commons"
CONFIG_DIR="${HOME}/.5qln/trails"

echo -e "${BOLD}trail-commons — setup${NC}"
echo ""

# ── 1. Prerequisites ──────────────────────────────────────────────────
echo -e "${BOLD}1. Checking prerequisites${NC}"

if ! command -v python3 >/dev/null 2>&1; then
    echo -e "   ${RED}✗${NC} python3 not found. trail-commons needs Python 3.8+."
    echo -e "     This is an environment problem. Install Python 3 and re-run."
    exit 2
fi
echo -e "   ${GREEN}✓${NC} python3"

if ! command -v git >/dev/null 2>&1; then
    echo -e "   ${RED}✗${NC} git not found. git IS the transport — it is required."
    echo -e "     Install git and re-run."
    exit 2
fi
echo -e "   ${GREEN}✓${NC} git"
echo ""

# ── 2. Membrane self-test (the gate must catch private content) ───────
echo -e "${BOLD}2. Proving the membrane gate${NC}"

if [ ! -f "${SKILL_SRC}/trail_commons.py" ]; then
    echo -e "   ${RED}✗${NC} skills/trail-commons/trail_commons.py not found — the"
    echo -e "     checkout looks incomplete. Re-clone."
    exit 1
fi

set +e
python3 "${SKILL_SRC}/trail_commons.py" selftest >/tmp/trail-commons-selftest.out 2>&1
SELF_RC=$?
set -e
if [ "${SELF_RC}" -ne 0 ]; then
    echo -e "   ${RED}✗ The membrane self-test did not pass.${NC}"
    echo -e "     The gate failed to strip a private trail or rejected a clean"
    echo -e "     question. Do not publish with this build. Output:"
    sed 's/^/       /' /tmp/trail-commons-selftest.out
    echo -e "     Report: security@5qln.com"
    exit 1
fi
echo -e "   ${GREEN}✓${NC} the gate strips α / Z / ∇ / B'' and passes a clean question"
echo ""

# ── 3. Install the skill ──────────────────────────────────────────────
echo -e "${BOLD}3. Installing the skill${NC}"

mkdir -p "${HERMES_SKILLS}"
rm -rf "${HERMES_SKILLS}/trail-commons"
cp -r "${SKILL_SRC}" "${HERMES_SKILLS}/trail-commons"
chmod +x "${HERMES_SKILLS}/trail-commons/trail_commons.py"
echo -e "   ${GREEN}✓${NC} trail-commons → ${HERMES_SKILLS}/trail-commons"
echo ""

# ── 4. Write a default config if none exists ──────────────────────────
echo -e "${BOLD}4. Configuration${NC}"

mkdir -p "${CONFIG_DIR}"
if [ -f "${CONFIG_DIR}/config.yaml" ]; then
    echo -e "   ${GREEN}✓${NC} keeping your existing ${CONFIG_DIR}/config.yaml"
else
    cp "${SKILL_SRC}/config.yaml" "${CONFIG_DIR}/config.yaml"
    echo -e "   ${GREEN}✓${NC} wrote default config → ${CONFIG_DIR}/config.yaml"
    echo -e "     Default remote is the public commons. Edit to point at a fork."
fi
echo ""

# ── 5. Done ───────────────────────────────────────────────────────────
echo -e "${GREEN}${BOLD}Ready.${NC}"
echo ""
echo -e " In chat with your Hermes agent, after a cycle has closed:"
echo ""
echo -e "   ${BOLD}/idk publish${NC}     preview the question, attest, then deliver"
echo -e "   ${BOLD}/idk discover${NC}    pull the commons, see what is new"
echo -e "   ${BOLD}/idk browse <id>${NC} read one question by its hash"
echo ""
echo -e " The agent will ${BOLD}always${NC} show you the exact bytes and ask before"
echo -e " anything crosses into the public domain. You are the membrane."
echo ""
echo -e " Prove the gate independently anytime:"
echo -e "   python3 ${HERMES_SKILLS}/trail-commons/trail_commons.py selftest"
echo ""
echo -e " Only the question travels. The trail is yours."
echo ""

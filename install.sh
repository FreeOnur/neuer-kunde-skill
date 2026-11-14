#!/usr/bin/env bash
# Links the skill into Claude Code, so `git pull` updates it in place.
#   ./install.sh              link into ~/.claude/skills/neuer-kunde
#   ./install.sh --uninstall  remove that link
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZIEL="$HOME/.claude/skills/neuer-kunde"
if [[ "${1:-}" == "--uninstall" ]]; then
  [[ -L "$ZIEL" ]] && rm "$ZIEL" && echo "removed $ZIEL" || echo "nothing to remove"
  exit 0
fi
mkdir -p "$HOME/.claude/skills"
if [[ -e "$ZIEL" && ! -L "$ZIEL" ]]; then
  echo "$ZIEL exists and is not a link. Move it away first." >&2; exit 1
fi
ln -sfn "$REPO/skills/neuer-kunde" "$ZIEL"
echo "linked $ZIEL -> $REPO/skills/neuer-kunde"
echo "Start a new Claude Code session and type /neuer-kunde"

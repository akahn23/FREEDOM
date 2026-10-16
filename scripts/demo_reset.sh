#!/bin/sh
# Undo a demo rehearsal: removes what create_node.py / create_task_block.py generated for
# robot.<name> (default: agv) and restores the files they edited. Usage: scripts/demo_reset.sh [name]
set -e
cd "$(dirname "$0")/.."
name="${1:-agv}"
rm -rf "backend/src/robot/$name" "backend/src/job/task/robot/$name"
git checkout -- nodes.yaml frontend/messages/ja.json backend/src/robot/__init__.py backend/src/job/task/robot/__init__.py
echo "reset robot.$name (backend reloads automatically)"

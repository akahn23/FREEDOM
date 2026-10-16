#!/usr/bin/env python3
"""create-node: scaffold a new FREEDOM node under backend/src/<repository>/<name>/.

    python scripts/create_node.py robot agv --label "AGV"
    # then add one line to nodes.yaml (printed below), or pass --register to do it for you

Generates the Domain / NodeDomain / Node / Repository files following the existing
abstract.Node pattern (modelled on backend/src/robot/dummy), registers the package in
backend/src/<repository>/__init__.py and adds the dashboard label to frontend/messages/ja.json.
Stdlib only - runs on the host or inside the devcontainer.
"""

import argparse
import json
import re

from scaffold_common import BACKEND_SRC, ROOT, TEMPLATES, Plan, add_import, check_name, fail, render

TEMPLATE_FILES = ("__init__.py", "domain.py", "node.py", "repository.py")
MESSAGES = ROOT / "frontend" / "messages" / "ja.json"
NODES_YAML = ROOT / "nodes.yaml"
STATE_LABELS = {"0": "切断", "1": "待機", "2": "手動", "3": "動作中", "4": "警告", "5": "異常"}


def add_label(repository: str, name: str, label: str, plan: Plan) -> None:
    """Insert Node.<repository>.<name> into ja.json textually so the rest of the file is untouched."""
    text = MESSAGES.read_text(encoding="utf-8")
    messages = json.loads(text)
    if name in messages.get("Node", {}).get(repository, {}):
        return
    match = re.search(rf'^(\s*)"{re.escape(repository)}": \{{\n', text, re.M)
    if not match:
        fail(f'"Node.{repository}" not found in {MESSAGES.relative_to(ROOT)}')
    indent = match.group(1) + "  "
    entry = json.dumps({"name": label, "state": STATE_LABELS}, ensure_ascii=False, indent=2)
    entry = "\n".join(indent + line for line in entry.splitlines())
    block = f'{indent}"{name}": {entry.lstrip()},\n'
    plan.edit(MESSAGES, len(block.splitlines()))
    if not plan.dry_run:
        MESSAGES.write_text(text[: match.end()] + block + text[match.end():], encoding="utf-8")
    json.loads(MESSAGES.read_text(encoding="utf-8"))


def yaml_line(repository: str, name: str, instances: list[str]) -> str:
    return f"  {repository}.{name}: [{', '.join(instances)}]"


def register(line: str, key: str, plan: Plan) -> None:
    """Append the node line at the end of the `nodes:` block of nodes.yaml."""
    lines = NODES_YAML.read_text(encoding="utf-8").splitlines(keepends=True)
    if any(re.match(rf"\s*{re.escape(key)}\s*:", l) for l in lines):
        print(f"  nodes.yaml already registers {key}")
        return
    try:
        start = next(i for i, l in enumerate(lines) if re.match(r"nodes\s*:", l))
    except StopIteration:
        fail("nodes.yaml has no top-level `nodes:` key")
    end = start + 1
    for i in range(start + 1, len(lines)):
        if lines[i].strip() and not lines[i].startswith((" ", "\t", "#")):
            break
        if lines[i].strip() and not lines[i].lstrip().startswith("#"):
            end = i + 1
    if end and not lines[end - 1].endswith("\n"):
        lines[end - 1] += "\n"
    lines.insert(end, line + "\n")
    plan.edit(NODES_YAML, 1)
    if not plan.dry_run:
        NODES_YAML.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repository", choices=["robot"], help="node repository (backend/src/<repository>/)")
    parser.add_argument("name", help="node name, snake_case (e.g. agv)")
    parser.add_argument("--label", help="dashboard label (default: name)")
    parser.add_argument("--instances", help="comma-separated instance names (default: <name>_1,<name>_2)")
    parser.add_argument("--register", action="store_true", help="also append the line to nodes.yaml")
    parser.add_argument("--dry-run", action="store_true", help="print what would be generated")
    args = parser.parse_args()

    check_name(args.name, "node name")
    target = BACKEND_SRC / args.repository / args.name
    if target.exists():
        fail(f"{target.relative_to(ROOT)} already exists")
    label = args.label or args.name
    instances = [i.strip() for i in (args.instances or f"{args.name}_1,{args.name}_2").split(",") if i.strip()]
    for instance in instances:
        if not re.match(r"^[A-Za-z0-9_\-]+$", instance):
            fail(f"instance name '{instance}' may only contain letters, digits, '_' and '-'")

    plan = Plan(args.dry_run)
    print(f"create-node {args.repository}.{args.name}")
    for filename in TEMPLATE_FILES:
        text = render(TEMPLATES / "node" / args.repository / f"{filename}.tmpl", name=args.name, label=label)
        plan.create(target / filename, text)
    if add_import(BACKEND_SRC / args.repository / "__init__.py", args.name, args.dry_run):
        plan.edit(BACKEND_SRC / args.repository / "__init__.py", 1)
    add_label(args.repository, args.name, label, plan)

    line = yaml_line(args.repository, args.name, instances)
    if args.register:
        register(line, f"{args.repository}.{args.name}", plan)
    plan.summary()
    if not args.register:
        print("\nNext: add this one line under `nodes:` in nodes.yaml")
        print(line)
    print("\nThe backend reloads automatically (docker compose); refresh the dashboard to see "
          f"{label} under ロボット.")


if __name__ == "__main__":
    main()

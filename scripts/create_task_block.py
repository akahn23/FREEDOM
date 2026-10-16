#!/usr/bin/env python3
"""create-task-block: scaffold a new Blockly task block under backend/src/job/task/<node>/<name>/.

    python scripts/create_task_block.py robot.agv inspect --label "点検"

Generates domain.py (Domain with define_block() / define_toolbox(), modelled on
backend/src/job/task/common/control/controls_select/domain.py) plus the logic.py / __init__.py
the job runner needs, and registers the package in backend/src/job/task/<node>/__init__.py.
JobCreate.fetch_define() (backend/src/job/create/node.py) discovers it automatically, so the
block appears in the Job Creator toolbox under the <node> category - no frontend changes.

<node> must be a node registered in nodes.yaml (e.g. robot.agv, robot.dummy) or a common
category (e.g. common.control). Stdlib only.
"""

import argparse
import zlib

from scaffold_common import BACKEND_SRC, ROOT, TEMPLATES, Plan, add_import, check_name, fail, render

TASK_ROOT = BACKEND_SRC / "job" / "task"

ROBOT = {
    "robot_doc": "        robot (abstract.value.Domain): 対象ロボット\n",
    "robot_field": "    robot: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)\n",
    "robot_arg": (
        "                {\n"
        "                    \"type\": \"input_value\",\n"
        "                    \"name\": \"robot\",\n"
        "                    \"align\": \"RIGHT\",\n"
        "                    \"check\": \"Robot\"\n"
        "                },\n"
    ),
    "robot_shadow": (
        "                \"robot\": {\n"
        "                    \"shadow\": {\n"
        "                        \"type\": \"robot._get\"\n"
        "                    }\n"
        "                },\n"
    ),
    "robot_init": "        self._robot = await self.domain.robot.make_logic(self._job_id, self._logger)\n",
    "robot_exec": "        node: robot.Node = await self._robot.exec()\n",
    "target_log": " robot={node.domain.name}",
}
NO_ROBOT = {key: "" for key in ROBOT}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("node", help="toolbox category / node, dotted (e.g. robot.agv, common.control)")
    parser.add_argument("name", help="block name, snake_case (e.g. inspect)")
    parser.add_argument("--label", help="text shown on the block (default: name)")
    parser.add_argument("--tooltip", help="tooltip (default: '<label> を実行する')")
    parser.add_argument("--robot", action=argparse.BooleanOptionalAction, default=None,
                        help="add a robot input socket (default: on for robot.* nodes)")
    parser.add_argument("--dry-run", action="store_true", help="print what would be generated")
    args = parser.parse_args()

    parts = args.node.split(".")
    for part in parts:
        check_name(part, "node segment")
    check_name(args.name, "block name")
    node_dir = TASK_ROOT.joinpath(*parts)
    target = node_dir / args.name
    if target.exists():
        fail(f"{target.relative_to(ROOT)} already exists")
    if parts[0] != "common" and not (BACKEND_SRC.joinpath(*parts) / "__init__.py").exists():
        fail(f"node backend/src/{'/'.join(parts)}/ does not exist - run scripts/create_node.py first")

    label = args.label or args.name
    use_robot = parts[0] == "robot" if args.robot is None else args.robot
    values = dict(ROBOT if use_robot else NO_ROBOT)
    block_type = f"{args.node}.{args.name}"
    inputs = ["%1 %2"] + (["ロボット %3", "時間(秒) %4"] if use_robot else ["時間(秒) %3"])
    values |= {
        "label": label,
        "block_type": block_type,
        "tooltip": args.tooltip or f"{label} を実行する",
        "message": " ".join(inputs),
        "colour": str(zlib.crc32(block_type.encode()) % 360),
        "module": f"src.job.task.{block_type}",
    }

    plan = Plan(args.dry_run)
    print(f"create-task-block {block_type}")
    for filename in ("__init__.py", "domain.py", "logic.py"):
        text = render(TEMPLATES / "task_block" / f"{filename}.tmpl", **values)
        if filename == "logic.py" and use_robot:
            text = text.replace("from src.job import command\n", "from src import robot\nfrom src.job import command\n", 1)
        plan.create(target / filename, text)

    # make every package on the way importable and register the block with its parent
    for depth in range(len(parts), 0, -1):
        pkg = TASK_ROOT.joinpath(*parts[:depth])
        child = args.name if depth == len(parts) else parts[depth]
        if add_import(pkg / "__init__.py", child, args.dry_run):
            plan.edit(pkg / "__init__.py", 1)
    plan.summary()
    print(f"\nRefresh ジョブ作成 (Job Creator): the '{label}' block is in the toolbox category of node "
          f"'{args.node}' (shown with its dashboard label, e.g. AGV for robot.agv).")


if __name__ == "__main__":
    main()

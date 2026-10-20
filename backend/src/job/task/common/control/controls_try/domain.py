# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """Sequential exception-handling task
    Args:
        type (str): Task type
        id (str): Task ID
        name (str): Task name
            Text displayed as the task name in the UI
        next (Domain): Next task
        should_show (bool): Whether to display
            Whether to display while the job is running
        can_recover (bool): Whether the task can be resumed
            Whether the job can be resumed after it is stopped
        finished (bool): Finished flag
        command (list): Command contents
        init_task (abstract.statement.Domain): Task run at start
        try_task (abstract.statement.Domain): Task to execute
        except_task (abstract.statement.Domain): Task run on error
        finally_task (abstract.statement.Domain): Task run at the end
    """
    name:str = ""
    should_show:bool = False
    can_recover:bool = False
    init_task: abstract.statement.Domain = None
    try_task: abstract.statement.Domain = None
    except_task: abstract.statement.Domain = None
    finally_task: abstract.statement.Domain = None

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "controls_try",
            "message0": "開始時に実行 %1 タスク実行 %2 異常時に実行 %3 終了時に実行 %4",
            "args0": [
                {
                    "type": "input_statement",
                    "name": "init_task",
                    "align": "RIGHT"
                },
                {
                    "type": "input_statement",
                    "name": "try_task",
                    "align": "RIGHT"
                },
                {
                    "type": "input_statement",
                    "name": "except_task",
                    "align": "RIGHT"
                },
                {
                    "type": "input_statement",
                    "name": "finally_task",
                    "align": "RIGHT"
                }
            ],
            "previousStatement": None,
            "nextStatement": None,
            "colour": 180,
            "tooltip": "",
            "inputsInline": False,
        }]

    @classmethod
    def define_toolbox(cls) -> list[dict]:
        """Toolbox definition
        Define initial values for fields and output blocks
        https://developers.google.com/blockly/guides/configure/web/toolboxes/category?hl=ja
        Returns:
            list[dict]: Toolbox definitions
        """
        return [{
            "kind": "block",
            "type": "controls_try"
        }]

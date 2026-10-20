# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import typing

from src.repository import repository
from src.job.task import abstract
from src import job


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """controls_job_exec task
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
        job (str): Job name
        kwargs (abstract.value.Domain): Arguments
        var (dict[typing.Literal["id"], str]): Return-value variable name
    """
    can_recover: bool|str = "OK"
    name: str = "ジョブ実行"
    job: str = "none"
    kwargs: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    var: dict[typing.Literal["id"], str] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        """Post-instantiation processing"""
        super().__post_init__()
        self.can_recover = self.can_recover == "OK"

    @classmethod
    async def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        option = [[name, name] for name in await repository.retrieve(job.create.Node)[0].fetch_name_list(is_admin=True)]
        return [{
            "type": "job.active.exec",
            "tooltip": "任意のジョブを実行する",
            "helpUrl": "",
            "message0": "%1 %2 タスク表示 %3",
            "args0": [
                {
                    "type": "field_input",
                    "name": "name",
                    "text": cls.name
                },
                {"type": "input_dummy"},
                {
                    "type": "field_checkbox",
                    "name": "should_show",
                    "checked": cls.should_show
                },
            ],
            "message1": "%1 を実行する %2 ここから復帰 %3 %4 引数 (変数名：値) %5 戻り値を %6 にセット",
            "args1": [
                {
                    "type": "field_dropdown",
                    "name": "job",
                    "options": option if option else [["設定なし", "設定なし"]]
                },
                {"type": "input_dummy", "align": "RIGHT"},
                {
                    "type": "field_dropdown",
                    "name": "can_recover",
                    "options": [
                        ["できる", "OK"],
                        ["できない", "NG"]
                    ]
                },
                {"type": "input_dummy", "align": "RIGHT"},
                {
                    "type": "input_value",
                    "name": "kwargs",
                    "align": "RIGHT",
                    "check": "Dict"
                },
                {
                    "type": "field_variable",
                    "name": "var",
                    "variable": "result"
                }
            ],
            "previousStatement": None,
            "nextStatement": None,
            "colour": 360
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
            "type": "job.active.exec",
            "inputs": {
                "kwargs": {
                    "shadow": {
                        "type": "_dict_get",
                    }
                }
            }
        }]

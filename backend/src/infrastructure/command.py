# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses


@dataclasses.dataclass
class Button:
    """Button display
    Args:
        label (str): Button text
        func (str): Function to execute
        kwargs (str): Arguments
        type (str): Command type
    """
    label:str
    func:str
    kwargs:dict = dataclasses.field(default_factory=dict)
    type:str = "button"

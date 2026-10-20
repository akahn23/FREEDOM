# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src import abstract


@dataclasses.dataclass
class DefaultView:
    """Initial map view settings
    Args:
        center (list[float,float]]): Coordinates (latitude, longitude)
        zoom (int): Zoom level
        rotate (float): Rotation (deg)
    """
    center:list[float, float] = dataclasses.field(default_factory=lambda:[0.0, 0.0])
    zoom:int = 0
    rotate:float = 0.0


@dataclasses.dataclass
class Image:
    """Map image settings
    Args:
        name (str): Image name
        visible (bool): Shown/hidden
        corners (list[list[float,float,float,float]]): Corner coordinates (top-left, top-right, bottom-left, bottom-right)
    """
    name:str
    visible:bool
    corners:list[list[float,float,float,float]]


@dataclasses.dataclass
class Domain(abstract.Domain):
    """Map settings
    Args:
        default_view (list[float, float, float, float]): View settings
        image_list (list[Image]): Image settings
    """
    default_view:DefaultView = dataclasses.field(default_factory=DefaultView)
    image_list:list[Image] = dataclasses.field(default_factory=list)

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return {
            "default_view": {
                "type": "mapDefaultView",
                "label": "位置設定",
            },
            "image_list": {
                "type": "mapImage",
                "label": "画像設定",
            },
        }

    def __post_init__(self):
        """Post-initialization processing"""
        if type(self.default_view) is not DefaultView:
            self.default_view = DefaultView(**self.default_view)
        for i, image in enumerate(self.image_list):
            if type(image) is not Image:
                self.image_list[i] = Image(**image)

# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses


@dataclasses.dataclass
class Area:
    """Area settings
    Args:
        name (str): Name
        vertex_list (list[list[float]]): List of vertices
            Vertices must be ordered clockwise or counterclockwise
    """
    name:str
    vertex_list:list[list[float]]

def _is_inside(location:list[float,float], area_list:list[Area]) -> bool:
    """Inside-area check
    Inside-area check using the ray casting method
    Args:
        location (list[float,float]): Latitude, longitude
        area_list (list[util.map.Area]): List of areas
    Returns:
        bool: Whether inside the area
    """
    px, py = location
    inside = False
    for area in area_list:
        for i in range(len(area.vertex_list)):
            x1, y1 = area.vertex_list[i]
            x2, y2 = area.vertex_list[(i + 1) % len(area.vertex_list)]  # 次の頂点
            if (y1 > py) != (y2 > py) and px < ((x2 - x1) * (py - y1) / (y2 - y1) + x1):
                inside = not inside
        if inside:
            break
    return inside

# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import json
from datetime import date, datetime


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        """サポート外の型が指定されたときの挙動を定義する"""
        if dataclasses.is_dataclass(o):
            return o.__dict__
        elif hasattr(o, '__iter__'):
            return list(o)
        elif isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)


def dumps(obj, **kwargs):
    """自作JSONエンコーダ"""
    return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)

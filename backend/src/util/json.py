# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
from datetime import datetime, date
import json


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        """Defines the behavior when an unsupported type is given"""
        if dataclasses.is_dataclass(o):
            return o.__dict__
        elif hasattr(o, '__iter__'):
            return list(o)
        elif isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)


def dumps(obj, **kwargs):
    """Custom JSON encoder"""
    return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)

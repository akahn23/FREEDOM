# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

class LoopBreak(Exception):
    """Exception used to break out of a loop"""
    pass

class LoopContinue(Exception):
    """Exception used to continue to the next loop iteration"""
    pass

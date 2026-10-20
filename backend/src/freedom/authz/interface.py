# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc
from src.freedom.authz.domain import Domain


class Interface(abc.ABC):
    @abc.abstractmethod
    def __init__(self, domain: Domain):
        """AuthZ database connection interface
        Args:
            domain (Domain): Settings
        """
        raise NotImplementedError()

# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc

from src.abstract import Domain


class Node(abc.ABC):
    @abc.abstractmethod
    def __init__(self):
        """Abstract node
        Class that manages a domain and the processing of each node
        Methods implemented here can be executed via node requests from the UI
        """
        self.domain = Domain()

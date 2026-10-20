# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import collections
import typing


T = typing.TypeVar('T')


class Repository(collections.UserList[T]):
    """Node container class
    Subclass of list; nodes stored in self.data are contained
    """
    N = typing.TypeVar('N')

    def retrieve(self, cls:type[N], **kwargs) -> list[N]:
        """Search nodes
        Gets nodes of the given type or of subclasses inheriting from it
        If a Repository is stored, also searches the nodes under it
        Args:
            cls (type[N]): Node type
        Returns:
            list[N]: Search results
        """
        ret = list()
        for item in self.data:
            if isinstance(item, cls) and all(v==getattr(item.domain,k,None) for k,v in kwargs.items()):
                ret.append(item)
            elif isinstance(item, Repository):
                ret.extend(item.retrieve(cls, **kwargs))
        return ret


repository = Repository()

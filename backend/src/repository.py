# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import collections
import typing

T = typing.TypeVar('T')


class Repository(collections.UserList[T]):
    """ノード格納クラス
    list型継承クラス self.dataに格納したノードが入る
    """
    N = typing.TypeVar('N')

    def retrieve(self, cls:type[N], **kwargs) -> list[N]:
        """ノード探索
        指定した型と同じ、または型を継承したサブクラスを取得する
        Repositoryを格納している場合、その配下も探索する
        Args:
            cls (type[N]): ノード型
        Returns:
            list[N]: 探索結果
        """
        ret = list()
        for item in self.data:
            if isinstance(item, cls) and all(v==getattr(item.domain,k,None) for k,v in kwargs.items()):
                ret.append(item)
            elif isinstance(item, Repository):
                ret.extend(item.retrieve(cls, **kwargs))
        return ret


repository = Repository()

# src.job / src.abstract を直接importすると循環importになるため、先にsrc.freedomを読み込む
from src import freedom  # noqa: F401

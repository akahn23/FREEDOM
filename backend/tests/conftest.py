# Import order matters: importing src.job / src.abstract first triggers a
# circular import, so load the packages in the same order as config/dummy.py.
from src import freedom, job, infrastructure, robot, equipment  # noqa: F401

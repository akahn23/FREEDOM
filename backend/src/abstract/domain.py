# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc
import dataclasses


@dataclasses.dataclass
class Domain(abc.ABC):
    """Abstract domain
    Class that manages the variables saved to the settings database and returned for domain requests from the UI
    Only class variables are saved to the settings database
    Domain requests return both class variables and instance variables
    Do not declare types that util.json.dumps cannot convert to JSON
    """
    @classmethod
    @abc.abstractmethod
    def make_form(cls) -> dict:
        """Generate the form for the settings screen
        Returns the format of the settings form displayed on the UI's /config/[...node] page
        See frontend/components/config/form.tsx for the form format
        Returns:
            dict: Settings form
        """
        raise NotImplementedError("Subclasses must implement make_form method")

    def __post_init__(self):
        """Post-initialization processing
        Instance variables declared here are not saved to the settings database
        """
        pass

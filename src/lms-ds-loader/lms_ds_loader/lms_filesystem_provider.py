# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

import os
from dataclasses import dataclass, field


@dataclass
class LmsFilesystemProvider:
    """
    Navigates a standard filesystem layout to find CSV files for loading into an
    Ed-Fi LMS-DS compatible database. Expected filesystem layout:

    base_path/
      section=<identifier>/
        activities/
            <files>
        assignment=<identifer>/
          submissions/
            <files>
        assignments/
          <files>
        attendance/
          <files>
        grades/
          <files>
        section-associations/
          <files>
      sections/
        <files>
      users/
        <files>

    Parameters
    ----------
    base_path : str
        Base path on the filesystem containing the LMS csv files to load.
    """

    base_path: str
    Users: list = field(default_factory=list)

    def get_all_files(self):
        """
        Traverses the base path to find all relevant CSV files.

        Returns
        -------
        LmsFilesystemProvider
            The current object.
        """

        if not os.path.exists(self.base_path):
            raise OSError(f"Path {self.base_path} does not exist.")

        def _get_user_files():
            user_path = os.path.join(self.base_path, "Users")

            if os.path.exists(user_path):
                self.Users = [
                    f.path for f in os.scandir(user_path) if f.name.endswith(".csv")
                ]

        # Other "local" functions can be added for other file types

        _get_user_files()

        return self

# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

from datetime import datetime
import os

USERS = "users"
SECTION = "section"
ASSIGNMENTS = "assignments"


def _get_file_name() -> str:
    return datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".csv"


def _create_directory_if_it_does_not_exist(dir: str):
    if not os.path.exists(dir):
        os.mkdir(dir)


def get_assignment_file_path(output_directory: str, section_id: int) -> str:
    base_dir = os.path.join(output_directory, f"{SECTION}={section_id}")
    _create_directory_if_it_does_not_exist(base_dir)
    base_dir = os.path.join(base_dir, ASSIGNMENTS)
    _create_directory_if_it_does_not_exist(base_dir)

    return os.path.join(base_dir, _get_file_name())


def get_user_file_path(output_directory: str) -> str:
    base_dir = os.path.join(output_directory, USERS)
    _create_directory_if_it_does_not_exist(base_dir)

    return os.path.join(base_dir, _get_file_name())
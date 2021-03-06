# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

from datetime import datetime
import pytest
import xxhash
from pandas import read_sql_query, DataFrame
from google_classroom_extractor.api.students import _sync_without_cleanup

COLUMNS = [
    "courseId",
    "userId",
    "profile.id",
    "profile.name.givenName",
    "profile.name.familyName",
    "profile.name.fullName",
    "profile.emailAddress",
    "profile.permissions",
    "profile.photoUrl",
    "profile.verifiedTeacher",
]

CHANGED_STUDENT_BEFORE = [
    "1",
    "11",
    "111",
    "givenName1",
    "familyName1",
    "fullName1",
    "1@gmail.com",
    "1111",
    "http://111",
    "False",
]

CHANGED_STUDENT_AFTER = [
    "1",
    "11",
    "111",
    "*CHANGED*",
    "familyName1",
    "fullName1",
    "1@gmail.com",
    "1111",
    "http://111",
    "False",
]

UNCHANGED_STUDENT = [
    "2",
    "22",
    "222",
    "givenName2",
    "familyName2",
    "fullName2",
    "2@gmail.com",
    "2222",
    "http://222",
    "False",
]

OMITTED_FROM_SYNC_STUDENT = [
    "3",
    "33",
    "333",
    "givenName3",
    "familyName3",
    "fullName3",
    "3@gmail.com",
    "3333",
    "http://333",
    "False",
]

NEW_STUDENT = [
    "4",
    "44",
    "444",
    "givenName4",
    "familyName4",
    "fullName4",
    "4@gmail.com",
    "4444",
    "http://444",
    "False",
]

SYNC_DATA = [CHANGED_STUDENT_AFTER, UNCHANGED_STUDENT, NEW_STUDENT]


def describe_when_testing_sync_with_new_and_missing_and_updated_rows():
    @pytest.fixture
    def test_db_after_sync(test_db_fixture):
        # arrange
        INITIAL_STUDENT_DATA = [
            CHANGED_STUDENT_BEFORE,
            UNCHANGED_STUDENT,
            OMITTED_FROM_SYNC_STUDENT,
        ]

        students_initial_df = DataFrame(INITIAL_STUDENT_DATA, columns=COLUMNS)
        students_initial_df["Hash"] = students_initial_df.apply(
            lambda row: xxhash.xxh64_hexdigest(row.to_json().encode("utf-8")),
            axis=1,
        )
        dateToUse = datetime(2020, 9, 14, 12, 0, 0)
        students_initial_df["SyncNeeded"] = 0
        students_initial_df["CreateDate"] = dateToUse
        students_initial_df["LastModifiedDate"] = dateToUse

        students_sync_df = DataFrame(SYNC_DATA, columns=COLUMNS)

        with test_db_fixture.connect() as con:
            con.execute("DROP TABLE IF EXISTS Students")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS Students (
                    courseId TEXT,
                    userId TEXT,
                    "profile.id" TEXT,
                    "profile.name.givenName" TEXT,
                    "profile.name.familyName" TEXT,
                    "profile.name.fullName" TEXT,
                    "profile.emailAddress" TEXT,
                    "profile.permissions" TEXT,
                    "profile.photoUrl" TEXT,
                    "profile.verifiedTeacher" TEXT,
                    Hash TEXT,
                    CreateDate DATETIME,
                    LastModifiedDate DATETIME,
                    SyncNeeded BIGINT,
                    PRIMARY KEY (courseId,userId)
                )
                """
            )

        students_initial_df.to_sql(
            "Students", test_db_fixture, if_exists="append", index=False, chunksize=1000
        )

        # act
        _sync_without_cleanup(students_sync_df, test_db_fixture)

        return test_db_fixture

    def it_should_have_students_table_with_updated_row_and_added_new_row(
        test_db_after_sync,
    ):
        EXPECTED_STUDENT_DATA_AFTER_SYNC = [
            UNCHANGED_STUDENT,
            OMITTED_FROM_SYNC_STUDENT,
            CHANGED_STUDENT_AFTER,
            NEW_STUDENT,
        ]
        with test_db_after_sync.connect() as con:
            expected_students_df = (
                DataFrame(EXPECTED_STUDENT_DATA_AFTER_SYNC, columns=COLUMNS)
                .set_index(["courseId", "userId"])  # ignore generated dataframe index
                .astype("string")
            )
            students_from_db_df = (
                read_sql_query("SELECT * from Students", con)
                .loc[:, "courseId":"profile.verifiedTeacher"]  # original columns only
                .set_index(["courseId", "userId"])  # ignore generated dataframe index
                .astype("string")
            )
            assert expected_students_df.to_csv() == students_from_db_df.to_csv()

    def it_should_have_temporary_sync_table_unchanged(test_db_after_sync):
        EXPECTED_SYNC_DATA_AFTER_SYNC = SYNC_DATA
        with test_db_after_sync.connect() as con:
            expected_sync_students_df = DataFrame(
                EXPECTED_SYNC_DATA_AFTER_SYNC, columns=COLUMNS
            ).astype("string")
            sync_students_from_db_df = (
                read_sql_query("SELECT * from Sync_Students", con)
                .loc[:, "courseId":"profile.verifiedTeacher"]  # original columns only
                .astype("string")
            )
            assert expected_sync_students_df.to_csv() == sync_students_from_db_df.to_csv()

    def it_should_have_temporary_unmatched_table_with_correct_intermediate_rows(
        test_db_after_sync,
    ):
        EXPECTED_UNMATCHED_DATA_AFTER_SYNC = [
            CHANGED_STUDENT_AFTER,
            CHANGED_STUDENT_BEFORE,
            OMITTED_FROM_SYNC_STUDENT,
            NEW_STUDENT,
        ]
        with test_db_after_sync.connect() as con:
            expected_unmatched_df = DataFrame(
                EXPECTED_UNMATCHED_DATA_AFTER_SYNC, columns=COLUMNS
            ).astype("string")
            unmatched_from_db_df = (
                read_sql_query("SELECT * from Unmatched_Students", con)
                .loc[:, "courseId":"profile.verifiedTeacher"]  # original columns only
                .astype("string")
            )
            assert expected_unmatched_df.to_csv() == unmatched_from_db_df.to_csv()

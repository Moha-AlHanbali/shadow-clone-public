"""This module extracts a single student cheating case out of pre-existing ones"""

import os
from datetime import datetime
import pandas as pd


class Extract:
    """
    Extract class searches for a student in a specific cohort reports and collects all of their previous cheating cases in one csv file.

    ...

    Attributes
    ----------

    cohort : str
        name of the cohort

    paths : list
        list of paths containing the target student cohort reports

    Methods
    -------

    search(cohort):
            Searches for the directories containing reports for the target student cohort.

    extract(student):
            Extracts the target student data from the cohort reports.
    """

    def __init__(self, paths=list()) -> None:
        """
        Parameters
        ----------

        paths : list
            list of paths containing the target student cohort reports
        """
        self.paths = paths

    def search(self, cohort: str) -> None:
        """
        Searches for the directories containing reports for the target student cohort.

        Parameters
        ----------

        cohort : str
            name of the cohort

        Returns
        -------

        None
        """
        self.cohort = cohort

        for root, dirs, files in os.walk("./reports"):
            for file in files:
                if self.cohort in root and not ".xlsx" in file:
                    self.paths.append(root + "/" + file)

    def extract(self, student: str) -> None:
        """
        Extracts the target student data from the cohort reports.

        Parameters
        ----------

        student : str
            name of the target student

        Returns
        -------

        None
        """
        cohort_df = pd.DataFrame(
            columns=[
                "Similarity Score",
                "First Student",
                "First Branch",
                "First File Name",
                "First URL",
                "Second Student",
                "Second Branch",
                "Second File Name",
                "Second URL",
            ]
        )

        for path in self.paths:
            assignment_df = pd.read_csv(path)
            cohort_df = pd.concat([assignment_df])

        time_stamp = datetime.fromtimestamp(
            datetime.timestamp(datetime.now())
        ).strftime("%d-%B-%Y")
        cohort_df = cohort_df[
            cohort_df["First Student"].str.contains(f"{student}")
            | cohort_df["Second Student"].str.contains(f"{student}")
        ].reset_index(drop=True)
        os.makedirs(
            os.path.dirname(f"./extractions/{self.cohort}/{time_stamp}/"), exist_ok=True
        )
        cohort_df.to_csv(f"./extractions/{self.cohort}/{time_stamp}/{student}.csv")

"""This module generates a report using acquired data from clone detection"""

import os, csv
from datetime import datetime
from typing import Dict, List, Any

import pandas


class Report:
    """
    Report class generates a CSV report of each detection run.

    ...

    Attributes
    ----------

    cohort : str
        name of the cohort

    Methods
    -------

    generate_report(report, repository):
        Generates a report for the detection process.
    """

    def __init__(self, cohort: str) -> None:
        """
        Parameters
        ----------

        cohort : str
            name of the cohort

        """
        self.cohort = cohort

    def generate_report(
        self, report: List[Dict[Any, Any]], repository: str, legacy: bool, excel: bool
    ) -> str:
        """
        Generates a report for the detection process.

        Parameters
        ----------

        report : list
            list of report_data dicts

        repository : str
            required assignment repository name

        legacy : bool
            search for repo globally (time intensive and might encounter rate-limit)

        excel : bool
            generate report in Excel file format

        Returns
        -------

        report_path : str
            path to generated report
        """
        try:
            mode = "LEGACY" if legacy else "NORMAL"

            print("\n░ Initiating report generation... \n")

            fieldnames = [
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
            time_stamp = datetime.fromtimestamp(
                datetime.timestamp(datetime.now())
            ).strftime("%d-%B-%Y")
            os.makedirs(
                os.path.dirname(f"./reports/{self.cohort}/{time_stamp}/"), exist_ok=True
            )
            with open(
                f"./reports/{self.cohort}/{time_stamp}/{mode}-{repository}.csv", "w+"
            ) as sheet:
                document = csv.DictWriter(sheet, fieldnames=fieldnames)
                document.writeheader()
                document.writerows(report)

            if excel:
                print("\n░ Initiating excel report generation... \n")

                csv_file = pandas.read_csv(
                    f"./reports/{self.cohort}/{time_stamp}/{mode}-{repository}.csv"
                )
                csv_file.to_excel(
                    f"./reports/{self.cohort}/{time_stamp}/{mode}-{repository}.xlsx",
                    index=False,
                    header=True,
                    sheet_name=f"{time_stamp} {mode}-{repository}",
                )

                # NOTE: Needs refactor
                return f"./reports/{self.cohort}/{time_stamp}/{mode}-{repository}.xlsx"

            # NOTE: Needs refactor
            return f"./reports/{self.cohort}/{time_stamp}/{mode}-{repository}.csv"

        except Exception as err:
            print(
                "╔═══════════════════════════════════════════════════════════════════╗"
            )
            print(
                "║              Something went wrong in report generation..          ║"
            )
            print(
                "╚═══════════════════════════════════════════════════════════════════╝"
            )
            print(f"× Error: {err}")

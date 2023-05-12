"""This module handles processing students names and repos to detect similarity in their codes per assignment"""

import copy, time
from typing import Dict

from shadow_clone_api.modules.repo_scanner import Scanner
from shadow_clone_api.modules.clone_detector import Detector
from shadow_clone_api.modules.file_writer import Writer
from shadow_clone_api.modules.report_generator import Report
from shadow_clone_api.modules.case_extractor import Extract


class ShadowClone:

    """
    ShadowClone class handles processing students data and returning results.

    ...

    Attributes
    ----------

    scanner : Scanner
        an instance of Scanner class

    writer : Writer
        an instance of Writer class

    detector : Detector
        an instance of Detector class

    report : Report
        an instance of Report class

    extractor : Extractor
        an instance of Extractor class

    cohort : str
        name of the cohort

    code_stack : dict
        information about scanned assignment

    cheater_report : bool
        generate a report for the process

    max_threads : int
        number of maximum active threads in detection process

    quick_mode : bool
        start detecting without writing files locally (resource intensive)

    legacy : bool
        search for repo globally (time intensive and might encounter rate-limit)

    excel : bool
        generate report in Excel file format

    Methods
    -------

    assignment_handler(assignment):
        Maps the assignment file extensions.

    operate():
        Runs the entire detection process.

    extract(cohort, student):
        Collects a target student past cheating record from pre-existing reports.
    """

    def __init__(
        self,
        assignment: str,
        owners: list,
        repository: str,
        cohort: str,
        max_threads: int,
        similarity_threshold: float = 80.0,
        tests: bool = False,
        cheater_report: bool = True,
        quick_mode: bool = False,
        legacy: bool = False,
        excel: bool = False,
        code_stack: Dict[str, dict] = dict(),
    ) -> None:
        """
        Parameters
        ----------

        assignment : str
            assignment type/language

        owners : list
            list of targeted students GitHub IDs

        repository : str
            required assignment repository name

        cohort : str
            name of the cohort

        max_threads : int
            number of maximum active threads in detection process

        similarity_threshold: float
            minimum threshold to consider while comparing similar code

        tests : bool
            include test files in detection process

        cheater_report : bool
            generate a report for the process

        quick_mode : bool
            start detecting without writing files locally (resource intensive)

        legacy : bool
            search for repo globally (time intensive and might encounter rate-limit)

        code_stack : dict
            information about scanned assignment

        excel : bool
            generate report in Excel file format
        """

        self.scanner = Scanner(
            assignment,
            self.assignment_handler(assignment),
            tests,
            owners,
            repository,
            max_threads,
            quick_mode,
            legacy,
        )
        self.detector = Detector(
            similarity_threshold, owners, max_threads, quick_mode, legacy
        )
        self.cohort = cohort
        self.repository = repository
        self.report = Report(cohort)
        self.code_stack = code_stack
        self.cheater_report = cheater_report
        self.writer = Writer(max_threads)
        self.max_threads = max_threads
        self.extractor = Extract()
        self.quick_mode = quick_mode
        self.legacy = legacy
        self.excel = excel

    def assignment_handler(self, assignment: str) -> list:
        """
        Maps the assignment file extentions.

        Parameters
        ----------

        assignment : str
            assignment type/language

        Returns
        -------

        assignment_extensions : list
            list of assignment extensions
        """

        assignment_extensions = {
            "Python": ["py", "ipynb", "html"],
            "JavaScript": ["js", "html"],
            "React": ["js", "jsx", "css"],
            "Java": ["java", "html"],
            ".NET": ["cs", "html"],
        }
        return assignment_extensions[assignment]

    def operate(self) -> str:
        """
        Runs the entire detection process.

        Parameters
        ----------

        None

        Returns
        -------

        report_path : str
            path to generated report
        """

        try:
            start_time = time.perf_counter()
            self.code_stack = self.scanner.scan()
            if not self.quick_mode:
                self.writer.scraper(
                    copy.deepcopy(self.code_stack), self.repository, self.cohort
                )
            report = self.detector.read_files(
                self.code_stack, self.repository, self.cheater_report, self.cohort
            )
            report_path = self.report.generate_report(
                report, self.repository, self.legacy, self.excel
            )
            end_time = time.perf_counter()
            total_time = round(float((end_time - start_time)), 2)
            print(
                "╔═══════════════════════════════════════════════════════════════════╗"
            )
            print(
                "║               All proccesses finished successfully.               ║"
            )
            print(
                "║          It took {} seconds to complete the operation.         ║".format(
                    float(total_time)
                )
            )
            print(
                "╚═══════════════════════════════════════════════════════════════════╝"
            )

            return report_path

        except Exception as err:
            print(
                "╔═══════════════════════════════════════════════════════════════════╗"
            )
            print(
                "║                      Something went wrong...                      ║"
            )
            print(
                "╚═══════════════════════════════════════════════════════════════════╝"
            )
            print(f"× Error: {err}")

    def extract(self, cohort: str, student: str) -> None:
        """
        Collects a target student past cheating record from pre-existing reports.

        Parameters
        ----------

        cohort : str
            name of the cohort

        student : str
            target student GitHub ID

        Returns
        -------

        None
        """

        try:
            self.extractor.search(cohort)
            self.extractor.extract(student)
            print(
                "╔═══════════════════════════════════════════════════════════════════╗"
            )
            print(
                "║           Cheat cases extraction finished successfully.           ║"
            )
            print(
                "╚═══════════════════════════════════════════════════════════════════╝"
            )
        except Exception as err:
            print(
                "╔═══════════════════════════════════════════════════════════════════╗"
            )
            print(
                "║                      Something went wrong...                      ║"
            )
            print(
                "╚═══════════════════════════════════════════════════════════════════╝"
            )
            print(f"× Error: {err}")

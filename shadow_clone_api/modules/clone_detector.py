"""This module detects cloned string content"""

import textdistance, concurrent.futures, sys
from typing import Dict, List, Any


class Detector:
    """
    Detector class compares two cases and calculates the similarities between them.

    ...

    Attributes
    ----------

    similarity_threshold: float
        minimum threshold to consider while comparing similar code

    owners : list
        list of targeted students GitHub IDs

    case1 : str
        first student code as text

    case2 : str
        second student code as text

    report : list
        list of report_data dicts

    max_threads : int
        number of maximum active threads in detection process

    code_stack : dict
        information about scanned assignment

    paths : list
        list of unique pathes read

    cheater_report : bool
        generate a report for the process

    first_owner : str
        first student GitHub ID

    repository : str
        required assignment repository name

    first_branch : str
        name of first student's branch

    first_file_name :
        name of first student's file

    first_url : str
        first student file URL on GitHub

    first_suffix : str
        extension of the first file

    normalized_similarity: int
        similarity percentage of the two student codes

    quick_mode : bool
        start detecting without writing files locally (resource intensive)

    legacy : bool
        search for repo globally (time intensive and might encounter rate-limit)

    Methods
    -------

    read_files(code_stack, repository, cheater_report, cohort):
        Reads all detection case locally written files.

    threaded_read_files(second_owner):
        Does each file read process on a separate thread.

    detect_similarity(first_owner, second_owner, first_branch, second_branch, first_file_name, second_file_name, second_url, case1, case2, repository):
        Compares the similarity of two text files.
    """

    def __init__(
        self,
        similarity_threshold: float,
        owners: list,
        max_threads: int,
        quick_mode: bool,
        legacy: bool,
        report: List[dict] = list(),
    ) -> None:
        """
        Parameters
        ----------

        similarity_threshold: float
            minimum threshold to consider while comparing similar code

        owners : list
            list of targeted students GitHub IDs

        max_threads : int
            number of maximum active threads in detection process

        quick_mode : bool
            start detecting without writing files locally (resource intensive)

        legacy : bool
            search for repo globally (time intensive and might encounter rate-limit)

        report : list
            list of report_data dicts
        """
        self.similarity_threshold = similarity_threshold
        self.owners = owners
        self.case1 = ""
        self.case2 = ""
        self.report = report
        self.max_threads = max_threads
        self.quick_mode = quick_mode
        self.legacy = legacy

    def read_files(
        self,
        code_stack: Dict[str, dict],
        repository: str,
        cheater_report: bool,
        cohort: str,
        paths: List[str] = list(),
    ) -> List[Dict[Any, Any]]:
        """
        Reads all detection case locally written files.

        Parameters
        ----------
        code_stack : dict
            information about scanned assignment

        repository : str
            required assignment repository name

        cheater_report : bool
            generate a report for the process

        cohort : str
            name of the cohort

        paths : list
            list of unique pathes read

        Returns
        -------

        report : list
            list of report_data dicts
        """
        self.cohort = cohort

        try:
            print("\n░ Initiating files comparison...\n")
            self.code_stack = code_stack
            self.paths = paths

            while len(code_stack) >= 2:

                print(f"\n► Comparing file #{len(self.paths)} in progress...\n")
                for _ in range(3):
                    sys.stdout.write("\033[F")

                if self.legacy:
                    first_owner = self.owners.pop(0)
                    while (
                        not first_owner in code_stack.keys() and self.owners
                    ):  # NOTE: Only check for students against others.
                        first_owner = self.owners.pop(
                            0
                        )  # NOTE: Otherwise it would look for non-existent key.

                    if (
                        not self.owners
                    ):  # NOTE : Stop if all students have been checked.
                        break

                else:
                    first_owner = next(
                        iter(code_stack)
                    )  # NOTE: In normal mode, compare everyone (all of them are students).

                first_code_page = code_stack.pop(first_owner)
                first_branches = first_code_page.keys()

                while first_branches:
                    first_branch = next(iter(first_branches))
                    first_urls = first_code_page.pop(first_branch)

                    while first_urls:
                        first_file_name = next(iter(first_urls))
                        first_url = first_urls.pop(first_file_name)
                        self.repository = repository
                        self.cheater_report = cheater_report
                        self.first_owner = first_owner
                        self.repository = repository
                        self.first_branch = first_branch
                        self.first_file_name = first_file_name
                        self.first_url = first_url

                        if (
                            self.first_file_name
                            and not self.first_file_name == "directory_not_found"
                        ):

                            self.first_suffix = first_file_name.split(".")[
                                1
                            ]  # NOTE: Check the first file extension

                            if self.quick_mode:
                                self.case1 = list(self.first_url.values())[0]

                            else:
                                with open(
                                    f"./students_code/{self.cohort}/{self.first_owner}/{self.repository}/{self.first_branch}/{self.first_file_name}.txt",
                                    "r",
                                ) as case1:
                                    self.case1 = case1.read()

                            with concurrent.futures.ThreadPoolExecutor(
                                max_workers=self.max_threads
                            ) as scanner:
                                scanner.map(self.threaded_read_files, code_stack)

            print(f"\n► Completed {len(self.paths)} comparison process...\n")

            return self.report

        except Exception as err:
            print(
                "╔═══════════════════════════════════════════════════════════════════╗"
            )
            print(
                "║              Something went wrong in files comparison...          ║"
            )
            print(
                "╚═══════════════════════════════════════════════════════════════════╝"
            )
            print(f"× Error: {err}")
            return self.report

    def threaded_read_files(self, second_owner: str) -> None:
        """
        Does each file read process on a separate thread.

        Parameters
        ----------
        second_owner : str
            second student GitHub ID

        Returns
        -------

        None
        """

        second_code_page = self.code_stack[second_owner]
        second_branches = second_code_page.keys()

        for second_branch in second_branches:
            second_urls = second_code_page[second_branch]

            for second_file_name in second_urls:
                second_url = second_urls[second_file_name]

                if not second_file_name == "directory_not_found":
                    path = f"{self.cohort}/{self.first_owner}/{self.repository}/{self.first_branch}/{self.first_file_name} : {second_owner}/{self.repository}/{second_branch}/{second_file_name}"
                    if not path in self.paths:
                        self.paths.append(path)

                        second_suffix = second_file_name.split(".")[
                            1
                        ]  # NOTE: Check the second file extension

                        if self.first_suffix == second_suffix:

                            if self.quick_mode:
                                self.case2 = list(second_url.values())[0]

                            else:
                                with open(
                                    f"./students_code/{self.cohort}/{second_owner}/{self.repository}/{second_branch}/{second_file_name}.txt",
                                    "r",
                                ) as case2:
                                    self.case2 = case2.read()

                            if not self.case1 == "" and not self.case2 == "":
                                self.detect_similarity(
                                    self.first_owner,
                                    second_owner,
                                    self.first_branch,
                                    second_branch,
                                    self.first_file_name,
                                    second_file_name,
                                    second_url,
                                    self.case1,
                                    self.case2,
                                    self.repository,
                                )

                            else:
                                continue
                        else:
                            continue

    def detect_similarity(
        self,
        first_owner: str,
        second_owner: str,
        first_branch: str,
        second_branch: str,
        first_file_name: str,
        second_file_name: str,
        second_url: dict,
        case1: str,
        case2: str,
        repository: str,
    ) -> float:
        """
        Compares the similarity of two text files.

        Parameters
        ----------
        first_owner : str
            first student GitHub ID

        second_owner : str
            second student GitHub ID

        first_branch : str
            name of first student's branch

        second_branch : str
            name of second student's branch

        first_file_name :
            name of first student's file

        second_file_name :
            name of second_branch student's file

        first_url : str
            first student file URL on GitHub

        second_url : dict
            second student file URL on GitHub

        case1 : str
            first student code as text

        case2 : str
            second student code as text

        repository : str
            required assignment repository name

        Returns
        -------

        normalized_similarity: int
            similarity percentage of the two student codes

        """
        algorithms = textdistance.algorithms
        self.normalized_similarity: float = round(
            (algorithms.levenshtein.normalized_similarity(case1, case2) * 100), 2
        )
        report_data = {
            "Similarity Score": self.normalized_similarity,
            "First Student": self.first_owner,
            "First Branch": self.first_branch,
            "First File Name": self.first_file_name,
            "First URL": list(self.first_url.keys())[0],
            "Second Student": second_owner,
            "Second Branch": second_branch,
            "Second File Name": second_file_name,
            "Second URL": list(second_url.keys())[0],
        }
        if not self.cheater_report:
            self.report.append(report_data)

        elif self.normalized_similarity >= self.similarity_threshold:
            self.report.append(report_data)

            print(
                f"▌ Comparing {first_owner}'s {repository}/{first_branch}/{first_file_name} to {second_owner}'s {repository}/{second_branch}/{second_file_name}...\n    ▓   Similarity percentage: {self.normalized_similarity}%    ▓\n"
            )
        return self.normalized_similarity

"""This module scrapes code files and writes them locally as text files"""

import requests, os, concurrent.futures
from typing import Dict


class Writer:
    """
    Writer class scrapes code files off GitHub and writes them as text files locally.

    ...

    Attributes
    ----------

    max_threads : int
        number of maximum active threads in detection process

    repository : str
        required assignment repository name

    code_stack : dict
        information about scanned assignment

    cohort : str
        name of the cohort

    Methods
    -------

    scraper(code_stack, repository, cohort):
        Saves a version of the code file as a text file locally.

    threaded_scraper(owner):
            Does the scraping process for each file on a separate thread.
    """

    def __init__(self, max_threads: int) -> None:
        """
        Parameters
        ----------

        max_threads : int
            number of maximum active threads in detection process
        """
        self.max_threads = max_threads

    def scraper(
        self, code_stack: Dict[str, dict], repository: str, cohort: str
    ) -> Dict[str, dict]:
        """
        Saves a version of the code file as a text file locally.

        Parameters
        ----------

        code_stack : dict
            information about scanned assignment

        repository : str
            required assignment repository name

        cohort : str
            name of the cohort

        Returns
        -------

        code_stack : dict
            information about scanned assignment
        """

        try:
            print("\n░ Initiating file writing...\n")

            self.repository = repository
            self.code_stack = code_stack
            self.cohort = cohort
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_threads
            ) as writer:
                writer.map(self.threaded_scraper, code_stack)

            return self.code_stack

        except Exception as err:
            print(
                "╔═══════════════════════════════════════════════════════════════════╗"
            )
            print(
                "║              Something went wrong in file writing...              ║"
            )
            print(
                "╚═══════════════════════════════════════════════════════════════════╝"
            )
            print(f"× Error: {err}")
            return self.code_stack

    def threaded_scraper(self, owner: str) -> None:
        """
        Does the scraping process for each file on a separate thread.

        Parameters
        ----------

        owner : str
            student GitHub ID

        Returns
        -------

        None
        """
        code_page = self.code_stack[owner]
        branches = code_page.keys()

        while branches:
            branch = next(iter(branches))
            urls = code_page.pop(branch)

            while urls:
                file_name = next(iter(urls))
                url = urls.pop(file_name)
                if not file_name == "directory_not_found":
                    os.makedirs(
                        os.path.dirname(
                            f"./students_code/{self.cohort}/{owner}/{self.repository}/{branch}/",
                        ),
                        exist_ok=True,
                    )
                    res = requests.get(url).text
                    print(
                        f"◌ Writing '{self.cohort}/{owner}/{self.repository}/{branch}/{file_name}' to disk..."
                    )
                    with open(
                        f"./students_code/{self.cohort}/{owner}/{self.repository}/{branch}/{file_name}.txt",
                        "w+",
                    ) as code:
                        res = os.linesep.join(
                            [line.strip() for line in res.splitlines() if line]
                        )

                        code.write(res)

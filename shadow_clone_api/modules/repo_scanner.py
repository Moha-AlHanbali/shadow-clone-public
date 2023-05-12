"""This module scans repos for their content"""

import re, os, sys, requests, textdistance, concurrent.futures
from typing import Dict
from dotenv import load_dotenv
from github import Github
from shadow_clone_api.modules.scan_exceptions import assignment_exceptions


load_dotenv()
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
BASE_API_URL = "https://api.github.com/repos"
gh_scanner = Github(GITHUB_ACCESS_TOKEN)


class Scanner:
    """
    Scanner class targets a Github owner's repo and downloads its' content.

    ...

    Attributes
    ----------

     assignment : str
            assignment type/language

    extensions : list
        list of assignment extensions

    tests : bool
        include test files in detection process

    owners : list
        list of targeted students GitHub IDs

    repository : str
        required assignment repository name

    exceptions : list
        list of exception files and folder names to skip

    test_folders : list
        list of test files and folder names

    code_stack : dict
        information about scanned assignment

    max_threads : int
        number of maximum active threads in detection process

    Methods
    -------

    scan():
        Scans GitHub for the repository over the list of owners.

    threaded_scan(owner):
        Does scanning process on separate threads.

    extract_repo(owner):
        Handles misnamed repositories.

    quick_mode : bool
        start detecting without writing files locally (resource intensive)

    legacy : bool
        search for repo globally (time intensive and might encounter rate-limit)
    """

    def __init__(
        self,
        assignment: str,
        extensions: list,
        tests: bool,
        owners: list,
        repository: str,
        max_threads: int,
        quick_mode: bool,
        legacy: bool,
    ) -> None:

        """
        Parameters
        ----------

        assignment : str
            assignment type/language

        extensions : list
            list of assignment extensions

        tests : bool
            include test files in detection process

        owners : list
            list of targeted students GitHub IDs

        repository : str
            required assignment repository name

        max_threads : int
            number of maximum active threads in detection process

        code_stack : dict
            information about scanned assignment

        quick_mode : bool
            start detecting without writing files locally (resource intensive)

        legacy : bool
            search for repo globally (time intensive and might encounter rate-limit)
        """

        self.assignment = assignment
        self.extensions = extensions
        self.tests = tests
        self.owners = owners
        self.repository = repository
        self.exceptions = [".vscode"] + assignment_exceptions[assignment]
        self.test_folders = ["test", "tests", "test.py", "tests.py"]
        self.code_stack: Dict[str, dict] = dict()
        self.max_threads = max_threads
        self.quick_mode = quick_mode
        self.legacy = legacy

    def scan(self) -> dict:
        """
        Scans GitHub for the repository over the list of owners.

        Parameters
        ----------

        assignment : str
            assignment type/language

        Returns
        -------

        code_stack : dict
            information about scanned assignment
        """
        try:
            if self.legacy:
                print(
                    f"\n░ Initiating GLOBAL repository scan for {self.repository}...\n\n"
                )
                repositories = gh_scanner.search_repositories(
                    query=f"language:{self.assignment} {self.repository} in:name"
                )

                for count, repo in enumerate(repositories):
                    if not repo.owner.login in self.owners:
                        self.owners.append(repo.owner.login)

                    print(
                        f"\n► Found {repo.owner.login}'s {self.repository} as repository #{count}...\n"
                    )
                    for _ in range(3):
                        sys.stdout.write("\033[F")

            else:
                print(f"\n░ Initiating repository scan for {self.repository}...\n\n")

            if not self.tests:
                self.exceptions += self.test_folders

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_threads
            ) as scanner:
                scanner.map(self.threaded_scan, self.owners)

            return self.code_stack

        except Exception as err:
            print(
                "╔═══════════════════════════════════════════════════════════════════╗"
            )
            print(
                "║              Something went wrong in repository scan...           ║"
            )
            print(
                "╚═══════════════════════════════════════════════════════════════════╝"
            )
            print(f"× Error: {err}")
            return self.code_stack

    def threaded_scan(self, owner: str) -> dict:
        """
        Does scanning process on separate threads.

        Parameters
        ----------

        owner : str
            student GitHub ID

        Returns
        -------

        code_stack : dict
            information about scanned assignment
        """

        repo_branches = list()
        code_file: Dict[str, dict] = dict()
        try:
            repo = gh_scanner.get_repo(f"{owner}/{self.repository}")
            if (
                self.repository == "data-structures-and-algorithms"
                or self.repository == "datastructures-and-algorithms"
            ):
                print(f"▌ Geting main branch for {self.repository} repository...")
                repo_branches.append(repo.get_branch(branch="main"))
            else:
                repo_branches = list(repo.get_branches())

        except:
            print(
                f"▌ Looking for misspelled {self.repository} in {owner}'s repositories..."
            )

            misnamed_repo = self.extract_repo(owner)

            if misnamed_repo:
                repo = gh_scanner.get_repo(f"{owner}/{misnamed_repo}")
                if (
                    self.repository == "data-structures-and-algorithms"
                    or self.repository == "datastructures-and-algorithms"
                ):
                    print(f"▌ Geting main branch for {misnamed_repo} repository...")
                    repo_branches.append(repo.get_branch(branch="main"))
                else:
                    repo_branches = list(repo.get_branches())

                print(f"▌ Found {misnamed_repo} in {owner}'s repositories▌")

            else:

                print(f"▌ {self.repository} was not found in {owner}'s repositories!")

                code_file["directory_not_found"] = dict()
                code_file["directory_not_found"][
                    "directory_not_found"
                ] = "https://github.com"
                self.code_stack[owner] = code_file

        for branch in repo_branches:

            print(f"■ Scanning {owner}'s {repo.name}: {branch.name}...")
            contents = repo.get_contents("", branch.name)
            code_file[branch.name] = dict()
            while contents:
                file_content = contents.pop(0)  # type: ignore[union-attr]
                if not file_content.name in self.exceptions:
                    if file_content.type == "dir":
                        contents.extend(  # type: ignore[union-attr]
                            repo.get_contents(file_content.path, branch.name)  # type: ignore[arg-type]
                        )
                    else:
                        for extension in self.extensions:
                            if re.search(f"^.*\.({extension})$", file_content.path):
                                if self.quick_mode:
                                    code_file[branch.name][file_content.name] = {
                                        file_content.download_url: os.linesep.join(
                                            [
                                                line.strip()
                                                for line in requests.get(
                                                    file_content.download_url
                                                ).text.splitlines()
                                                if line
                                            ]
                                        )  # NOTE: Removes empty lines and extra white spaces
                                    }

                                else:
                                    code_file[branch.name][
                                        file_content.name
                                    ] = file_content.download_url

                                print(
                                    f"◌ {owner}/{repo.name}/{branch.name}: Found {file_content.name} file"
                                )

        self.code_stack[owner] = code_file

        return self.code_stack

    def extract_repo(self, owner: str) -> str:
        """
        Handles misnamed repositories.

        Parameters
        ----------

        owner : str
            student GitHub ID

        Returns
        -------

        misnamed_repo : str
            the name of the repository
        """
        user = gh_scanner.get_user(owner)
        repos = user.get_repos()
        misnamed_repo = ""

        for repo in repos:
            similarity = textdistance.algorithms.levenshtein.normalized_similarity(
                repo.name, self.repository
            )

            if similarity >= 0.50:
                misnamed_repo = repo.name
            else:
                continue

            if (
                textdistance.algorithms.levenshtein.normalized_similarity(
                    repo.name, misnamed_repo
                )
                > similarity
            ):
                misnamed_repo = repo.name

        return misnamed_repo

import argparse

# Functions imported from other modules within the autopr package
from .git_utils import get_repo_from_git_config
from .github_service import create_pr, list_issues, start_work_on_issue


def main():
    parser = argparse.ArgumentParser(description="AutoPR CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subparser for the 'create' command
    create_parser = subparsers.add_parser("create", help="Create a new PR")
    create_parser.add_argument("--title", required=True, help="Title of the new PR")
    create_parser.add_argument("--base", help="The base branch for the PR.")

    # Subparser for the 'ls' command
    list_parser = subparsers.add_parser(
        "ls", help="List issues in the current repository"
    )
    list_parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        required=False,
        help="Include all issues (open and closed). Default is open issues only.",
    )

    # Subparser for the 'workon' command
    workon_parser = subparsers.add_parser(
        "workon", help="Start working on a GitHub issue and create a new branch."
    )
    workon_parser.add_argument(
        "issue_number", type=int, help="The number of the GitHub issue to work on."
    )

    args = parser.parse_args()

    # Commands that don't need repo detection first (or handle it themselves)
    if args.command == "workon":
        start_work_on_issue(args.issue_number)
        return

    # For other commands, detect repository first
    try:
        repo = get_repo_from_git_config()
        print(f"Detected repository: {repo}")
    except Exception as e:
        print(f"Error detecting repository: {e}")
        return

    if args.command == "create":
        create_pr(args.title)
    elif args.command == "ls":
        list_issues(show_all_issues=args.all)


# Note: The if __name__ == '__main__': block is typically not included
# in a module file that's meant to be imported. The entry point
# script (run_cli.py) will handle that.

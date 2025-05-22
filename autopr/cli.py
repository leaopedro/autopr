import argparse

# Functions imported from other modules within the autopr package
from .git_utils import get_repo_from_git_config
from .github_service import create_pr, list_issues


def main():
    parser = argparse.ArgumentParser(description="AutoPR CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Subparser for the 'create' command
    create_parser = subparsers.add_parser("create", help="Create a new PR")
    create_parser.add_argument("--title", required=True, help="Title of the new PR")

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

    args = parser.parse_args()

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

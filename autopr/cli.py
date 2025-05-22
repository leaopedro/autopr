import argparse

# Functions imported from other modules within the autopr package
from .git_utils import get_repo_from_git_config
from .github_service import (
    create_pr, 
    list_issues, 
    start_work_on_issue, 
    get_staged_diff,
    git_commit
)
from .ai_service import get_commit_message_suggestion

# Placeholder function for commit logic
def handle_commit_command():
    print("Handling commit command...")
    staged_diff = get_staged_diff()
    if staged_diff:
        print("Staged Diffs:\n")
        print(staged_diff)
        print("\nAttempting to get AI suggestion for commit message...")
        suggestion = get_commit_message_suggestion(staged_diff)
        
        # Check for error messages from AI service
        if suggestion.startswith("[Error") or suggestion.startswith("[OpenAI client not initialized") or suggestion.startswith("[No diff provided"):
            print(f"\nCould not get AI suggestion: {suggestion}")
            print("Please commit manually using git.")
            return

        print(f"\nSuggested commit message:\n{suggestion}")
        
        confirmation = input("\nDo you want to commit with this message? (y/n): ").lower()
        if confirmation == 'y':
            print("Committing with the suggested message...")
            commit_success, commit_output = git_commit(suggestion)
            if commit_success:
                print("Commit successful!")
                print(commit_output) # Print output from git commit
            else:
                print("Commit failed.")
                print(commit_output) # Print error output from git commit
        else:
            print("Commit aborted by user. Please commit manually using git.")
    else:
        print("No changes staged for commit.")

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

    # Subparser for the 'commit' command
    commit_parser = subparsers.add_parser("commit", help="Process staged changes for a commit.")
    # No arguments for commit in MVP

    args = parser.parse_args()

    # For commands that need repository detection or further dispatch
    try:
        repo = get_repo_from_git_config() # commit will also need this
        print(f"Detected repository: {repo}")
    except Exception as e:
        print(f"Error detecting repository: {e}")
        # For commands that absolutely cannot run without repo context from .git/config
        if args.command in ["ls", "create"]:
             return
        # For 'workon' and 'commit', they might have deeper git interactions that could still fail
        # but let them proceed to their specific handlers for now.
        pass 

    if args.command == "create":
        create_pr(args.title)
    elif args.command == "workon":
        start_work_on_issue(args.issue_number)
    elif args.command == "ls":
        list_issues(show_all_issues=args.all)
    elif args.command == "commit":
        handle_commit_command()


# Note: The if __name__ == '__main__': block is typically not included
# in a module file that's meant to be imported. The entry point
# script (run_cli.py) will handle that.

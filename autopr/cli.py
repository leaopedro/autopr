import argparse

# Functions imported from other modules within the autopr package
from .git_utils import get_repo_from_git_config
from .github_service import (
    create_pr,
    list_issues,
    start_work_on_issue,
    get_staged_diff,
    git_commit,
    get_pr_changes,
    post_pr_review_comment,
)
from .ai_service import (
    get_commit_message_suggestion,
    get_pr_description_suggestion,
    get_pr_review_suggestions,
)


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
        if (
            suggestion.startswith("[Error")
            or suggestion.startswith("[OpenAI client not initialized")
            or suggestion.startswith("[No diff provided")
        ):
            print(f"\nCould not get AI suggestion: {suggestion}")
            print("Please commit manually using git.")
            return

        print(f"\nSuggested commit message:\n{suggestion}")

        confirmation = input(
            "\nDo you want to commit with this message? (y/n): "
        ).lower()
        if confirmation == "y":
            print("Committing with the suggested message...")
            commit_success, commit_output = git_commit(suggestion)
            if commit_success:
                print("Commit successful!")
                print(commit_output)  # Print output from git commit
            else:
                print("Commit failed.")
                print(commit_output)  # Print error output from git commit
        else:
            print("Commit aborted by user. Please commit manually using git.")
    else:
        print("No changes staged for commit.")


def handle_review_command(pr_number: int):
    """
    Handles the 'review' command logic, including fetching PR changes and posting review comments.
    """
    print(f"Fetching changes for PR #{pr_number}...")
    pr_changes = get_pr_changes(pr_number)
    if not pr_changes:
        print("Could not fetch PR changes. Please check the PR number and try again.")
        return

    print("\nAnalyzing changes and generating review suggestions...")
    suggestions = get_pr_review_suggestions(pr_changes)
    if not suggestions:
        print(
            "No suggestions were generated. The changes might be too complex or there might be an error."
        )
        return

    print(f"\nGenerated {len(suggestions)} suggestions for review.")
    print("\nPosting review comments...")

    success_count = 0
    for suggestion in suggestions:
        try:
            path = suggestion["path"]
            line = suggestion["line"]
            body = suggestion["suggestion"]

            if post_pr_review_comment(pr_number, body, path, line):
                success_count += 1
                print(f"Posted comment on {path}:{line}")
            else:
                print(f"Failed to post comment on {path}:{line}")
        except KeyError as e:
            print(f"Error in suggestion format: missing {e}")
            continue
        except Exception as e:
            print(f"Unexpected error posting comment: {e}")
            continue

    print(
        f"\nReview complete. Successfully posted {success_count} out of {len(suggestions)} comments."
    )


def main():
    parser = argparse.ArgumentParser(description="AutoPR CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subparser for the 'review' command
    review_parser = subparsers.add_parser(
        "review",
        help="Review a PR and post AI-generated suggestions as comments.",
    )
    review_parser.add_argument(
        "pr_number",
        type=int,
        help="The number of the PR to review.",
    )

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
    commit_parser = subparsers.add_parser(
        "commit", help="Process staged changes for a commit."
    )
    # No arguments for commit in MVP

    args = parser.parse_args()

    repo_full_path = "."  # Default to current directory, can be refined if needed
    try:
        repo_name = get_repo_from_git_config()
        print(f"Detected repository: {repo_name}")
    except Exception as e:
        print(f"Error detecting repository: {e}")
        if args.command in [
            "ls",
            "pr",
            "review",
        ]:  # Added review to commands that can work without repo
            return
        pass

    if args.command == "pr":
        handle_pr_create_command(base_branch=args.base, repo_path=repo_full_path)
    elif args.command == "workon":
        start_work_on_issue(args.issue_number, repo_path=repo_full_path)
    elif args.command == "ls":
        list_issues(show_all_issues=args.all)
    elif args.command == "commit":
        handle_commit_command()
    elif args.command == "review":
        handle_review_command(args.pr_number)


# Note: The if __name__ == '__main__': block is typically not included
# in a module file that's meant to be imported. The entry point
# script (run_cli.py) will handle that.

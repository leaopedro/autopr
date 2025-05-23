import argparse

# Functions imported from other modules within the autopr package
from .git_utils import get_repo_from_git_config
from .github_service import (
    list_issues,
    start_work_on_issue,
    get_staged_diff,
    git_commit,
    get_current_issue_number,
    get_issue_details,
    get_commit_messages_for_branch,
    create_pr_gh,
)

# Import the actual create_pr from github_service if we rename the cli handler
# from .github_service import create_pr as service_create_pr

from .ai_service import get_commit_message_suggestion, get_pr_description_suggestion


# Placeholder function for commit logic
def handle_commit_command():  # Handles the 'commit' command logic, including AI suggestions.
    print("Handling commit command...")
    staged_diff = get_staged_diff()
    if staged_diff:
        diff_len = len(staged_diff)
        if diff_len > 450000:
            print(
                f"Error: Diff is too large ({diff_len} characters). Maximum allowed is 450,000 characters."
            )
            print("Please break down your changes into smaller commits.")
            return
        elif diff_len > 400000:
            print(
                f"Warning: Diff is very large ({diff_len} characters). AI suggestion quality may be affected."
            )
            print(
                "Consider breaking down your changes into smaller commits for better results."
            )

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


def handle_pr_create_command(base_branch: str, repo_path: str = "."):
    print(f"Initiating PR creation process against base branch: {base_branch}")

    commit_messages = get_commit_messages_for_branch(base_branch)
    if commit_messages is None:
        print(
            f"Error: Could not retrieve commit messages for the current branch against base '{base_branch}'."
        )
        return
    if not commit_messages:
        print(
            "No new commit messages found on this branch compared to base. Cannot generate PR description."
        )
        return

    print(f"Retrieved {len(commit_messages)} commit message(s).")

    print("\nAttempting to generate PR title and body using AI...")
    pr_title_suggestion, pr_body_suggestion = get_pr_description_suggestion(
        commit_messages
    )

    print("\n--- Suggested PR Title ---")
    print(pr_title_suggestion)
    print("\n--- Suggested PR Body ---")
    print(pr_body_suggestion)

    confirmation = input("Do you want to create this PR? (y/n): ").lower()
    if confirmation == "y":
        if not pr_title_suggestion:
            print("Error: Cannot create PR with an empty title suggestion.")
            return
        if not pr_body_suggestion:  # Or decide if an empty body is acceptable
            print(
                "Warning: PR body suggestion is empty. Proceeding with an empty body."
            )
            # Alternatively, pr_body_suggestion = "" if you want to ensure it's a string

        print("Attempting to create PR...")
        success, output = create_pr_gh(
            pr_title_suggestion, pr_body_suggestion, base_branch
        )
        if success:
            print("PR created successfully!")
            print(output)  # Print link to PR and other output from gh
        else:
            print("Failed to create PR.")
            print(output)  # Print error message from gh or the service
    else:
        print("PR creation aborted by user.")


def main():
    parser = argparse.ArgumentParser(description="AutoPR CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subparser for the 'pr' command (renamed from 'create')
    pr_parser = subparsers.add_parser(
        "pr",
        help="Suggest title and body for a new PR and create it after confirmation.",
    )  # Renamed and updated help
    pr_parser.add_argument(
        "--title",
        required=False,
        help="(Optional) User-specified title hint (currently ignored by AI). AI will suggest a title.",
    )
    pr_parser.add_argument(
        "--base",
        required=False,
        default="main",
        help="The target base branch for the PR. Defaults to 'main'.",
    )  # Now optional, defaults to main

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
        # Potentially derive repo_full_path if get_repo_from_git_config can provide it or we add a helper
    except Exception as e:
        print(f"Error detecting repository: {e}")
        if args.command in ["ls", "pr"]:  # Renamed from create to pr
            return
        pass

    if args.command == "pr":  # Renamed from create to pr
        # The old create_pr(args.title) is removed in favor of the new handler
        handle_pr_create_command(base_branch=args.base, repo_path=repo_full_path)
    elif args.command == "workon":
        start_work_on_issue(
            args.issue_number, repo_path=repo_full_path
        )  # Assuming start_work_on_issue can take repo_path
    elif args.command == "ls":
        list_issues(show_all_issues=args.all)
    elif args.command == "commit":
        handle_commit_command()  # repo_path could be passed if needed by get_staged_diff


# main() is the designated entry point for the CLI, called by setup.py.

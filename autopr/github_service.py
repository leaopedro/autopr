import subprocess
import json
import re
import os


def list_issues(show_all_issues: bool = False):
    print("Listing Issues...")
    try:
        cmd = ["gh", "issue", "list"]
        if show_all_issues:
            cmd.extend(["--state", "all"])

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout.strip():
            print("Issues:")
            print(result.stdout)
        else:
            print("No issues found for the current filters.")
    except subprocess.CalledProcessError as e:
        print("Failed to fetch issues.")
        print(e.output)


def _sanitize_branch_name(name):
    """Sanitizes a string to be a valid git branch name."""
    # Lowercase
    name = name.lower()
    # Replace spaces and common separators with hyphens
    name = re.sub(r"[\s_.:/]+", "-", name)
    # Remove any characters that are not alphanumeric or hyphen
    name = re.sub(r"[^a-z0-9-]", "", name)
    # Remove leading/trailing hyphens
    name = name.strip("-")
    # Limit length to avoid issues (e.g., 50 chars for the title part)
    return name[:50]


def get_staged_diff() -> str | None:
    """Gets the staged git diff.
    Returns the diff string or None if error or no diff.
    """
    try:
        # Ensure we are in a git repository, otherwise `git diff` might act unexpectedly or error.
        # A simple check could be to see if `.git` exists or `git rev-parse --is-inside-work-tree`
        # For now, assume `handle_commit_command` is called in a context where being in a git repo is expected.

        result = subprocess.run(
            ["git", "diff", "--staged"],
            capture_output=True,
            text=True,
            check=False,  # Don't raise an exception for non-zero exit if there are no staged changes (it might return 1)
        )
        # `git diff --staged` can return exit code 1 if there are differences, 0 if none.
        # We are interested in the stdout (the diff itself).
        # An error (like not being in a git repo) might result in a different exit code and stderr output.
        if result.stderr:
            # This could capture git errors like "not a git repository"
            print(f"Error getting staged diff: {result.stderr.strip()}")
            return None  # Or handle more gracefully

        return (
            result.stdout.strip()
        )  # .strip() to remove leading/trailing whitespace, including newlines if diff is empty

    except FileNotFoundError:  # If git command is not found
        print(
            "Error: git command not found. Please ensure git is installed and in your PATH."
        )
        return None
    except Exception as e:
        print(f"An unexpected error occurred while getting staged diff: {e}")
        return None


def git_commit(message: str) -> tuple[bool, str]:
    """Performs a git commit with the given message.
    Returns a tuple (success_boolean, output_string).
    """
    try:
        # Using check=False to manually handle success/failure based on returncode
        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            # Git commit can fail for various reasons (e.g., nothing to commit, hooks failing)
            # Stderr usually contains the error message from git
            error_message = result.stderr.strip()
            if (
                not error_message and result.stdout.strip()
            ):  # Sometimes error is on stdout
                error_message = result.stdout.strip()
            return False, error_message
    except FileNotFoundError:  # If git command is not found
        return (
            False,
            "Error: git command not found. Please ensure git is installed and in your PATH.",
        )
    except Exception as e:
        return False, f"An unexpected error occurred during git commit: {e}"


def get_current_issue_number(repo_path: str = ".") -> int | None:
    """Reads the current issue number from .git/.autopr_current_issue."""
    context_file_path = os.path.join(repo_path, ".git", ".autopr_current_issue")
    try:
        if os.path.exists(context_file_path):
            with open(context_file_path, "r") as f:
                content = f.read().strip()
                return int(content)
        else:
            print(f"Context file not found: {context_file_path}")
            return None
    except ValueError:
        print(f"Error: Invalid content in {context_file_path}. Expected an integer.")
        return None
    except Exception as e:
        print(f"Error reading current issue number: {e}")
        return None


def get_issue_details(issue_number: int) -> dict | None:
    """Fetches issue details (number, title, body, labels) using gh CLI."""
    print(f"Fetching details for issue #{issue_number}...")
    try:
        gh_issue_cmd = [
            "gh",
            "issue",
            "view",
            str(issue_number),
            "--json",
            "number,title,body,labels",  # Added body and labels
        ]
        result = subprocess.run(
            gh_issue_cmd, capture_output=True, text=True, check=True
        )
        issue_data = json.loads(result.stdout)
        # Ensure essential fields are present or provide defaults if appropriate for your use case
        # For PR generation, title and body are quite important.
        return issue_data
    except subprocess.CalledProcessError as e:
        print(f"Error fetching issue details for #{issue_number} via gh:")
        print(f"Command '{' '.join(e.cmd)}' failed with exit code {e.returncode}")
        if e.stdout:
            print(f"Stdout:\n{e.stdout}")
        if e.stderr:
            print(f"Stderr:\n{e.stderr}")
        return None
    except json.JSONDecodeError:
        print(
            f"Error: Could not parse issue details for #{issue_number} from gh CLI output."
        )
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching issue details: {e}")
        return None


def get_commit_messages_for_branch(base_branch: str) -> list[str] | None:
    """Gets commit messages (subjects only) from current branch since divergence from base_branch."""
    print(
        f"Fetching commit messages for current branch against base '{base_branch}'..."
    )
    try:
        # git log main..HEAD --pretty=format:%s
        # The range <base_branch>..HEAD means commits in HEAD that are not in <base_branch>
        cmd = ["git", "log", f"{base_branch}..HEAD", "--pretty=format:%s"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout:
            commit_messages = result.stdout.strip().split("\n")
            return commit_messages
        else:
            return (
                []
            )  # No commits found, or an empty list if the command ran but no output
    except subprocess.CalledProcessError as e:
        print(f"Error getting commit messages:")
        print(f"Command '{' '.join(e.cmd)}' failed with exit code {e.returncode}")
        if e.stdout:
            print(f"Stdout:\n{e.stdout}")
        if e.stderr:
            print(f"Stderr:\n{e.stderr}")
        # Check if the error is because the base_branch doesn't exist or is not an ancestor
        if (
            "unknown revision" in e.stderr.lower()
            or "not a valid object name" in e.stderr.lower()
        ):
            print(
                f"Hint: Ensure '{base_branch}' is a valid branch and an ancestor of the current branch."
            )
        return None
    except FileNotFoundError:
        print("Error: git command not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching commit messages: {e}")
        return None


def start_work_on_issue(issue_number: int, repo_path: str = "."):
    """Fetches issue details, creates a new branch, and stores issue context."""
    print(f"Starting work on issue #{issue_number}...")
    try:
        # Fetch issue details (using the new more detailed function for consistency, though only title is used here)
        issue_data = get_issue_details(issue_number)
        if not issue_data:
            # get_issue_details already prints errors, so just return
            return
        issue_title = issue_data.get("title", "untitled")

        # Generate branch name
        sanitized_title = _sanitize_branch_name(issue_title)
        branch_name = f"feature/{issue_number}-{sanitized_title}"

        print(f"Creating and switching to branch: {branch_name}")
        # Assuming git commands are run from the root of the repo, repo_path might not be needed for subprocess
        # if the script's CWD is set correctly by the user or a higher level function.
        # For now, let's keep subprocess calls as they are, assuming they operate in current CWD.
        git_checkout_cmd = ["git", "checkout", "-b", branch_name]
        subprocess.run(git_checkout_cmd, check=True, capture_output=True, text=True)

        # Store issue context
        git_dir_path = os.path.join(repo_path, ".git")
        if not os.path.isdir(git_dir_path):
            print(
                f"Error: .git directory not found at {git_dir_path}. Are you in a git repository?"
            )
            return

        context_file_path = os.path.join(git_dir_path, ".autopr_current_issue")
        with open(context_file_path, "w") as f:
            f.write(str(issue_number))
        print(
            f"Issue #{issue_number} context saved. You are now on branch {branch_name}."
        )

    except subprocess.CalledProcessError as e:
        # This will now primarily catch errors from git checkout if get_issue_details succeeded
        print(
            f"Error during 'workon' process (git checkout) for issue #{issue_number}:"
        )
        print(f"Command '{' '.join(e.cmd)}' failed with exit code {e.returncode}")
        if e.stdout:
            print(f"Stdout:\n{e.stdout}")
        if e.stderr:
            print(f"Stderr:\n{e.stderr}")
    # json.JSONDecodeError is handled by get_issue_details
    except Exception as e:
        print(f"An unexpected error occurred in start_work_on_issue: {e}")


def create_pr_gh(title: str, body: str, base_branch: str) -> tuple[bool, str]:
    """
    Creates a pull request on GitHub using the gh CLI.

    Args:
        title: The title of the pull request.
        body: The body content of the pull request.
        base_branch: The base branch for the pull request.

    Returns:
        A tuple containing a boolean indicating success and the stdout/stderr from the command.
    """
    try:
        # Using --fill to auto-populate the PR body from commits if the body is empty
        # However, we are providing a body, so this might just be a good default.
        # If we want to strictly use the AI body, we ensure 'body' is not empty.
        # If 'body' can be empty and we want gh to auto-fill, then we'd adjust logic.
        command = [
            "gh",
            "pr",
            "create",
            "--title",
            title,
            "--body",
            body,
            "--base",
            base_branch,
        ]

        # If the body is empty, `gh pr create` can sometimes hang or open an editor.
        # To avoid this, we can use a placeholder if the AI returns an empty body,
        # or rely on `gh`'s `--fill` behavior if that's desired (though `--fill` is more about commit messages).
        # For now, we assume AI provides a non-empty body. If body is empty, user might need to intervene or we add placeholder.
        # An alternative for empty body: gh pr create --title "title" --body "" --base base --fill
        # But for now, we pass the body as is. If it's empty, it's an empty body PR.

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,  # We'll check success based on returncode
        )
        if process.returncode == 0:
            return True, process.stdout
        else:
            error_message = f"Error creating PR: {process.stderr.strip()}"
            if (
                process.stdout.strip()
            ):  # Sometimes gh sends info to stdout even on error
                error_message += f"\nstdout: {process.stdout.strip()}"
            return False, error_message
    except FileNotFoundError:
        return (
            False,
            "Error: 'gh' command not found. Please ensure it is installed and in your PATH.",
        )
    except Exception as e:
        return (
            False,
            f"An unexpected error occurred while trying to create PR with gh: {e}",
        )


def get_pr_changes(pr_number: int) -> str:
    """
    Fetches the changes (diff) for a given PR number using 'gh pr view --patch'.
    
    Args:
        pr_number: The number of the PR to fetch changes for.
        
    Returns:
        The diff string if successful, empty string otherwise.
    """
    print(f"Fetching changes for PR #{pr_number}...")
    try:
        cmd = ["gh", "pr", "view", str(pr_number), "--patch"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PR changes for PR #{pr_number} via gh:")
        print(f"Command '{' '.join(e.cmd)}' failed with exit code {e.returncode}")
        if e.stdout:
            print(f"Stdout:\n{e.stdout}")
        if e.stderr:
            print(f"Stderr:\n{e.stderr}")
        return ""
    except FileNotFoundError:
        print("Error: 'gh' command not found. Please ensure it is installed and in your PATH.")
        return ""
    except Exception as e:
        print(f"An unexpected error occurred while fetching PR changes: {e}")
        return ""


def _get_repo_details() -> tuple[str, str] | None:
    """Fetches repository owner and name using gh repo view."""
    try:
        cmd = ["gh", "repo", "view", "--json", "owner,name"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        # Owner can be a dict for organizations, so access 'login' field
        owner_login = data["owner"]["login"] if isinstance(data["owner"], dict) else data["owner"]
        repo_name = data["name"]
        return owner_login, repo_name
    except subprocess.CalledProcessError as e:
        print(f"Error fetching repository details: {e.stderr}")
        return None
    except json.JSONDecodeError:
        print("Error parsing repository details from gh.")
        return None
    except FileNotFoundError:
        print("Error: 'gh' command not found for _get_repo_details.")
        return None
    except Exception as e:
        print(f"Unexpected error in _get_repo_details: {e}")
        return None


def _get_pr_head_commit_sha(pr_number: int) -> str | None:
    """Fetches the head commit SHA for a given PR number."""
    try:
        cmd = ["gh", "pr", "view", str(pr_number), "--json", "headRefOid"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return data.get("headRefOid")
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PR head commit SHA for PR #{pr_number}: {e.stderr}")
        return None
    except json.JSONDecodeError:
        print(f"Error parsing PR head commit SHA for PR #{pr_number}.")
        return None
    except FileNotFoundError:
        print("Error: 'gh' command not found for _get_pr_head_commit_sha.")
        return None
    except Exception as e:
        print(f"Unexpected error in _get_pr_head_commit_sha for PR #{pr_number}: {e}")
        return None


def post_pr_review_comment(pr_number: int, body: str, path: str, line: int) -> bool:
    """
    Posts a review comment on a specific line of a PR using 'gh api'.
    
    Args:
        pr_number: The number of the PR to comment on.
        body: The comment text.
        path: The path to the file being commented on.
        line: The line number to comment on.
        
    Returns:
        True if the comment was posted successfully, False otherwise.
    """
    print(f"Attempting to post review comment on PR #{pr_number}, file {path}:{line}")
    repo_details = _get_repo_details()
    if not repo_details:
        print("Failed to post comment: Could not retrieve repository details.")
        return False
    owner, repo = repo_details

    commit_sha = _get_pr_head_commit_sha(pr_number)
    if not commit_sha:
        print(f"Failed to post comment: Could not retrieve head commit SHA for PR #{pr_number}.")
        return False

    api_path = f"repos/{owner}/{repo}/pulls/{pr_number}/comments"
    # Construct fields for the gh api command.
    # Using -f for simple key=value and --input for JSON body if it gets complex.
    # For now, -f should work.
    fields = [
        "-f", f"body={body}",
        "-f", f"commit_id={commit_sha}",
        "-f", f"path={path}",
        "-F", f"line={line}" # Use -F for integer to avoid issues with gh parsing
    ]
    
    cmd = ["gh", "api", api_path, "-X", "POST"] + fields
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Successful API call usually returns JSON data of the created comment
        print(f"Successfully posted comment on PR #{pr_number} to {path}:{line}. Response: {result.stdout[:100]}...")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error posting review comment via gh api for PR #{pr_number}:")
        print(f"Command '{' '.join(e.cmd)}' failed with exit code {e.returncode}")
        if e.stdout:
            print(f"Stdout:\n{e.stdout}")
        if e.stderr:
            print(f"Stderr:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print("Error: 'gh' command not found. Please ensure it is installed and in your PATH.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while posting review comment: {e}")
        return False

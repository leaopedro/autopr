import subprocess
import json
import re
import os


def create_pr(title):
    print(f"Creating a new PR with title: {title}")


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
    name = re.sub(r'[\s_.:/]+', '-', name)
    # Remove any characters that are not alphanumeric or hyphen
    name = re.sub(r'[^a-z0-9-]', '', name)
    # Remove leading/trailing hyphens
    name = name.strip('-')
    # Limit length to avoid issues (e.g., 50 chars for the title part)
    return name[:50]


def start_work_on_issue(issue_number: int):
    """Fetches issue details, creates a new branch, and stores issue context."""
    print(f"Starting work on issue #{issue_number}...")
    try:
        # Fetch issue details
        gh_issue_cmd = [
            'gh', 'issue', 'view',
            str(issue_number),
            '--json', 'number,title'
        ]
        result = subprocess.run(gh_issue_cmd, capture_output=True, text=True, check=True)
        issue_data = json.loads(result.stdout)
        issue_title = issue_data.get('title', 'untitled')

        # Generate branch name
        sanitized_title = _sanitize_branch_name(issue_title)
        branch_name = f"feature/{issue_number}-{sanitized_title}"

        print(f"Creating and switching to branch: {branch_name}")
        git_checkout_cmd = ['git', 'checkout', '-b', branch_name]
        subprocess.run(git_checkout_cmd, check=True, capture_output=True, text=True) # capture_output to hide git success msgs if desired
        
        # Store issue context
        # Ensure .git directory exists (it should in a git repo)
        git_dir = ".git"
        if not os.path.isdir(git_dir):
            print(f"Error: .git directory not found. Are you in a git repository?")
            return
        
        context_file_path = os.path.join(git_dir, ".autopr_current_issue")
        with open(context_file_path, 'w') as f:
            f.write(str(issue_number))
        print(f"Issue #{issue_number} context saved. You are now on branch {branch_name}.")

    except subprocess.CalledProcessError as e:
        print(f"Error during 'workon' process for issue #{issue_number}:")
        print(f"Command '{' '.join(e.cmd)}' failed with exit code {e.returncode}")
        if e.stdout:
            print(f"Stdout:\n{e.stdout}")
        if e.stderr:
            print(f"Stderr:\n{e.stderr}")
    except json.JSONDecodeError:
        print(f"Error: Could not parse issue details from gh CLI output.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

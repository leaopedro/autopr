import subprocess


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

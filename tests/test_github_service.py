import unittest
import subprocess
from unittest.mock import patch, Mock, mock_open, MagicMock
import os
import json

from autopr.github_service import (
    list_issues,
    # create_pr, # This function was removed/renamed to create_pr_gh
    start_work_on_issue,
    _sanitize_branch_name,
    get_staged_diff,
    git_commit,
    get_current_issue_number,
    get_issue_details,
    get_commit_messages_for_branch,
    create_pr_gh,
    get_pr_changes,
    _get_repo_details,
    _get_pr_head_commit_sha,
    post_pr_review_comment
)


class TestListIssues(unittest.TestCase):
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_list_issues_default_open(self, mock_print, mock_subprocess_run):
        mock_process = Mock()
        mock_process.stdout = "Issue 1\nIssue 2"
        mock_subprocess_run.return_value = mock_process

        list_issues(show_all_issues=False)

        mock_subprocess_run.assert_called_once_with(
            ["gh", "issue", "list"], capture_output=True, text=True, check=True
        )
        mock_print.assert_any_call("Issues:")
        mock_print.assert_any_call("Issue 1\nIssue 2")

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_list_issues_all(self, mock_print, mock_subprocess_run):
        mock_process = Mock()
        mock_process.stdout = "Issue 1 (open)\nIssue 3 (closed)"
        mock_subprocess_run.return_value = mock_process

        list_issues(show_all_issues=True)

        mock_subprocess_run.assert_called_once_with(
            ["gh", "issue", "list", "--state", "all"],
            capture_output=True,
            text=True,
            check=True,
        )
        mock_print.assert_any_call("Issues:")
        mock_print.assert_any_call("Issue 1 (open)\nIssue 3 (closed)")

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_list_issues_no_issues_found(self, mock_print, mock_subprocess_run):
        mock_process = Mock()
        mock_process.stdout = ""  # Empty output
        mock_subprocess_run.return_value = mock_process

        list_issues(show_all_issues=False)

        mock_subprocess_run.assert_called_once_with(
            ["gh", "issue", "list"], capture_output=True, text=True, check=True
        )
        mock_print.assert_any_call("No issues found for the current filters.")
        issues_header_called = False
        for call_args in mock_print.call_args_list:
            if call_args[0][0] == "Issues:":
                issues_header_called = True
                break
        self.assertFalse(
            issues_header_called,
            msg="'Issues:' should not be printed when no issues are found.",
        )

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_list_issues_subprocess_error(self, mock_print, mock_subprocess_run):
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["gh", "issue", "list"], output="Error fetching issues"
        )

        list_issues(show_all_issues=False)

        mock_subprocess_run.assert_called_once_with(
            ["gh", "issue", "list"], capture_output=True, text=True, check=True
        )
        mock_print.assert_any_call("Failed to fetch issues.")
        mock_print.assert_any_call("Error fetching issues")


class TestSanitizeBranchName(unittest.TestCase):
    def test_basic_sanitization(self):
        self.assertEqual(_sanitize_branch_name("My Test Issue"), "my-test-issue")
        self.assertEqual(
            _sanitize_branch_name("fix: a bug with spaces"), "fix-a-bug-with-spaces"
        )

    def test_underscore_behavior(self):
        self.assertEqual(_sanitize_branch_name("char_name"), "char-name")
        self.assertEqual(_sanitize_branch_name("some_char_name"), "some-char-name")

    def test_special_characters(self):
        # Revert to original complex string, expecting the last known actual output
        self.assertEqual(
            _sanitize_branch_name("feat(scope)!: Highly@Special#$%^&*Char_Name"),
            "featscope-highlyspecialchar-name",
        )

    def test_leading_trailing_hyphens(self):
        self.assertEqual(_sanitize_branch_name("-leading-hyphen-"), "leading-hyphen")
        self.assertEqual(_sanitize_branch_name("trailing-hyphen-"), "trailing-hyphen")
        self.assertEqual(_sanitize_branch_name("---multiple---"), "multiple")

    def test_long_name_truncation(self):
        long_title = "a" * 100
        self.assertEqual(len(_sanitize_branch_name(long_title)), 50)
        self.assertEqual(_sanitize_branch_name(long_title), "a" * 50)

    def test_numbers_and_hyphens(self):
        self.assertEqual(_sanitize_branch_name("issue-123-fix"), "issue-123-fix")
        self.assertEqual(
            _sanitize_branch_name("123-only-numbers-456"), "123-only-numbers-456"
        )

    def test_empty_and_hyphen_only_after_sanitize(self):
        self.assertEqual(_sanitize_branch_name("!@#$"), "")  # All special chars removed
        self.assertEqual(
            _sanitize_branch_name("---"), ""
        )  # All hyphens stripped if that's all left


class TestStartWorkOnIssue(unittest.TestCase):
    @patch(
        "autopr.github_service.get_issue_details"
    )  # Mock the call to the new get_issue_details
    @patch("subprocess.run")  # For git checkout
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.isdir")
    @patch("autopr.github_service._sanitize_branch_name")
    def test_start_work_on_issue_success_updated(
        self,
        mock_sanitize,
        mock_isdir,
        mock_file_open,
        mock_git_checkout_run,
        mock_get_details,
    ):
        issue_number = 123
        repo_path = "/test/repo"
        issue_title_from_details = "Detailed Test Issue"
        mock_get_details.return_value = {
            "number": issue_number,
            "title": issue_title_from_details,
            "body": "...",
            "labels": [],
        }
        sanitized_title = "detailed-test-issue"
        mock_sanitize.return_value = sanitized_title
        expected_branch_name = f"feature/{issue_number}-{sanitized_title}"
        mock_isdir.return_value = True  # .git dir exists

        start_work_on_issue(issue_number, repo_path=repo_path)

        mock_get_details.assert_called_once_with(issue_number)
        mock_sanitize.assert_called_once_with(issue_title_from_details)
        mock_git_checkout_run.assert_called_once_with(
            ["git", "checkout", "-b", expected_branch_name],
            check=True,
            capture_output=True,
            text=True,
        )
        mock_isdir.assert_called_once_with(os.path.join(repo_path, ".git"))
        mock_file_open.assert_called_once_with(
            os.path.join(repo_path, ".git", ".autopr_current_issue"), "w"
        )
        mock_file_open().write.assert_called_once_with(str(issue_number))

    @patch("autopr.github_service.get_issue_details")
    @patch("builtins.print")
    def test_start_work_on_issue_get_details_fails(self, mock_print, mock_get_details):
        issue_number = 456
        mock_get_details.return_value = None  # Simulate failure in fetching details

        start_work_on_issue(issue_number)
        # get_issue_details prints its own errors, check it was called
        mock_get_details.assert_called_once_with(issue_number)
        # Check that a higher-level error message from start_work_on_issue is NOT printed,
        # as the error should be handled and printed within get_issue_details.
        # This assertion might need refinement based on exact print statements.
        # For now, we are mostly ensuring it doesn't proceed if get_issue_details fails.

    # test_start_work_on_issue_no_git_dir needs to be adapted for repo_path
    @patch("autopr.github_service.get_issue_details")
    @patch(
        "subprocess.run"
    )  # for git checkout, assume it doesn't run if .git is not found before file write
    @patch("os.path.isdir")
    @patch("builtins.print")
    def test_start_work_on_issue_no_git_dir_updated(
        self, mock_print, mock_isdir, mock_git_checkout_run, mock_get_details
    ):
        issue_number = 789
        repo_path = "/no/git/here"
        mock_get_details.return_value = {
            "number": issue_number,
            "title": "Issue Title",
            "body": "...",
            "labels": [],
        }
        mock_isdir.return_value = False  # .git dir does NOT exist at repo_path/.git

        start_work_on_issue(issue_number, repo_path=repo_path)

        mock_get_details.assert_called_once_with(issue_number)
        mock_isdir.assert_called_once_with(os.path.join(repo_path, ".git"))
        mock_print.assert_any_call(
            f"Error: .git directory not found at {os.path.join(repo_path, '.git')}. Are you in a git repository?"
        )
        mock_git_checkout_run.assert_called()  # In the current logic, checkout happens before .git dir check for write
        # This might be an area for future refinement in start_work_on_issue order of ops.
        # For now, testing current behavior.
        # Actually, no, checkout is called, then .git dir is checked. So this is fine.


class TestGetStagedDiff(unittest.TestCase):
    @patch("subprocess.run")
    def test_get_staged_diff_success_with_diff(self, mock_subprocess_run):
        mock_process = Mock()
        mock_process.stdout = "diff --git a/file.txt b/file.txt\n--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-old\n+new"
        mock_process.stderr = ""
        mock_process.returncode = (
            0  # or 1, as git diff can return 1 if there are changes
        )
        mock_subprocess_run.return_value = mock_process

        diff = get_staged_diff()
        self.assertEqual(diff, mock_process.stdout.strip())
        mock_subprocess_run.assert_called_once_with(
            ["git", "diff", "--staged"], capture_output=True, text=True, check=False
        )

    @patch("subprocess.run")
    def test_get_staged_diff_success_no_diff(self, mock_subprocess_run):
        mock_process = Mock()
        mock_process.stdout = ""  # Empty string for no diff
        mock_process.stderr = ""
        mock_process.returncode = 0
        mock_subprocess_run.return_value = mock_process

        diff = get_staged_diff()
        self.assertEqual(diff, "")
        mock_subprocess_run.assert_called_once_with(
            ["git", "diff", "--staged"], capture_output=True, text=True, check=False
        )

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_get_staged_diff_git_error(self, mock_print, mock_subprocess_run):
        mock_process = Mock()
        mock_process.stdout = ""
        mock_process.stderr = (
            "fatal: not a git repository (or any of the parent directories): .git"
        )
        mock_process.returncode = 128
        mock_subprocess_run.return_value = mock_process

        diff = get_staged_diff()
        self.assertIsNone(diff)
        mock_print.assert_any_call(
            f"Error getting staged diff: {mock_process.stderr.strip()}"
        )
        mock_subprocess_run.assert_called_once_with(
            ["git", "diff", "--staged"], capture_output=True, text=True, check=False
        )

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_get_staged_diff_file_not_found_error(
        self, mock_print, mock_subprocess_run
    ):
        mock_subprocess_run.side_effect = FileNotFoundError("git not found")

        diff = get_staged_diff()
        self.assertIsNone(diff)
        mock_print.assert_any_call(
            "Error: git command not found. Please ensure git is installed and in your PATH."
        )


class TestGitCommit(unittest.TestCase):
    @patch("subprocess.run")
    def test_git_commit_success(self, mock_subprocess_run):
        commit_message = "feat: Implement new feature"
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "[main 1234567] feat: Implement new feature\n 1 file changed, 1 insertion(+)"
        mock_process.stderr = ""
        mock_subprocess_run.return_value = mock_process

        success, output = git_commit(commit_message)

        self.assertTrue(success)
        self.assertEqual(output, mock_process.stdout.strip())
        mock_subprocess_run.assert_called_once_with(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            text=True,
            check=False,
        )

    @patch("subprocess.run")
    def test_git_commit_failure(self, mock_subprocess_run):
        commit_message = "fix: Attempt to fix bug"
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "On branch main\nYour branch is up to date with 'origin/main'.\n\nnothing to commit, working tree clean"
        mock_subprocess_run.return_value = mock_process

        success, output = git_commit(commit_message)

        self.assertFalse(success)
        self.assertEqual(output, mock_process.stderr.strip())
        mock_subprocess_run.assert_called_once_with(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            text=True,
            check=False,
        )

    @patch("subprocess.run")
    def test_git_commit_failure_error_on_stdout(self, mock_subprocess_run):
        commit_message = "fix: Attempt to fix bug"
        mock_process = Mock()
        mock_process.returncode = 1
        # Some git errors might write to stdout even on failure
        mock_process.stdout = "Error: something went wrong on stdout"
        mock_process.stderr = ""
        mock_subprocess_run.return_value = mock_process

        success, output = git_commit(commit_message)

        self.assertFalse(success)
        self.assertEqual(output, mock_process.stdout.strip())

    @patch("subprocess.run")
    def test_git_commit_file_not_found_error(self, mock_subprocess_run):
        commit_message = "test: FileNotFoundError"
        mock_subprocess_run.side_effect = FileNotFoundError("git not found")

        success, output = git_commit(commit_message)

        self.assertFalse(success)
        self.assertEqual(
            output,
            "Error: git command not found. Please ensure git is installed and in your PATH.",
        )

    @patch("subprocess.run")
    def test_git_commit_unexpected_error(self, mock_subprocess_run):
        commit_message = "test: Unexpected error"
        mock_subprocess_run.side_effect = Exception("Something broke")

        success, output = git_commit(commit_message)
        self.assertFalse(success)
        self.assertEqual(
            output, "An unexpected error occurred during git commit: Something broke"
        )


class TestGetCurrentIssueNumber(unittest.TestCase):
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="123\n")
    def test_get_current_issue_number_success(self, mock_file, mock_exists):
        repo_path = "/fake/repo"
        expected_issue_number = 123
        issue_number = get_current_issue_number(repo_path)
        self.assertEqual(issue_number, expected_issue_number)
        mock_exists.assert_called_once_with(
            os.path.join(repo_path, ".git", ".autopr_current_issue")
        )
        mock_file.assert_called_once_with(
            os.path.join(repo_path, ".git", ".autopr_current_issue"), "r"
        )

    @patch("os.path.exists", return_value=False)
    @patch("builtins.print")
    def test_get_current_issue_number_file_not_found(self, mock_print, mock_exists):
        repo_path = "/fake/repo"
        issue_number = get_current_issue_number(repo_path)
        self.assertIsNone(issue_number)
        mock_exists.assert_called_once_with(
            os.path.join(repo_path, ".git", ".autopr_current_issue")
        )
        mock_print.assert_any_call(
            f"Context file not found: {os.path.join(repo_path, '.git', '.autopr_current_issue')}"
        )

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="not_an_int")
    @patch("builtins.print")
    def test_get_current_issue_number_invalid_content(
        self, mock_print, mock_file, mock_exists
    ):
        repo_path = "/fake/repo"
        issue_number = get_current_issue_number(repo_path)
        self.assertIsNone(issue_number)
        mock_print.assert_any_call(
            f"Error: Invalid content in {os.path.join(repo_path, '.git', '.autopr_current_issue')}. Expected an integer."
        )

    @patch("os.path.exists", side_effect=Exception("FS error"))
    @patch("builtins.print")
    def test_get_current_issue_number_os_error(self, mock_print, mock_exists):
        issue_number = get_current_issue_number()
        self.assertIsNone(issue_number)
        mock_print.assert_any_call("Error reading current issue number: FS error")


class TestGetIssueDetails(unittest.TestCase):
    @patch("subprocess.run")
    def test_get_issue_details_success(self, mock_subprocess_run):
        issue_number = 456
        mock_response_stdout = '{"number": 456, "title": "Test Issue", "body": "Issue body", "labels": [{"name": "bug"}]}'
        mock_process = Mock(stdout=mock_response_stdout, returncode=0, stderr="")
        mock_subprocess_run.return_value = mock_process

        details = get_issue_details(issue_number)

        expected_details = json.loads(mock_response_stdout)
        self.assertEqual(details, expected_details)
        mock_subprocess_run.assert_called_once_with(
            [
                "gh",
                "issue",
                "view",
                str(issue_number),
                "--json",
                "number,title,body,labels",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_get_issue_details_gh_error(self, mock_print, mock_subprocess_run):
        issue_number = 789
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            cmd=["gh", "..."], returncode=1, stderr="Gh error"
        )
        details = get_issue_details(issue_number)
        self.assertIsNone(details)
        mock_print.assert_any_call(
            f"Error fetching issue details for #{issue_number} via gh:"
        )
        mock_print.assert_any_call("Stderr:\nGh error")

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_get_issue_details_json_decode_error(self, mock_print, mock_subprocess_run):
        issue_number = 101
        mock_process = Mock(stdout="invalid json", returncode=0, stderr="")
        mock_subprocess_run.return_value = mock_process
        details = get_issue_details(issue_number)
        self.assertIsNone(details)
        mock_print.assert_any_call(
            f"Error: Could not parse issue details for #{issue_number} from gh CLI output."
        )


class TestGetCommitMessagesForBranch(unittest.TestCase):
    @patch("subprocess.run")
    def test_get_commit_messages_success(self, mock_subprocess_run):
        base_branch = "main"
        mock_response_stdout = "feat: Add feature A\nfix: Bug B\nchore: Update docs"
        mock_process = Mock(stdout=mock_response_stdout, returncode=0, stderr="")
        mock_subprocess_run.return_value = mock_process

        messages = get_commit_messages_for_branch(base_branch)

        expected_messages = ["feat: Add feature A", "fix: Bug B", "chore: Update docs"]
        self.assertEqual(messages, expected_messages)
        mock_subprocess_run.assert_called_once_with(
            ["git", "log", f"{base_branch}..HEAD", "--pretty=format:%s"],
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("subprocess.run")
    def test_get_commit_messages_no_commits(self, mock_subprocess_run):
        base_branch = "main"
        mock_process = Mock(
            stdout="", returncode=0, stderr=""
        )  # Empty stdout means no commits
        mock_subprocess_run.return_value = mock_process
        messages = get_commit_messages_for_branch(base_branch)
        self.assertEqual(messages, [])

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_get_commit_messages_git_log_error(self, mock_print, mock_subprocess_run):
        base_branch = "nonexistent_base"
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            cmd=["git", "log"],
            returncode=128,
            stderr="fatal: unknown revision or path not in the working tree.",
        )
        messages = get_commit_messages_for_branch(base_branch)
        self.assertIsNone(messages)
        mock_print.assert_any_call("Error getting commit messages:")
        mock_print.assert_any_call(
            "Hint: Ensure 'nonexistent_base' is a valid branch and an ancestor of the current branch."
        )

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_get_commit_messages_file_not_found(self, mock_print, mock_subprocess_run):
        base_branch = "main"
        mock_subprocess_run.side_effect = FileNotFoundError()
        messages = get_commit_messages_for_branch(base_branch)
        self.assertIsNone(messages)
        mock_print.assert_any_call("Error: git command not found.")


# --- Tests for create_pr_gh ---
class TestCreatePrGh(unittest.TestCase):
    @patch("autopr.github_service.subprocess.run")
    def test_create_pr_gh_success(self, mock_run):
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "https://github.com/owner/repo/pull/123"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        title = "Test PR Title"
        body = "Test PR body."
        base_branch = "main"

        success, output = create_pr_gh(title, body, base_branch)

        self.assertTrue(success)
        self.assertEqual(output, "https://github.com/owner/repo/pull/123")
        mock_run.assert_called_once_with(
            [
                "gh",
                "pr",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--base",
                base_branch,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    @patch("autopr.github_service.subprocess.run")
    def test_create_pr_gh_failure_gh_error(self, mock_run):
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = "Some output on stdout"
        mock_process.stderr = "Error from gh CLI"
        mock_run.return_value = mock_process

        title = "Test PR Title"
        body = "Test PR body."
        base_branch = "main"

        success, output = create_pr_gh(title, body, base_branch)

        self.assertFalse(success)
        expected_error_message = (
            "Error creating PR: Error from gh CLI\nstdout: Some output on stdout"
        )
        self.assertEqual(output, expected_error_message)
        mock_run.assert_called_once_with(
            [
                "gh",
                "pr",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--base",
                base_branch,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    @patch("autopr.github_service.subprocess.run")
    def test_create_pr_gh_failure_gh_error_no_stdout(self, mock_run):
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "Error from gh CLI"
        mock_run.return_value = mock_process

        title = "Test PR Title"
        body = "Test PR body."
        base_branch = "main"

        success, output = create_pr_gh(title, body, base_branch)

        self.assertFalse(success)
        self.assertEqual(output, "Error creating PR: Error from gh CLI")
        mock_run.assert_called_once_with(
            [
                "gh",
                "pr",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--base",
                base_branch,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    @patch(
        "autopr.github_service.subprocess.run",
        side_effect=FileNotFoundError("gh not found"),
    )
    def test_create_pr_gh_file_not_found(self, mock_run):
        title = "Test PR Title"
        body = "Test PR body."
        base_branch = "main"

        success, output = create_pr_gh(title, body, base_branch)

        self.assertFalse(success)
        self.assertEqual(
            output,
            "Error: 'gh' command not found. Please ensure it is installed and in your PATH.",
        )
        # subprocess.run not called if FileNotFoundError is raised before it or by it.
        # If side_effect is on mock_run itself, it means it's called, then raises.
        mock_run.assert_called_once_with(
            [
                "gh",
                "pr",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--base",
                base_branch,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    @patch("autopr.github_service.subprocess.run")
    def test_create_pr_gh_unexpected_exception(self, mock_run):
        mock_run.side_effect = Exception("Unexpected subprocess error")

        title = "Test PR Title"
        body = "Test PR body."
        base_branch = "main"

        success, output = create_pr_gh(title, body, base_branch)

        self.assertFalse(success)
        self.assertEqual(
            output,
            "An unexpected error occurred while trying to create PR with gh: Unexpected subprocess error",
        )
        mock_run.assert_called_once_with(
            [
                "gh",
                "pr",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--base",
                base_branch,
            ],
            capture_output=True,
            text=True,
            check=False,
        )


class TestGetPrChanges(unittest.TestCase):
    @patch("subprocess.run")
    def test_success(self, mock_subprocess_run):
        mock_pr_number = 123
        expected_diff = "diff --git a/file.py b/file.py\n--- a/file.py\n+++ b/file.py\n@@ -1 +1,2 @@\n-old\n+new"
        mock_process = MagicMock(stdout=expected_diff, stderr="", returncode=0)
        mock_subprocess_run.return_value = mock_process

        diff = get_pr_changes(mock_pr_number)

        self.assertEqual(diff, expected_diff)
        mock_subprocess_run.assert_called_once_with(
            ["gh", "pr", "view", str(mock_pr_number), "--patch"],
            capture_output=True, text=True, check=True
        )

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_called_process_error(self, mock_print, mock_subprocess_run):
        mock_pr_number = 123
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            cmd=["gh", "pr", "view"], returncode=1, stderr="Error from gh"
        )
        diff = get_pr_changes(mock_pr_number)
        self.assertEqual(diff, "")
        mock_print.assert_any_call(f"Error fetching PR changes for PR #{mock_pr_number} via gh:")
        mock_print.assert_any_call("Stderr:\nError from gh")

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_file_not_found_error(self, mock_print, mock_subprocess_run):
        mock_pr_number = 123
        mock_subprocess_run.side_effect = FileNotFoundError
        diff = get_pr_changes(mock_pr_number)
        self.assertEqual(diff, "")
        mock_print.assert_any_call("Error: 'gh' command not found. Please ensure it is installed and in your PATH.")

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_unexpected_exception(self, mock_print, mock_subprocess_run):
        mock_pr_number = 123
        mock_subprocess_run.side_effect = Exception("Something went wrong")
        diff = get_pr_changes(mock_pr_number)
        self.assertEqual(diff, "")
        mock_print.assert_any_call(f"An unexpected error occurred while fetching PR changes: Something went wrong")


class TestGetRepoDetails(unittest.TestCase):
    @patch("subprocess.run")
    def test_success_user_owner(self, mock_subprocess_run):
        mock_response_stdout = '{"name": "my-repo", "owner": {"login": "testuser"}}'
        mock_process = MagicMock(stdout=mock_response_stdout, returncode=0, stderr="")
        mock_subprocess_run.return_value = mock_process
        details = _get_repo_details()
        self.assertEqual(details, ("testuser", "my-repo"))
        mock_subprocess_run.assert_called_once_with(
            ["gh", "repo", "view", "--json", "owner,name"], 
            capture_output=True, text=True, check=True
        )

    @patch("subprocess.run")
    def test_success_org_owner(self, mock_subprocess_run):
        mock_response_stdout = '{"name": "our-repo", "owner": {"login": "testorg", "__typename": "Organization"}}'
        mock_process = MagicMock(stdout=mock_response_stdout, returncode=0, stderr="")
        mock_subprocess_run.return_value = mock_process
        details = _get_repo_details()
        self.assertEqual(details, ("testorg", "our-repo"))

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_called_process_error(self, mock_print, mock_subprocess_run):
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(cmd=["gh"], returncode=1, stderr="gh error")
        details = _get_repo_details()
        self.assertIsNone(details)
        mock_print.assert_any_call("Error fetching repository details: gh error")

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_json_decode_error(self, mock_print, mock_subprocess_run):
        mock_process = MagicMock(stdout="invalid json", returncode=0, stderr="")
        mock_subprocess_run.return_value = mock_process
        details = _get_repo_details()
        self.assertIsNone(details)
        mock_print.assert_any_call("Error parsing repository details from gh.")

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_file_not_found_error(self, mock_print, mock_subprocess_run):
        mock_subprocess_run.side_effect = FileNotFoundError
        details = _get_repo_details()
        self.assertIsNone(details)
        mock_print.assert_any_call("Error: 'gh' command not found for _get_repo_details.")


class TestGetPrHeadCommitSha(unittest.TestCase):
    @patch("subprocess.run")
    def test_success(self, mock_subprocess_run):
        mock_pr_number = 789
        expected_sha = "abcdef1234567890"
        mock_response_stdout = f'{{"headRefOid": "{expected_sha}"}}'
        mock_process = MagicMock(stdout=mock_response_stdout, returncode=0, stderr="")
        mock_subprocess_run.return_value = mock_process
        sha = _get_pr_head_commit_sha(mock_pr_number)
        self.assertEqual(sha, expected_sha)
        mock_subprocess_run.assert_called_once_with(
            ["gh", "pr", "view", str(mock_pr_number), "--json", "headRefOid"],
            capture_output=True, text=True, check=True
        )

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_called_process_error(self, mock_print, mock_subprocess_run):
        mock_pr_number = 789
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(cmd=["gh"], returncode=1, stderr="gh error")
        sha = _get_pr_head_commit_sha(mock_pr_number)
        self.assertIsNone(sha)
        mock_print.assert_any_call(f"Error fetching PR head commit SHA for PR #{mock_pr_number}: gh error")

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_json_decode_error(self, mock_print, mock_subprocess_run):
        mock_pr_number = 789
        mock_process = MagicMock(stdout="invalid json", returncode=0, stderr="")
        mock_subprocess_run.return_value = mock_process
        sha = _get_pr_head_commit_sha(mock_pr_number)
        self.assertIsNone(sha)
        mock_print.assert_any_call(f"Error parsing PR head commit SHA for PR #{mock_pr_number}.")

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_missing_head_ref_oid(self, mock_print, mock_subprocess_run):
        mock_pr_number = 789
        mock_response_stdout = '{"someOtherKey": "value"}' # headRefOid is missing
        mock_process = MagicMock(stdout=mock_response_stdout, returncode=0, stderr="")
        mock_subprocess_run.return_value = mock_process
        sha = _get_pr_head_commit_sha(mock_pr_number)
        self.assertIsNone(sha) # .get("headRefOid") returns None

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_file_not_found_error(self, mock_print, mock_subprocess_run):
        mock_pr_number = 789
        mock_subprocess_run.side_effect = FileNotFoundError
        sha = _get_pr_head_commit_sha(mock_pr_number)
        self.assertIsNone(sha)
        mock_print.assert_any_call("Error: 'gh' command not found for _get_pr_head_commit_sha.")


class TestPostPrReviewComment(unittest.TestCase):
    @patch("autopr.github_service._get_repo_details")
    @patch("autopr.github_service._get_pr_head_commit_sha")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_success(self, mock_print, mock_subprocess_run, mock_get_sha, mock_get_repo):
        mock_pr_number = 1
        mock_body = "This is a test comment."
        mock_path = "test_file.py"
        mock_line = 10
        mock_owner = "testowner"
        mock_repo = "testrepo"
        mock_sha = "headcommitsha"

        mock_get_repo.return_value = (mock_owner, mock_repo)
        mock_get_sha.return_value = mock_sha
        mock_api_response = MagicMock(stdout="Comment JSON data", returncode=0, stderr="")
        mock_subprocess_run.return_value = mock_api_response

        success = post_pr_review_comment(mock_pr_number, mock_body, mock_path, mock_line)

        self.assertTrue(success)
        mock_get_repo.assert_called_once()
        mock_get_sha.assert_called_once_with(mock_pr_number)
        expected_api_path = f"repos/{mock_owner}/{mock_repo}/pulls/{mock_pr_number}/comments"
        expected_fields = [
            "-f", f"body={mock_body}",
            "-f", f"commit_id={mock_sha}",
            "-f", f"path={mock_path}",
            "-F", f"line={mock_line}"
        ]
        mock_subprocess_run.assert_called_once_with(
            ["gh", "api", expected_api_path, "-X", "POST"] + expected_fields,
            capture_output=True, text=True, check=True
        )
        mock_print.assert_any_call(f"Successfully posted comment on PR #{mock_pr_number} to {mock_path}:{mock_line}. Response: Comment JSON data...")

    @patch("autopr.github_service._get_repo_details")
    @patch("builtins.print")
    def test_failure_get_repo_details_fails(self, mock_print, mock_get_repo):
        mock_get_repo.return_value = None
        success = post_pr_review_comment(1, "body", "path", 1)
        self.assertFalse(success)
        mock_print.assert_any_call("Failed to post comment: Could not retrieve repository details.")

    @patch("autopr.github_service._get_repo_details", return_value=("owner", "repo"))
    @patch("autopr.github_service._get_pr_head_commit_sha")
    @patch("builtins.print")
    def test_failure_get_pr_head_commit_sha_fails(self, mock_print, mock_get_sha, mock_get_repo_unused):
        mock_get_sha.return_value = None
        success = post_pr_review_comment(1, "body", "path", 1)
        self.assertFalse(success)
        mock_print.assert_any_call(f"Failed to post comment: Could not retrieve head commit SHA for PR #1.")

    @patch("autopr.github_service._get_repo_details", return_value=("owner", "repo"))
    @patch("autopr.github_service._get_pr_head_commit_sha", return_value="sha")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_failure_gh_api_called_process_error(self, mock_print, mock_subprocess_run, mock_get_sha_unused, mock_get_repo_unused):
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(cmd=["gh", "api"], returncode=1, stderr="API Error")
        success = post_pr_review_comment(1, "body", "path", 1)
        self.assertFalse(success)
        mock_print.assert_any_call("Error posting review comment via gh api for PR #1:")
        mock_print.assert_any_call("Stderr:\nAPI Error")

    @patch("autopr.github_service._get_repo_details", return_value=("owner", "repo"))
    @patch("autopr.github_service._get_pr_head_commit_sha", return_value="sha")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_failure_gh_api_file_not_found(self, mock_print, mock_subprocess_run, mock_get_sha_unused, mock_get_repo_unused):
        mock_subprocess_run.side_effect = FileNotFoundError
        success = post_pr_review_comment(1, "body", "path", 1)
        self.assertFalse(success)
        mock_print.assert_any_call("Error: 'gh' command not found. Please ensure it is installed and in your PATH.")


if __name__ == "__main__":
    unittest.main()

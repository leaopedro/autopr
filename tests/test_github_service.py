import unittest
import subprocess
from unittest.mock import patch, Mock

from autopr.github_service import list_issues, create_pr


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


class TestCreatePr(unittest.TestCase):
    @patch("builtins.print")
    def test_create_pr_prints_title(self, mock_print):
        test_title = "My Test PR Title"
        create_pr(test_title)
        mock_print.assert_called_once_with(
            f"Creating a new PR with title: {test_title}"
        )


if __name__ == "__main__":
    unittest.main()

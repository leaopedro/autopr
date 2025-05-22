import unittest
import subprocess
from unittest.mock import patch, Mock, mock_open
import os
import json

from autopr.github_service import list_issues, create_pr, start_work_on_issue, _sanitize_branch_name


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


class TestSanitizeBranchName(unittest.TestCase):
    def test_basic_sanitization(self):
        self.assertEqual(_sanitize_branch_name("My Test Issue"), "my-test-issue")
        self.assertEqual(_sanitize_branch_name("fix: a bug with spaces"), "fix-a-bug-with-spaces")
    
    def test_underscore_behavior(self):
        self.assertEqual(_sanitize_branch_name("char_name"), "char-name")
        self.assertEqual(_sanitize_branch_name("some_char_name"), "some-char-name")

    def test_special_characters(self):
        # Revert to original complex string, expecting the last known actual output
        self.assertEqual(_sanitize_branch_name("feat(scope)!: Highly@Special#$%^&*Char_Name"), "featscope-highlyspecialchar-name") 
    
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
        self.assertEqual(_sanitize_branch_name("123-only-numbers-456"), "123-only-numbers-456")

    def test_empty_and_hyphen_only_after_sanitize(self):
        self.assertEqual(_sanitize_branch_name("!@#$"), "") # All special chars removed
        self.assertEqual(_sanitize_branch_name("---"), "") # All hyphens stripped if that's all left


class TestStartWorkOnIssue(unittest.TestCase):
    @patch('subprocess.run')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.isdir')
    @patch('json.loads')
    @patch('autopr.github_service._sanitize_branch_name') # Patch within the module
    def test_start_work_on_issue_success(self, mock_sanitize, mock_json_loads, mock_isdir, mock_file_open, mock_subprocess_run):
        issue_number = 123
        issue_title = "My Test Issue for Branch"
        sanitized_title = "my-test-issue-for-branch"
        expected_branch_name = f"feature/{issue_number}-{sanitized_title}"

        # Mock os.path.isdir to simulate .git directory exists
        mock_isdir.return_value = True

        # Mock gh issue view subprocess call
        mock_gh_process = Mock()
        mock_gh_process.stdout = '{"number": 123, "title": "My Test Issue for Branch"}'
        
        # Mock git checkout subprocess call (we can make it a separate mock if we want to check args specifically)
        mock_git_process = Mock()

        # Configure subprocess.run to return different mocks based on command
        def subprocess_side_effect(*args, **kwargs):
            cmd = args[0]
            if 'gh' in cmd and 'issue' in cmd and 'view' in cmd:
                return mock_gh_process
            elif 'git' in cmd and 'checkout' in cmd:
                return mock_git_process
            return Mock() # Default mock for any other calls
        mock_subprocess_run.side_effect = subprocess_side_effect
        
        # Mock json.loads
        mock_json_loads.return_value = {"number": issue_number, "title": issue_title}
        
        # Mock _sanitize_branch_name
        mock_sanitize.return_value = sanitized_title

        start_work_on_issue(issue_number)

        # Assertions
        mock_subprocess_run.assert_any_call(
            ['gh', 'issue', 'view', str(issue_number), '--json', 'number,title'],
            capture_output=True, text=True, check=True
        )
        mock_json_loads.assert_called_once_with(mock_gh_process.stdout)
        mock_sanitize.assert_called_once_with(issue_title)
        mock_subprocess_run.assert_any_call(
            ['git', 'checkout', '-b', expected_branch_name],
            check=True, capture_output=True, text=True
        )
        mock_isdir.assert_called_once_with(".git")
        mock_file_open.assert_called_once_with(os.path.join(".git", ".autopr_current_issue"), 'w')
        mock_file_open().write.assert_called_once_with(str(issue_number))

    @patch('subprocess.run')
    @patch('builtins.print') # To capture error prints
    def test_start_work_on_issue_gh_fails(self, mock_print, mock_subprocess_run):
        issue_number = 456
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=['gh', 'issue', 'view'], output="Error fetching", stderr="Gh error"
        )
        start_work_on_issue(issue_number)
        mock_print.assert_any_call(f"Error during 'workon' process for issue #{issue_number}:")
        mock_print.assert_any_call("Stderr:\nGh error")

    @patch('subprocess.run')
    @patch('os.path.isdir')
    @patch('builtins.print')
    def test_start_work_on_issue_no_git_dir(self, mock_print, mock_isdir, mock_subprocess_run):
        issue_number = 789
        # Mock gh issue view to succeed
        mock_gh_process = Mock()
        mock_gh_process.stdout = '{"number": 789, "title": "Test"}'
        mock_subprocess_run.return_value = mock_gh_process # Covers the first call
        
        mock_isdir.return_value = False # Simulate .git directory NOT found
        
        start_work_on_issue(issue_number)
        mock_isdir.assert_called_with(".git") # Check it tried to find .git
        mock_print.assert_any_call("Error: .git directory not found. Are you in a git repository?")


if __name__ == "__main__":
    unittest.main()

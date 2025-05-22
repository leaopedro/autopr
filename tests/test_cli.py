import unittest
import sys
from unittest.mock import patch, MagicMock

from autopr.cli import main as autopr_main, handle_commit_command # Import main directly

class TestMainCLI(unittest.TestCase):

    @patch('autopr.cli.list_issues')
    @patch('autopr.cli.get_repo_from_git_config')
    def test_ls_command_calls_list_issues(self, mock_get_repo, mock_list_issues):
        with patch.object(sys, 'argv', ['cli.py', 'ls']): # Script name in argv[0] is conventional
            mock_get_repo.return_value = "owner/repo"
            autopr_main()
            mock_get_repo.assert_called_once()
            mock_list_issues.assert_called_once_with(show_all_issues=False)

    @patch('autopr.cli.list_issues')
    @patch('autopr.cli.get_repo_from_git_config')
    def test_ls_command_all_calls_list_issues_all(self, mock_get_repo, mock_list_issues):
        with patch.object(sys, 'argv', ['cli.py', 'ls', '-a']):
            mock_get_repo.return_value = "owner/repo"
            autopr_main()
            mock_get_repo.assert_called_once()
            mock_list_issues.assert_called_once_with(show_all_issues=True)

    @patch('autopr.cli.create_pr')
    @patch('autopr.cli.get_repo_from_git_config')
    def test_create_command_calls_create_pr(self, mock_get_repo, mock_create_pr):
        test_title = "Test PR"
        with patch.object(sys, 'argv', ['cli.py', 'create', '--title', test_title]):
            mock_get_repo.return_value = "owner/repo"
            autopr_main()
            mock_get_repo.assert_called_once()
            mock_create_pr.assert_called_once_with(test_title)

    @patch('builtins.print') 
    @patch('autopr.cli.get_repo_from_git_config')
    def test_repo_detection_failure(self, mock_get_repo, mock_print):
        with patch.object(sys, 'argv', ['cli.py', 'ls']):
            mock_get_repo.side_effect = FileNotFoundError("Mocked .git/config not found")
            autopr_main()
            mock_get_repo.assert_called_once()
            mock_print.assert_any_call("Error detecting repository: Mocked .git/config not found")

    @patch('autopr.cli.start_work_on_issue') 
    def test_workon_command_calls_start_work_on_issue(self, mock_start_work_on_issue):
        issue_number = 789
        with patch.object(sys, 'argv', ['cli.py', 'workon', str(issue_number)]):
            autopr_main()
            mock_start_work_on_issue.assert_called_once_with(issue_number)

    @patch('builtins.print') 
    def test_workon_command_invalid_issue_number(self, mock_print):
        with patch.object(sys, 'argv', ['cli.py', 'workon', 'not_a_number']):
            with self.assertRaises(SystemExit):
                autopr_main()

    @patch('autopr.cli.get_repo_from_git_config')
    @patch('autopr.cli.handle_commit_command')
    def test_commit_command_calls_handle_commit(self, mock_handle_commit, mock_get_repo):
        mock_get_repo.return_value = "owner/repo" # Simulate successful repo detection
        with patch.object(sys, 'argv', ['cli.py', 'commit']):
            autopr_main()
        mock_get_repo.assert_called_once() # Ensure repo detection is still called
        mock_handle_commit.assert_called_once()

    # Tests for handle_commit_command itself (which is now in cli.py)
    @patch('autopr.cli.get_staged_diff')
    @patch('builtins.print')
    def test_handle_commit_command_with_staged_changes(self, mock_print, mock_get_staged_diff):
        mock_get_staged_diff.return_value = "fake diff data"
        handle_commit_command()
        mock_get_staged_diff.assert_called_once()
        mock_print.assert_any_call("Handling commit command...")
        mock_print.assert_any_call("Staged Diffs:\n")
        mock_print.assert_any_call("fake diff data")
        mock_print.assert_any_call("\nMVP: AI suggestion would appear here. Please commit manually using git.")

    @patch('autopr.cli.get_staged_diff')
    @patch('builtins.print')
    def test_handle_commit_command_no_staged_changes(self, mock_print, mock_get_staged_diff):
        mock_get_staged_diff.return_value = None # Or empty string, depending on get_staged_diff behavior for no diff
        # Based on current get_staged_diff, it returns stripped stdout, so empty string if no diff and no error.
        # If get_staged_diff returns None on error, handle_commit_command should check for that specifically.
        # For now, let's assume get_staged_diff returns "" for no diff.
        mock_get_staged_diff.return_value = "" 

        handle_commit_command()
        mock_get_staged_diff.assert_called_once()
        mock_print.assert_any_call("Handling commit command...")
        mock_print.assert_any_call("No changes staged for commit.")

    @patch('autopr.cli.get_staged_diff')
    @patch('builtins.print')
    def test_handle_commit_command_get_diff_returns_none(self, mock_print, mock_get_staged_diff):
        # This tests the case where get_staged_diff itself had an error and returned None
        mock_get_staged_diff.return_value = None
        handle_commit_command()
        mock_get_staged_diff.assert_called_once()
        mock_print.assert_any_call("Handling commit command...")
        # Depending on desired behavior, it might print an error or specific message here.
        # Current handle_commit_command logic implicitly treats None from get_staged_diff as "no changes".
        # If get_staged_diff prints its own errors, then handle_commit_command doesn't need to repeat.
        # The current logic is: if not staged_diff (None or "" is falsy): print("No changes staged...")
        mock_print.assert_any_call("No changes staged for commit.")


# Placeholder for more CLI tests

if __name__ == '__main__':
    unittest.main()

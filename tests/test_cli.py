import unittest
import sys
from unittest.mock import patch, MagicMock

from autopr.cli import main as autopr_main # Import main directly

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


# Placeholder for more CLI tests

if __name__ == '__main__':
    unittest.main()

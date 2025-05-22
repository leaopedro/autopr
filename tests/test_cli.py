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
        mock_get_repo.return_value = "owner/repo" 
        with patch.object(sys, 'argv', ['cli.py', 'commit']):
            autopr_main()
        mock_get_repo.assert_called_once() 
        mock_handle_commit.assert_called_once()

    # Updated tests for handle_commit_command
    @patch('builtins.input', return_value='y')
    @patch('autopr.cli.git_commit') # Mock the new git_commit function in cli.py's scope
    @patch('autopr.cli.get_commit_message_suggestion')
    @patch('autopr.cli.get_staged_diff')
    @patch('builtins.print')
    def test_handle_commit_command_ai_suggest_confirm_yes_commit_success(self, mock_print, mock_get_staged_diff, mock_get_ai_suggestion, mock_git_commit, mock_input):
        mock_get_staged_diff.return_value = "fake diff data"
        ai_suggestion = "AI: feat: awesome new feature"
        mock_get_ai_suggestion.return_value = ai_suggestion
        mock_git_commit.return_value = (True, "Commit successful output")

        handle_commit_command()

        mock_get_staged_diff.assert_called_once()
        mock_get_ai_suggestion.assert_called_once_with("fake diff data")
        mock_input.assert_called_once_with("\nDo you want to commit with this message? (y/n): ")
        mock_git_commit.assert_called_once_with(ai_suggestion)
        mock_print.assert_any_call(f"\nSuggested commit message:\n{ai_suggestion}")
        mock_print.assert_any_call("Committing with the suggested message...")
        mock_print.assert_any_call("Commit successful!")
        mock_print.assert_any_call("Commit successful output")

    @patch('builtins.input', return_value='n')
    @patch('autopr.cli.git_commit')
    @patch('autopr.cli.get_commit_message_suggestion')
    @patch('autopr.cli.get_staged_diff')
    @patch('builtins.print')
    def test_handle_commit_command_ai_suggest_confirm_no(self, mock_print, mock_get_staged_diff, mock_get_ai_suggestion, mock_git_commit, mock_input):
        mock_get_staged_diff.return_value = "fake diff data"
        ai_suggestion = "AI: feat: another feature"
        mock_get_ai_suggestion.return_value = ai_suggestion

        handle_commit_command()

        mock_input.assert_called_once_with("\nDo you want to commit with this message? (y/n): ")
        mock_git_commit.assert_not_called()
        mock_print.assert_any_call("Commit aborted by user. Please commit manually using git.")

    @patch('builtins.input', return_value='y') # User says yes, but commit fails
    @patch('autopr.cli.git_commit')
    @patch('autopr.cli.get_commit_message_suggestion')
    @patch('autopr.cli.get_staged_diff')
    @patch('builtins.print')
    def test_handle_commit_command_ai_suggest_confirm_yes_commit_fail(self, mock_print, mock_get_staged_diff, mock_get_ai_suggestion, mock_git_commit, mock_input):
        mock_get_staged_diff.return_value = "fake diff data"
        ai_suggestion = "AI: fix: a bug"
        mock_get_ai_suggestion.return_value = ai_suggestion
        mock_git_commit.return_value = (False, "Commit failed output")

        handle_commit_command()
        
        mock_git_commit.assert_called_once_with(ai_suggestion)
        mock_print.assert_any_call("Commit failed.")
        mock_print.assert_any_call("Commit failed output")

    @patch('autopr.cli.get_commit_message_suggestion')
    @patch('autopr.cli.get_staged_diff')
    @patch('builtins.print')
    def test_handle_commit_command_ai_returns_error(self, mock_print, mock_get_staged_diff, mock_get_ai_suggestion):
        mock_get_staged_diff.return_value = "fake diff data"
        error_suggestion = "[Error communicating with OpenAI API]"
        mock_get_ai_suggestion.return_value = error_suggestion

        handle_commit_command()

        mock_print.assert_any_call(f"\nCould not get AI suggestion: {error_suggestion}")
        mock_print.assert_any_call("Please commit manually using git.")

    @patch('autopr.cli.get_staged_diff')
    @patch('builtins.print')
    def test_handle_commit_command_no_staged_changes(self, mock_print, mock_get_staged_diff):
        mock_get_staged_diff.return_value = "" 
        handle_commit_command()
        mock_get_staged_diff.assert_called_once()
        mock_print.assert_any_call("No changes staged for commit.")

    @patch('autopr.cli.get_staged_diff')
    @patch('builtins.print')
    # No need to patch get_commit_message_suggestion here
    def test_handle_commit_command_get_diff_returns_none(self, mock_print, mock_get_staged_diff):
        mock_get_staged_diff.return_value = None
        handle_commit_command()
        mock_get_staged_diff.assert_called_once()
        mock_print.assert_any_call("Handling commit command...")
        mock_print.assert_any_call("No changes staged for commit.")


# Placeholder for more CLI tests

if __name__ == '__main__':
    unittest.main()

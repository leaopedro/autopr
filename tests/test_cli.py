import unittest
import sys
from unittest.mock import patch, MagicMock

# Import the main script, assuming it can be run and its main() function can be called.
# This might need adjustment depending on how run_cli.py is structured.
import run_cli


class TestMainCLI(unittest.TestCase):

    @patch("sys.argv")
    @patch("run_cli.get_repo_from_git_config")
    @patch("run_cli.list_issues")
    def test_ls_command_calls_list_issues(
        self, mock_list_issues, mock_get_repo, mock_argv
    ):
        # Simulate command line arguments: python run_cli.py ls
        mock_argv.__getitem__.side_effect = lambda x: ["run_cli.py", "ls"][x]
        mock_argv.__len__.return_value = 2

        mock_get_repo.return_value = "owner/repo"  # Simulate successful repo detection

        run_cli.main()

        mock_get_repo.assert_called_once()
        mock_list_issues.assert_called_once_with(show_all_issues=False)

    @patch("sys.argv")
    @patch("run_cli.get_repo_from_git_config")
    @patch("run_cli.list_issues")
    def test_ls_command_all_calls_list_issues_all(
        self, mock_list_issues, mock_get_repo, mock_argv
    ):
        # Simulate: python run_cli.py ls -a
        mock_argv.__getitem__.side_effect = lambda x: ["run_cli.py", "ls", "-a"][x]
        mock_argv.__len__.return_value = 3

        mock_get_repo.return_value = "owner/repo"

        run_cli.main()

        mock_get_repo.assert_called_once()
        mock_list_issues.assert_called_once_with(show_all_issues=True)

    @patch("sys.argv")
    @patch("run_cli.get_repo_from_git_config")
    @patch("run_cli.create_pr")
    def test_create_command_calls_create_pr(
        self, mock_create_pr, mock_get_repo, mock_argv
    ):
        # Simulate: python run_cli.py create --title "Test PR"
        test_title = "Test PR"
        mock_argv.__getitem__.side_effect = lambda x: [
            "run_cli.py",
            "create",
            "--title",
            test_title,
        ][x]
        mock_argv.__len__.return_value = 4

        mock_get_repo.return_value = "owner/repo"

        run_cli.main()

        mock_get_repo.assert_called_once()
        mock_create_pr.assert_called_once_with(test_title)

    @patch("sys.argv")
    @patch("run_cli.get_repo_from_git_config")
    @patch("builtins.print")  # To capture print output for errors
    def test_repo_detection_failure(self, mock_print, mock_get_repo, mock_argv):
        # Simulate: python run_cli.py ls
        mock_argv.__getitem__.side_effect = lambda x: ["run_cli.py", "ls"][x]
        mock_argv.__len__.return_value = 2

        mock_get_repo.side_effect = FileNotFoundError("Mocked .git/config not found")

        run_cli.main()

        mock_get_repo.assert_called_once()
        mock_print.assert_any_call(
            "Error detecting repository: Mocked .git/config not found"
        )


# Placeholder for more CLI tests

if __name__ == "__main__":
    unittest.main()

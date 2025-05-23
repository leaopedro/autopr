import unittest
import sys
from unittest.mock import patch, MagicMock
from io import StringIO

from autopr.cli import (
    main as autopr_main,
    handle_commit_command,
    handle_review_command,
)  # Import main directly


class TestMainCLI(unittest.TestCase):

    @patch("autopr.cli.list_issues")
    @patch("autopr.cli.get_repo_from_git_config")
    def test_ls_command_calls_list_issues(self, mock_get_repo, mock_list_issues):
        with patch.object(
            sys, "argv", ["cli.py", "ls"]
        ):  # Script name in argv[0] is conventional
            mock_get_repo.return_value = "owner/repo"
            autopr_main()
            mock_get_repo.assert_called_once()
            mock_list_issues.assert_called_once_with(show_all_issues=False)

    @patch("autopr.cli.list_issues")
    @patch("autopr.cli.get_repo_from_git_config")
    def test_ls_command_all_calls_list_issues_all(
        self, mock_get_repo, mock_list_issues
    ):
        with patch.object(sys, "argv", ["cli.py", "ls", "-a"]):
            mock_get_repo.return_value = "owner/repo"
            autopr_main()
            mock_get_repo.assert_called_once()
            mock_list_issues.assert_called_once_with(show_all_issues=True)

    @patch("builtins.print")
    @patch("autopr.cli.get_repo_from_git_config")
    def test_repo_detection_failure(self, mock_get_repo, mock_print):
        with patch.object(sys, "argv", ["cli.py", "ls"]):
            mock_get_repo.side_effect = FileNotFoundError(
                "Mocked .git/config not found"
            )
            autopr_main()
            mock_get_repo.assert_called_once()
            mock_print.assert_any_call(
                "Error detecting repository: Mocked .git/config not found"
            )

    @patch("autopr.cli.start_work_on_issue")
    def test_workon_command_calls_start_work_on_issue(self, mock_start_work_on_issue):
        issue_number = 789
        with patch.object(sys, "argv", ["cli.py", "workon", str(issue_number)]):
            autopr_main()
            mock_start_work_on_issue.assert_called_once_with(
                issue_number, repo_path="."
            )

    @patch("builtins.print")
    def test_workon_command_invalid_issue_number(self, mock_print):
        with patch.object(sys, "argv", ["cli.py", "workon", "not_a_number"]):
            with self.assertRaises(SystemExit):
                autopr_main()

    @patch("autopr.cli.get_repo_from_git_config")
    @patch("autopr.cli.handle_commit_command")
    def test_commit_command_calls_handle_commit(
        self, mock_handle_commit, mock_get_repo
    ):
        mock_get_repo.return_value = "owner/repo"
        with patch.object(sys, "argv", ["cli.py", "commit"]):
            autopr_main()
        mock_get_repo.assert_called_once()
        mock_handle_commit.assert_called_once()

    # Updated tests for handle_commit_command
    @patch("builtins.input", return_value="y")
    @patch(
        "autopr.cli.git_commit"
    )  # Mock the new git_commit function in cli.py's scope
    @patch("autopr.cli.get_commit_message_suggestion")
    @patch("autopr.cli.get_staged_diff")
    @patch("builtins.print")
    def test_handle_commit_command_ai_suggest_confirm_yes_commit_success(
        self,
        mock_print,
        mock_get_staged_diff,
        mock_get_ai_suggestion,
        mock_git_commit,
        mock_input,
    ):
        mock_get_staged_diff.return_value = "fake diff data"
        ai_suggestion = "AI: feat: awesome new feature"
        mock_get_ai_suggestion.return_value = ai_suggestion
        mock_git_commit.return_value = (True, "Commit successful output")

        handle_commit_command()

        mock_get_staged_diff.assert_called_once()
        mock_get_ai_suggestion.assert_called_once_with("fake diff data")
        mock_input.assert_called_once_with(
            "\nDo you want to commit with this message? (y/n): "
        )
        mock_git_commit.assert_called_once_with(ai_suggestion)
        mock_print.assert_any_call(f"\nSuggested commit message:\n{ai_suggestion}")
        mock_print.assert_any_call("Committing with the suggested message...")
        mock_print.assert_any_call("Commit successful!")
        mock_print.assert_any_call("Commit successful output")

    @patch("builtins.input", return_value="n")
    @patch("autopr.cli.git_commit")
    @patch("autopr.cli.get_commit_message_suggestion")
    @patch("autopr.cli.get_staged_diff")
    @patch("builtins.print")
    def test_handle_commit_command_ai_suggest_confirm_no(
        self,
        mock_print,
        mock_get_staged_diff,
        mock_get_ai_suggestion,
        mock_git_commit,
        mock_input,
    ):
        mock_get_staged_diff.return_value = "fake diff data"
        ai_suggestion = "AI: feat: another feature"
        mock_get_ai_suggestion.return_value = ai_suggestion

        handle_commit_command()

        mock_input.assert_called_once_with(
            "\nDo you want to commit with this message? (y/n): "
        )
        mock_git_commit.assert_not_called()
        mock_print.assert_any_call(
            "Commit aborted by user. Please commit manually using git."
        )

    @patch("builtins.input", return_value="y")  # User says yes, but commit fails
    @patch("autopr.cli.git_commit")
    @patch("autopr.cli.get_commit_message_suggestion")
    @patch("autopr.cli.get_staged_diff")
    @patch("builtins.print")
    def test_handle_commit_command_ai_suggest_confirm_yes_commit_fail(
        self,
        mock_print,
        mock_get_staged_diff,
        mock_get_ai_suggestion,
        mock_git_commit,
        mock_input,
    ):
        mock_get_staged_diff.return_value = "fake diff data"
        ai_suggestion = "AI: fix: a bug"
        mock_get_ai_suggestion.return_value = ai_suggestion
        mock_git_commit.return_value = (False, "Commit failed output")

        handle_commit_command()

        mock_git_commit.assert_called_once_with(ai_suggestion)
        mock_print.assert_any_call("Commit failed.")
        mock_print.assert_any_call("Commit failed output")

    @patch("autopr.cli.get_commit_message_suggestion")
    @patch("autopr.cli.get_staged_diff")
    @patch("builtins.print")
    def test_handle_commit_command_ai_returns_error(
        self, mock_print, mock_get_staged_diff, mock_get_ai_suggestion
    ):
        mock_get_staged_diff.return_value = "fake diff data"
        error_suggestion = "[Error communicating with OpenAI API]"
        mock_get_ai_suggestion.return_value = error_suggestion

        handle_commit_command()

        mock_print.assert_any_call(f"\nCould not get AI suggestion: {error_suggestion}")
        mock_print.assert_any_call("Please commit manually using git.")

    @patch("autopr.cli.get_staged_diff")
    @patch("builtins.print")
    def test_handle_commit_command_no_staged_changes(
        self, mock_print, mock_get_staged_diff
    ):
        mock_get_staged_diff.return_value = ""
        handle_commit_command()
        mock_get_staged_diff.assert_called_once()
        mock_print.assert_any_call("No changes staged for commit.")

    @patch("autopr.cli.get_staged_diff")
    @patch("builtins.print")
    # No need to patch get_commit_message_suggestion here
    def test_handle_commit_command_get_diff_returns_none(
        self, mock_print, mock_get_staged_diff
    ):
        mock_get_staged_diff.return_value = None
        handle_commit_command()
        mock_get_staged_diff.assert_called_once()
        mock_print.assert_any_call("Handling commit command...")
        mock_print.assert_any_call("No changes staged for commit.")

    def test_review_command_parsing(self):
        with patch.object(sys, "argv", ["autopr", "review", "123"]):
            with patch("autopr.cli.handle_review_command") as mock_handler:
                autopr_main()
                mock_handler.assert_called_once_with(123)

    def test_review_command_without_repo(self):
        with patch.object(sys, "argv", ["autopr", "review", "123"]):
            with patch(
                "autopr.cli.get_repo_from_git_config", side_effect=Exception("No repo")
            ):
                with patch("autopr.cli.handle_review_command") as mock_handler:
                    autopr_main()
                    mock_handler.assert_not_called()


class TestHandleReviewCommand(unittest.TestCase):
    @patch("autopr.cli.get_pr_changes")
    @patch("autopr.cli.get_pr_review_suggestions")
    @patch("autopr.cli.post_pr_review_comment")
    def test_handle_review_command_success(
        self, mock_post, mock_suggestions, mock_changes
    ):
        # Mock PR changes
        mock_changes.return_value = (
            "diff --git a/file.txt b/file.txt\n@@ -1,1 +1,1 @@\n-old\n+new"
        )

        # Mock review suggestions
        mock_suggestions.return_value = [
            {
                "path": "file.txt",
                "line": 10,
                "suggestion": "Consider adding a comment here",
            },
            {
                "path": "file.txt",
                "line": 20,
                "suggestion": "This could be simplified",
            },
        ]

        # Mock successful comment posting
        mock_post.return_value = True

        # Capture stdout
        with patch("sys.stdout", new=StringIO()) as fake_out:
            handle_review_command(123)

            output = fake_out.getvalue()
            self.assertIn("Fetching changes for PR #123...", output)
            self.assertIn(
                "Analyzing changes and generating review suggestions...", output
            )
            self.assertIn("Generated 2 suggestions for review.", output)
            self.assertIn("Posted comment on file.txt:10", output)
            self.assertIn("Posted comment on file.txt:20", output)
            self.assertIn(
                "Review complete. Successfully posted 2 out of 2 comments.", output
            )

        # Verify function calls
        mock_changes.assert_called_once_with(123)
        mock_suggestions.assert_called_once_with(
            "diff --git a/file.txt b/file.txt\n@@ -1,1 +1,1 @@\n-old\n+new"
        )
        self.assertEqual(mock_post.call_count, 2)

    @patch("autopr.cli.get_pr_changes")
    def test_handle_review_command_no_changes(self, mock_changes):
        # Mock no PR changes
        mock_changes.return_value = None

        # Capture stdout
        with patch("sys.stdout", new=StringIO()) as fake_out:
            handle_review_command(123)

            output = fake_out.getvalue()
            self.assertIn("Fetching changes for PR #123...", output)
            self.assertIn(
                "Could not fetch PR changes. Please check the PR number and try again.",
                output,
            )

    @patch("autopr.cli.get_pr_changes")
    @patch("autopr.cli.get_pr_review_suggestions")
    def test_handle_review_command_no_suggestions(self, mock_suggestions, mock_changes):
        # Mock PR changes
        mock_changes.return_value = (
            "diff --git a/file.txt b/file.txt\n@@ -1,1 +1,1 @@\n-old\n+new"
        )

        # Mock no suggestions
        mock_suggestions.return_value = []

        # Capture stdout
        with patch("sys.stdout", new=StringIO()) as fake_out:
            handle_review_command(123)

            output = fake_out.getvalue()
            self.assertIn("Fetching changes for PR #123...", output)
            self.assertIn(
                "Analyzing changes and generating review suggestions...", output
            )
            self.assertIn(
                "No suggestions were generated. The changes might be too complex or there might be an error.",
                output,
            )

    @patch("autopr.cli.get_pr_changes")
    @patch("autopr.cli.get_pr_review_suggestions")
    @patch("autopr.cli.post_pr_review_comment")
    def test_handle_review_command_partial_success(
        self, mock_post, mock_suggestions, mock_changes
    ):
        # Mock PR changes
        mock_changes.return_value = (
            "diff --git a/file.txt b/file.txt\n@@ -1,1 +1,1 @@\n-old\n+new"
        )

        # Mock review suggestions
        mock_suggestions.return_value = [
            {
                "path": "file.txt",
                "line": 10,
                "suggestion": "Consider adding a comment here",
            },
            {
                "path": "file.txt",
                "line": 20,
                "suggestion": "This could be simplified",
            },
        ]

        # Mock one successful and one failed comment
        mock_post.side_effect = [True, False]

        # Capture stdout
        with patch("sys.stdout", new=StringIO()) as fake_out:
            handle_review_command(123)

            output = fake_out.getvalue()
            self.assertIn("Fetching changes for PR #123...", output)
            self.assertIn(
                "Analyzing changes and generating review suggestions...", output
            )
            self.assertIn("Generated 2 suggestions for review.", output)
            self.assertIn("Posted comment on file.txt:10", output)
            self.assertIn("Failed to post comment on file.txt:20", output)
            self.assertIn(
                "Review complete. Successfully posted 1 out of 2 comments.", output
            )

    @patch("autopr.cli.get_pr_changes")
    @patch("autopr.cli.get_pr_review_suggestions")
    @patch("autopr.cli.post_pr_review_comment")
    def test_handle_review_command_invalid_suggestion(
        self, mock_post, mock_suggestions, mock_changes
    ):
        # Mock PR changes
        mock_changes.return_value = (
            "diff --git a/file.txt b/file.txt\n@@ -1,1 +1,1 @@\n-old\n+new"
        )

        # Mock invalid suggestion format
        mock_suggestions.return_value = [
            {
                "path": "file.txt",
                # Missing line number
                "suggestion": "Consider adding a comment here",
            },
        ]

        # Capture stdout
        with patch("sys.stdout", new=StringIO()) as fake_out:
            handle_review_command(123)

            output = fake_out.getvalue()
            self.assertIn("Fetching changes for PR #123...", output)
            self.assertIn(
                "Analyzing changes and generating review suggestions...", output
            )
            self.assertIn("Generated 1 suggestions for review.", output)
            self.assertIn("Error in suggestion format: missing 'line'", output)
            self.assertIn(
                "Review complete. Successfully posted 0 out of 1 comments.", output
            )


# Placeholder for more CLI tests

if __name__ == "__main__":
    unittest.main()

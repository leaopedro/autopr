import unittest
from unittest.mock import patch, MagicMock, call
import argparse
import sys
from io import StringIO

from autopr.cli import (
    main as autopr_main,
    handle_commit_command,
    handle_review_command,
    handle_pr_create_command,
)

class TestMainCLI(unittest.TestCase):

    @patch("autopr.cli.list_issues")
    @patch("autopr.cli.get_repo_from_git_config")
    def test_ls_command_calls_list_issues(self, mock_get_repo, mock_list_issues):
        with patch.object(sys, "argv", ["autopr_cli", "ls"]):
            mock_get_repo.return_value = "owner/repo"
            autopr_main()
            mock_get_repo.assert_called_once()
            mock_list_issues.assert_called_once_with(show_all_issues=False)

    @patch("autopr.cli.list_issues")
    @patch("autopr.cli.get_repo_from_git_config")
    def test_ls_command_all_calls_list_issues_all(
        self, mock_get_repo, mock_list_issues
    ):
        with patch.object(sys, "argv", ["autopr_cli", "ls", "-a"]):
            mock_get_repo.return_value = "owner/repo"
            autopr_main()
            mock_get_repo.assert_called_once()
            mock_list_issues.assert_called_once_with(show_all_issues=True)

    @patch("builtins.print")
    @patch("autopr.cli.get_repo_from_git_config")
    def test_repo_detection_failure(self, mock_get_repo, mock_print):
        with patch.object(sys, "argv", ["autopr_cli", "ls"]):
            mock_get_repo.side_effect = FileNotFoundError(
                "Mocked .git/config not found"
            )
            autopr_main()
            mock_get_repo.assert_called_once()
            mock_print.assert_any_call(
                "Error detecting repository: Mocked .git/config not found"
            )

    @patch("autopr.cli.start_work_on_issue")
    @patch("autopr.cli.get_repo_from_git_config")
    def test_workon_command_calls_start_work_on_issue_updated(
        self, mock_get_repo, mock_start_work_on_issue
    ):
        issue_number = 789
        mock_get_repo.return_value = "owner/repo"
        with patch.object(sys, "argv", ["autopr_cli", "workon", str(issue_number)]):
            autopr_main()
        mock_start_work_on_issue.assert_called_once_with(issue_number, repo_path=".")

    @patch("builtins.print")
    def test_workon_command_invalid_issue_number(self, mock_print):
        with patch.object(sys, "argv", ["autopr_cli", "workon", "not_a_number"]):
            with self.assertRaises(SystemExit):
                autopr_main()

    @patch("autopr.cli.get_repo_from_git_config")
    @patch("autopr.cli.handle_commit_command")
    def test_commit_command_calls_handle_commit(
        self, mock_handle_commit, mock_get_repo
    ):
        mock_get_repo.return_value = "owner/repo"
        with patch.object(sys, "argv", ["autopr_cli", "commit"]):
            autopr_main()
        mock_get_repo.assert_called_once()
        mock_handle_commit.assert_called_once_with()

    @patch("builtins.input", return_value="y")
    @patch("autopr.cli.git_commit")
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

    @patch("builtins.input", return_value="y")
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
    def test_handle_commit_command_get_diff_returns_none(
        self, mock_print, mock_get_staged_diff
    ):
        mock_get_staged_diff.return_value = None
        handle_commit_command()
        mock_get_staged_diff.assert_called_once()
        mock_print.assert_any_call("No changes staged for commit.")

    @patch("autopr.cli.get_repo_from_git_config")
    @patch("autopr.cli.handle_review_command")
    def test_review_command_calls_handle_review(
        self, mock_handle_review, mock_get_repo
    ):
        mock_get_repo.return_value = "owner/repo"
        with patch.object(sys, "argv", ["autopr_cli", "review", "123"]):
            autopr_main()
        mock_get_repo.assert_called_once()
        mock_handle_review.assert_called_once_with(123)

    @patch("autopr.cli.get_repo_from_git_config")
    @patch("autopr.cli.handle_pr_create_command")
    def test_pr_command_calls_handle_pr_create(
        self, mock_handle_pr_create, mock_get_repo
    ):
        mock_get_repo.return_value = "owner/repo"
        with patch.object(sys, "argv", ["autopr_cli", "pr"]):
            autopr_main()
        mock_get_repo.assert_called_once()
        mock_handle_pr_create.assert_called_once_with("main", ".")

    @patch("autopr.cli.get_repo_from_git_config")
    @patch("autopr.cli.handle_pr_create_command")
    def test_pr_command_with_base_branch(
        self, mock_handle_pr_create, mock_get_repo
    ):
        mock_get_repo.return_value = "owner/repo"
        with patch.object(sys, "argv", ["autopr_cli", "pr", "--base", "develop"]):
            autopr_main()
        mock_get_repo.assert_called_once()
        mock_handle_pr_create.assert_called_once_with("develop", ".")


class TestHandleReviewCommand(unittest.TestCase):
    @patch("autopr.cli.get_pr_changes")
    @patch("autopr.cli.get_pr_review_suggestions")
    @patch("autopr.cli.post_pr_review_comment")
    @patch("builtins.print")
    def test_handle_review_command_success(
        self, mock_print, mock_post_comment, mock_get_suggestions, mock_get_changes
    ):
        # Mock PR changes
        mock_get_changes.return_value = "fake diff"
        
        # Mock review suggestions
        mock_get_suggestions.return_value = [
            {
                "path": "file1.txt",
                "line": 10,
                "suggestion": "Consider adding a comment here",
            },
            {
                "path": "file2.txt",
                "line": 20,
                "suggestion": "This could be simplified",
            },
        ]
        
        # Mock posting comments
        mock_post_comment.side_effect = [True, False]  # First succeeds, second fails
        
        # Test the function
        handle_review_command(123)
        
        # Verify the calls
        mock_get_changes.assert_called_once_with(123)
        mock_get_suggestions.assert_called_once_with("fake diff")
        self.assertEqual(mock_post_comment.call_count, 2)
        
        # Verify the output
        mock_print.assert_any_call("Fetching changes for PR #123...")
        mock_print.assert_any_call("\nAnalyzing changes and generating review suggestions...")
        mock_print.assert_any_call("\nGenerated 2 suggestions for review.")
        mock_print.assert_any_call("\nPosting review comments...")
        mock_print.assert_any_call("Posted comment on file1.txt:10")
        mock_print.assert_any_call("Failed to post comment on file2.txt:20")
        mock_print.assert_any_call("\nReview complete. Successfully posted 1 out of 2 comments.")

    @patch("autopr.cli.get_pr_changes")
    @patch("builtins.print")
    def test_handle_review_command_no_changes(
        self, mock_print, mock_get_changes
    ):
        mock_get_changes.return_value = ""
        
        handle_review_command(123)
        
        mock_get_changes.assert_called_once_with(123)
        mock_print.assert_any_call("Could not fetch PR changes. Please check the PR number and try again.")

    @patch("autopr.cli.get_pr_changes")
    @patch("autopr.cli.get_pr_review_suggestions")
    @patch("builtins.print")
    def test_handle_review_command_no_suggestions(
        self, mock_print, mock_get_suggestions, mock_get_changes
    ):
        mock_get_changes.return_value = "fake diff"
        mock_get_suggestions.return_value = []
        
        handle_review_command(123)
        
        mock_get_changes.assert_called_once_with(123)
        mock_get_suggestions.assert_called_once_with("fake diff")
        mock_print.assert_any_call(
            "No suggestions were generated. The changes might be too complex or there might be an error."
        )


class TestHandlePrCreateCommand(unittest.TestCase):
    @patch("autopr.cli.get_commit_messages_for_branch")
    @patch("autopr.cli.get_pr_description_suggestion")
    @patch("autopr.cli.create_pr_gh")
    @patch("builtins.input", return_value="y")
    @patch("builtins.print")
    def test_handle_pr_create_command_success(
        self,
        mock_print,
        mock_input,
        mock_create_pr,
        mock_get_description,
        mock_get_commits,
    ):
        # Mock commit messages
        mock_get_commits.return_value = ["feat: add feature", "fix: fix bug"]
        
        # Mock PR description
        mock_get_description.return_value = (
            "feat: Add new feature",
            "This PR adds a new feature and fixes a bug.",
        )
        
        # Mock PR creation
        mock_create_pr.return_value = (True, "PR #123 created successfully")
        
        # Test the function
        handle_pr_create_command("main")
        
        # Verify the calls
        mock_get_commits.assert_called_once_with("main")
        mock_get_description.assert_called_once_with(["feat: add feature", "fix: fix bug"])
        mock_create_pr.assert_called_once_with(
            "feat: Add new feature",
            "This PR adds a new feature and fixes a bug.",
            "main",
        )
        
        # Verify the output
        mock_print.assert_any_call("Initiating PR creation process against base branch: main")
        mock_print.assert_any_call("Retrieved 2 commit message(s).")
        mock_print.assert_any_call("\nAttempting to generate PR title and body using AI...")
        mock_print.assert_any_call("\n--- Suggested PR Title ---")
        mock_print.assert_any_call("feat: Add new feature")
        mock_print.assert_any_call("\n--- Suggested PR Body ---")
        mock_print.assert_any_call("This PR adds a new feature and fixes a bug.")
        mock_print.assert_any_call("PR created successfully!")
        mock_print.assert_any_call("PR #123 created successfully")

    @patch("autopr.cli.get_commit_messages_for_branch")
    @patch("builtins.print")
    def test_handle_pr_create_command_no_commits(
        self, mock_print, mock_get_commits
    ):
        mock_get_commits.return_value = []
        
        handle_pr_create_command("main")
        
        mock_get_commits.assert_called_once_with("main")
        mock_print.assert_any_call(
            "No new commit messages found on this branch compared to base. Cannot generate PR description."
        )

    @patch("autopr.cli.get_commit_messages_for_branch")
    @patch("builtins.print")
    def test_handle_pr_create_command_error_getting_commits(
        self, mock_print, mock_get_commits
    ):
        mock_get_commits.return_value = None
        
        handle_pr_create_command("main")
        
        mock_get_commits.assert_called_once_with("main")
        mock_print.assert_any_call(
            "Error: Could not retrieve commit messages for the current branch against base 'main'."
        )

    @patch("autopr.cli.get_commit_messages_for_branch")
    @patch("autopr.cli.get_pr_description_suggestion")
    @patch("builtins.input", return_value="n")
    @patch("builtins.print")
    def test_handle_pr_create_command_user_rejects(
        self,
        mock_print,
        mock_input,
        mock_get_description,
        mock_get_commits,
    ):
        mock_get_commits.return_value = ["feat: add feature"]
        mock_get_description.return_value = (
            "feat: Add new feature",
            "This PR adds a new feature.",
        )
        
        handle_pr_create_command("main")
        
        mock_print.assert_any_call("PR creation aborted by user.")

    @patch("autopr.cli.get_commit_messages_for_branch")
    @patch("autopr.cli.get_pr_description_suggestion")
    @patch("autopr.cli.create_pr_gh")
    @patch("builtins.input", return_value="y")
    @patch("builtins.print")
    def test_handle_pr_create_command_pr_creation_fails(
        self,
        mock_print,
        mock_input,
        mock_create_pr,
        mock_get_description,
        mock_get_commits,
    ):
        mock_get_commits.return_value = ["feat: add feature"]
        mock_get_description.return_value = (
            "feat: Add new feature",
            "This PR adds a new feature.",
        )
        mock_create_pr.return_value = (False, "Failed to create PR")
        
        handle_pr_create_command("main")
        
        mock_print.assert_any_call("Failed to create PR.")
        mock_print.assert_any_call("Failed to create PR")


if __name__ == "__main__":
    unittest.main()

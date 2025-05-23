import unittest
from unittest.mock import patch, MagicMock, call
import argparse
import sys

from autopr.cli import (
    main as autopr_main,
    handle_commit_command,
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
        mock_print.assert_any_call("Handling commit command...")
        mock_print.assert_any_call("No changes staged for commit.")

    @patch("autopr.cli.get_staged_diff")
    @patch("autopr.cli.get_commit_message_suggestion")
    @patch("builtins.print")
    def test_handle_commit_command_diff_exceeds_hard_limit(
        self, mock_print, mock_get_ai_suggestion, mock_get_staged_diff
    ):
        large_diff = "a" * 450001
        mock_get_staged_diff.return_value = large_diff
        handle_commit_command()
        mock_get_staged_diff.assert_called_once()
        mock_print.assert_any_call(
            f"Error: Diff is too large ({len(large_diff)} characters). Maximum allowed is 450,000 characters."
        )
        mock_print.assert_any_call(
            "Please break down your changes into smaller commits."
        )
        mock_get_ai_suggestion.assert_not_called()  # AI should not be called

    @patch("autopr.cli.get_staged_diff")
    @patch("autopr.cli.get_commit_message_suggestion")
    @patch("builtins.input", return_value="y")  # Assume user confirms if AI is called
    @patch(
        "autopr.cli.git_commit"
    )  # Mock commit as it won't be reached if AI not called
    @patch("builtins.print")
    def test_handle_commit_command_diff_exceeds_warning_limit(
        self,
        mock_print,
        mock_git_commit,
        mock_input,
        mock_get_ai_suggestion,
        mock_get_staged_diff,
    ):
        warn_diff = "b" * 400001
        mock_get_staged_diff.return_value = warn_diff
        # Mock AI suggestion to ensure the flow continues past the warning
        ai_suggestion = "AI: feat: processed large diff"
        mock_get_ai_suggestion.return_value = ai_suggestion
        mock_git_commit.return_value = (True, "Committed large diff")

        handle_commit_command()

        mock_get_staged_diff.assert_called_once()
        mock_print.assert_any_call(
            f"Warning: Diff is very large ({len(warn_diff)} characters). AI suggestion quality may be affected."
        )
        mock_print.assert_any_call(
            "Consider breaking down your changes into smaller commits for better results."
        )
        mock_get_ai_suggestion.assert_called_once_with(warn_diff)  # AI should be called
        mock_input.assert_called_once_with(
            "\nDo you want to commit with this message? (y/n): "
        )
        mock_git_commit.assert_called_once_with(ai_suggestion)

    @patch("autopr.cli.handle_pr_create_command")
    @patch("autopr.cli.get_repo_from_git_config")
    def test_pr_command_uses_default_base(self, mock_get_repo, mock_handle_pr_create):
        mock_get_repo.return_value = "owner/repo"
        with patch.object(sys, "argv", ["autopr_cli", "pr"]):
            autopr_main()
        mock_get_repo.assert_called_once()
        mock_handle_pr_create.assert_called_once_with(base_branch="main", repo_path=".")

    @patch("autopr.cli.handle_pr_create_command")
    @patch("autopr.cli.get_repo_from_git_config")
    def test_pr_command_respects_explicit_base(
        self, mock_get_repo, mock_handle_pr_create
    ):
        explicit_base = "develop"
        mock_get_repo.return_value = "owner/repo"
        with patch.object(sys, "argv", ["autopr_cli", "pr", "--base", explicit_base]):
            autopr_main()
        mock_get_repo.assert_called_once()
        mock_handle_pr_create.assert_called_once_with(
            base_branch=explicit_base, repo_path="."
        )


class TestHandlePrCreateCommand(unittest.TestCase):
    @patch("autopr.cli.get_pr_description_suggestion")
    @patch("autopr.cli.get_commit_messages_for_branch")
    @patch("builtins.input")
    @patch("autopr.cli.create_pr_gh")
    @patch("builtins.print")
    def test_handle_pr_create_success_user_confirms(
        self,
        mock_print,
        mock_create_pr_gh,
        mock_input,
        mock_get_commits,
        mock_get_pr_desc,
    ):
        repo_path = "/fake/path"
        base_branch = "develop"
        commit_list = ["feat: did a thing", "fix: another thing"]
        ai_title, ai_body = "AI PR Title", "AI PR Body which is awesome"

        mock_get_commits.return_value = commit_list
        mock_get_pr_desc.return_value = (ai_title, ai_body)
        mock_input.return_value = "y"
        mock_create_pr_gh.return_value = (True, "PR created: URL")

        handle_pr_create_command(base_branch=base_branch, repo_path=repo_path)

        mock_get_commits.assert_called_once_with(base_branch)
        mock_get_pr_desc.assert_called_once_with(commit_list)
        mock_input.assert_called_once_with("Do you want to create this PR? (y/n): ")
        mock_create_pr_gh.assert_called_once_with(ai_title, ai_body, base_branch)

        mock_print.assert_any_call(
            f"Initiating PR creation process against base branch: {base_branch}"
        )
        mock_print.assert_any_call(f"Retrieved {len(commit_list)} commit message(s).")
        mock_print.assert_any_call(
            "\nAttempting to generate PR title and body using AI..."
        )
        mock_print.assert_any_call("\n--- Suggested PR Title ---")
        mock_print.assert_any_call(ai_title)
        mock_print.assert_any_call("\n--- Suggested PR Body ---")
        mock_print.assert_any_call(ai_body)
        mock_print.assert_any_call("Attempting to create PR...")
        mock_print.assert_any_call("PR created successfully!")
        mock_print.assert_any_call("PR created: URL")

    @patch("autopr.cli.get_pr_description_suggestion")
    @patch("autopr.cli.get_commit_messages_for_branch")
    @patch("builtins.input")
    @patch("autopr.cli.create_pr_gh")
    @patch("builtins.print")
    def test_handle_pr_create_success_user_declines(
        self,
        mock_print,
        mock_create_pr_gh,
        mock_input,
        mock_get_commits,
        mock_get_pr_desc,
    ):
        repo_path = "/fake/path"
        base_branch = "develop"
        commit_list = ["feat: did a thing"]
        ai_title, ai_body = "AI PR Title", "AI PR Body"

        mock_get_commits.return_value = commit_list
        mock_get_pr_desc.return_value = (ai_title, ai_body)
        mock_input.return_value = "n"

        handle_pr_create_command(base_branch=base_branch, repo_path=repo_path)

        mock_get_commits.assert_called_once_with(base_branch)
        mock_get_pr_desc.assert_called_once_with(commit_list)
        mock_input.assert_called_once_with("Do you want to create this PR? (y/n): ")
        mock_create_pr_gh.assert_not_called()
        mock_print.assert_any_call("PR creation aborted by user.")

    @patch("autopr.cli.get_commit_messages_for_branch", return_value=None)
    @patch("builtins.print")
    def test_handle_pr_create_no_commits_error(self, mock_print, mock_get_commits):
        handle_pr_create_command(base_branch="main", repo_path="/path")
        mock_print.assert_any_call(
            "Error: Could not retrieve commit messages for the current branch against base 'main'."
        )
        mock_get_commits.assert_called_once_with("main")

    @patch("autopr.cli.get_commit_messages_for_branch", return_value=[])
    @patch("builtins.print")
    def test_handle_pr_create_no_commits_empty(self, mock_print, mock_get_commits):
        handle_pr_create_command(base_branch="main", repo_path="/path")
        mock_print.assert_any_call(
            "No new commit messages found on this branch compared to base. Cannot generate PR description."
        )
        mock_get_commits.assert_called_once_with("main")

    @patch("autopr.cli.get_commit_messages_for_branch")
    @patch("autopr.cli.get_pr_description_suggestion")
    @patch("builtins.input")
    @patch("autopr.cli.create_pr_gh")
    @patch("builtins.print")
    def test_handle_pr_create_command_pr_creation_fails(
        self,
        mock_print,
        mock_create_pr_gh,
        mock_input,
        mock_get_pr_description,
        mock_get_commits,
    ):
        mock_get_commits.return_value = ["feat: new feature"]
        mock_get_pr_description.return_value = ("AI PR Title", "AI PR Body")
        mock_input.return_value = "y"
        mock_create_pr_gh.return_value = (False, "Error from gh")

        handle_pr_create_command(base_branch="main", repo_path=".")

        mock_get_commits.assert_called_once_with("main")
        mock_get_pr_description.assert_called_once_with(["feat: new feature"])
        mock_create_pr_gh.assert_called_once_with("AI PR Title", "AI PR Body", "main")
        mock_print.assert_any_call("Failed to create PR.")
        mock_print.assert_any_call("Error from gh")

    @patch("autopr.cli.get_commit_messages_for_branch")
    @patch("autopr.cli.get_pr_description_suggestion")
    @patch("builtins.input")
    @patch("autopr.cli.create_pr_gh")
    @patch("builtins.print")
    def test_handle_pr_create_command_empty_title_suggestion(
        self,
        mock_print,
        mock_create_pr_gh,
        mock_input,
        mock_get_pr_description,
        mock_get_commits,
    ):
        mock_get_commits.return_value = ["feat: new feature"]
        mock_get_pr_description.return_value = ("", "AI PR Body")
        mock_input.return_value = "y"

        handle_pr_create_command(base_branch="main", repo_path=".")

        mock_get_commits.assert_called_once_with("main")
        mock_get_pr_description.assert_called_once_with(["feat: new feature"])
        mock_input.assert_called_once_with("Do you want to create this PR? (y/n): ")
        mock_print.assert_any_call(
            "Error: Cannot create PR with an empty title suggestion."
        )
        mock_create_pr_gh.assert_not_called()

    @patch("autopr.cli.get_commit_messages_for_branch")
    @patch("autopr.cli.get_pr_description_suggestion")
    @patch("builtins.input")
    @patch("autopr.cli.create_pr_gh")
    @patch("builtins.print")
    def test_handle_pr_create_command_empty_body_suggestion_warning(
        self,
        mock_print,
        mock_create_pr_gh,
        mock_input,
        mock_get_pr_description,
        mock_get_commits,
    ):
        mock_get_commits.return_value = ["feat: new feature"]
        mock_get_pr_description.return_value = ("AI PR Title", "")
        mock_input.return_value = "y"
        mock_create_pr_gh.return_value = (True, "PR created with empty body")

        handle_pr_create_command(base_branch="main", repo_path=".")

        mock_get_commits.assert_called_once_with("main")
        mock_get_pr_description.assert_called_once_with(["feat: new feature"])
        mock_input.assert_called_once_with("Do you want to create this PR? (y/n): ")
        mock_print.assert_any_call(
            "Warning: PR body suggestion is empty. Proceeding with an empty body."
        )
        mock_create_pr_gh.assert_called_once_with("AI PR Title", "", "main")
        mock_print.assert_any_call("PR created successfully!")
        mock_print.assert_any_call("PR created with empty body")


if __name__ == "__main__":
    unittest.main()

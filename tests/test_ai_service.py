import unittest
from unittest.mock import patch, Mock, MagicMock
import openai  # Import openai for its error classes
import os  # Keep os if OPENAI_API_KEY is checked directly, otherwise remove if not used elsewhere.
import re  # Keep for regex in cleaning, or remove if cleaning logic changes.

from autopr.ai_service import (
    get_commit_message_suggestion,
    get_pr_description_suggestion,
    get_pr_review_suggestions,
)


class TestGetCommitMessageSuggestion(unittest.TestCase):

    @patch("autopr.ai_service.client")  # Patch the initialized client object
    def test_get_suggestion_success(self, mock_openai_client):
        mock_diff = "diff --git a/file.txt b/file.txt\n--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-old\n+new"
        expected_suggestion = "feat: Update file.txt with new content"

        # Mock the response from OpenAI API
        mock_completion = Mock()
        mock_completion.message = Mock()
        mock_completion.message.content = expected_suggestion

        mock_response = Mock()
        mock_response.choices = [mock_completion]

        mock_openai_client.chat.completions.create.return_value = mock_response

        suggestion = get_commit_message_suggestion(mock_diff)
        self.assertEqual(suggestion, expected_suggestion)
        mock_openai_client.chat.completions.create.assert_called_once()
        # You could add more detailed assertions about the prompt sent to OpenAI if desired

    @patch("autopr.ai_service.client")
    def test_no_diff_provided(self, mock_openai_client):
        suggestion = get_commit_message_suggestion("")
        self.assertEqual(suggestion, "[No diff provided to generate commit message.]")
        mock_openai_client.chat.completions.create.assert_not_called()

    @patch("autopr.ai_service.client")
    @patch("builtins.print")  # To capture error prints
    def test_openai_api_error(self, mock_print, mock_openai_client):
        mock_diff = "some diff"
        mock_openai_client.chat.completions.create.side_effect = openai.APIError(
            "API connection error", request=None, body=None
        )

        suggestion = get_commit_message_suggestion(mock_diff)
        self.assertEqual(suggestion, "[Error communicating with OpenAI API]")
        mock_print.assert_any_call("OpenAI API Error: API connection error")

    @patch("autopr.ai_service.client")
    @patch("builtins.print")
    def test_openai_client_not_initialized(self, mock_print, mock_openai_client):
        # Simulate client being None
        with patch("autopr.ai_service.client", None):
            suggestion = get_commit_message_suggestion("some diff")
            self.assertEqual(
                suggestion, "[OpenAI client not initialized. Check API key.]"
            )

    @patch("autopr.ai_service.client")
    @patch("builtins.print")
    def test_unexpected_error(self, mock_print, mock_openai_client):
        mock_diff = "some diff"
        mock_openai_client.chat.completions.create.side_effect = Exception(
            "Unexpected issue"
        )

        suggestion = get_commit_message_suggestion(mock_diff)
        self.assertEqual(suggestion, "[Error generating commit message]")
        mock_print.assert_any_call(
            "An unexpected error occurred in get_commit_message_suggestion: Unexpected issue"
        )

    @patch("autopr.ai_service.client")
    def test_get_suggestion_success_plain(self, mock_openai_client):
        mock_diff = "diff --git a/file.txt b/file.txt\n--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-old\n+new"
        raw_suggestion = "feat: Update file.txt with new content"
        expected_clean_suggestion = "feat: Update file.txt with new content"

        mock_completion = Mock()
        mock_completion.message = Mock()
        mock_completion.message.content = raw_suggestion
        mock_response = Mock()
        mock_response.choices = [mock_completion]
        mock_openai_client.chat.completions.create.return_value = mock_response

        suggestion = get_commit_message_suggestion(mock_diff)
        self.assertEqual(suggestion, expected_clean_suggestion)

    @patch("autopr.ai_service.client")
    def test_get_suggestion_with_triple_backticks(self, mock_openai_client):
        raw_suggestion = "```feat: Surrounded by triple backticks```"
        expected_clean_suggestion = "feat: Surrounded by triple backticks"
        mock_completion = Mock(message=Mock(content=raw_suggestion))
        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[mock_completion]
        )
        suggestion = get_commit_message_suggestion("some diff")
        self.assertEqual(suggestion, expected_clean_suggestion)

    @patch("autopr.ai_service.client")
    def test_get_suggestion_with_triple_backticks_and_lang(self, mock_openai_client):
        raw_suggestion = "```text\nfeat: Surrounded by triple backticks with lang\n```"
        expected_clean_suggestion = "feat: Surrounded by triple backticks with lang"
        mock_completion = Mock(message=Mock(content=raw_suggestion))
        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[mock_completion]
        )
        suggestion = get_commit_message_suggestion("some diff")
        self.assertEqual(suggestion, expected_clean_suggestion)

    @patch("autopr.ai_service.client")
    def test_get_suggestion_with_single_backticks(self, mock_openai_client):
        raw_suggestion = "`feat: Surrounded by single backticks`"
        expected_clean_suggestion = "feat: Surrounded by single backticks"
        mock_completion = Mock(message=Mock(content=raw_suggestion))
        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[mock_completion]
        )
        suggestion = get_commit_message_suggestion("some diff")
        self.assertEqual(suggestion, expected_clean_suggestion)

    @patch("autopr.ai_service.client")
    def test_get_suggestion_with_mixed_backticks_and_whitespace(
        self, mock_openai_client
    ):
        raw_suggestion = "  ```  `feat: Mixed with spaces`   ```  "
        # Expected: first ``` and content, then inner ` ` are stripped
        # Current logic: strips outer ``` then strips ` `
        expected_clean_suggestion = "feat: Mixed with spaces"
        mock_completion = Mock(message=Mock(content=raw_suggestion))
        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[mock_completion]
        )
        suggestion = get_commit_message_suggestion("some diff")
        self.assertEqual(suggestion, expected_clean_suggestion)

    @patch("autopr.ai_service.client")
    def test_get_suggestion_only_backticks(self, mock_openai_client):
        raw_suggestion = "``` ```"
        expected_clean_suggestion = ""
        mock_completion = Mock(message=Mock(content=raw_suggestion))
        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[mock_completion]
        )
        suggestion = get_commit_message_suggestion("some diff")
        self.assertEqual(suggestion, expected_clean_suggestion)

    @patch("autopr.ai_service.client")
    def test_get_suggestion_single_backticks_not_at_ends(self, mock_openai_client):
        raw_suggestion = "feat: Contains `middle` backticks"
        expected_clean_suggestion = "feat: Contains `middle` backticks"
        mock_completion = Mock(message=Mock(content=raw_suggestion))
        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[mock_completion]
        )
        suggestion = get_commit_message_suggestion("some diff")
        self.assertEqual(suggestion, expected_clean_suggestion)


class TestGetPrReviewSuggestions(unittest.TestCase):
    @patch("autopr.ai_service.client")
    def test_get_pr_review_suggestions_success(self, mock_client):
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='[{"path": "file.txt", "line": 10, "suggestion": "Consider adding a comment here"}, {"path": "file.txt", "line": 20, "suggestion": "This could be simplified"}]'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        # Test the function
        result = get_pr_review_suggestions(
            "diff --git a/file.txt b/file.txt\n@@ -1,1 +1,1 @@\n-old\n+new"
        )

        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["path"], "file.txt")
        self.assertEqual(result[0]["line"], 10)
        self.assertEqual(result[0]["suggestion"], "Consider adding a comment here")
        self.assertEqual(result[1]["path"], "file.txt")
        self.assertEqual(result[1]["line"], 20)
        self.assertEqual(result[1]["suggestion"], "This could be simplified")

        # Verify OpenAI call
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args["model"], "gpt-4-turbo-preview")
        self.assertEqual(call_args["temperature"], 0.7)
        self.assertEqual(call_args["max_tokens"], 1000)
        self.assertEqual(len(call_args["messages"]), 2)
        self.assertEqual(call_args["messages"][0]["role"], "system")
        self.assertEqual(call_args["messages"][1]["role"], "user")
        self.assertIn(
            "diff --git a/file.txt b/file.txt", call_args["messages"][1]["content"]
        )

    @patch("autopr.ai_service.client")
    def test_get_pr_review_suggestions_with_markdown(self, mock_client):
        # Mock OpenAI response with markdown code block
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='```json\n[{"path": "file.txt", "line": 10, "suggestion": "Consider adding a comment here"}]\n```'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        # Test the function
        result = get_pr_review_suggestions(
            "diff --git a/file.txt b/file.txt\n@@ -1,1 +1,1 @@\n-old\n+new"
        )

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["path"], "file.txt")
        self.assertEqual(result[0]["line"], 10)
        self.assertEqual(result[0]["suggestion"], "Consider adding a comment here")

    @patch("autopr.ai_service.client")
    def test_get_pr_review_suggestions_invalid_json(self, mock_client):
        # Mock OpenAI response with invalid JSON
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="This is not valid JSON"))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        # Test the function
        result = get_pr_review_suggestions(
            "diff --git a/file.txt b/file.txt\n@@ -1,1 +1,1 @@\n-old\n+new"
        )

        # Verify the result
        self.assertEqual(result, [])

    @patch("autopr.ai_service.client")
    def test_get_pr_review_suggestions_invalid_format(self, mock_client):
        # Mock OpenAI response with invalid suggestion format
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='[{"path": "file.txt", "line": "not a number", "suggestion": "Invalid line number"}]'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        # Test the function
        result = get_pr_review_suggestions(
            "diff --git a/file.txt b/file.txt\n@@ -1,1 +1,1 @@\n-old\n+new"
        )

        # Verify the result
        self.assertEqual(result, [])

    @patch("autopr.ai_service.client")
    def test_get_pr_review_suggestions_missing_fields(self, mock_client):
        # Mock OpenAI response with missing fields
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='[{"path": "file.txt", "suggestion": "Missing line number"}]'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        # Test the function
        result = get_pr_review_suggestions(
            "diff --git a/file.txt b/file.txt\n@@ -1,1 +1,1 @@\n-old\n+new"
        )

        # Verify the result
        self.assertEqual(result, [])

    @patch("autopr.ai_service.client")
    def test_get_pr_review_suggestions_api_error(self, mock_client):
        # Mock OpenAI API error
        mock_client.chat.completions.create.side_effect = openai.APIError(
            "API error", request=None, body=None
        )

        # Test the function
        result = get_pr_review_suggestions(
            "diff --git a/file.txt b/file.txt\n@@ -1,1 +1,1 @@\n-old\n+new"
        )

        # Verify the result
        self.assertEqual(result, [])


class TestGetPrDescriptionSuggestion(unittest.TestCase):
    @patch("autopr.ai_service.client")
    def test_get_pr_description_suggestion_success(self, mock_openai_client):
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="feat: Add new feature\n\nThis PR adds a new feature that improves the user experience."
                )
            )
        ]
        mock_openai_client.chat.completions.create.return_value = mock_response

        # Test the function
        title, body = get_pr_description_suggestion(["feat: Add new feature"])

        # Verify the result
        self.assertEqual(title, "feat: Add new feature")
        self.assertEqual(
            body, "This PR adds a new feature that improves the user experience."
        )

        # Verify OpenAI call
        mock_openai_client.chat.completions.create.assert_called_once()
        call_args = mock_openai_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args["model"], "gpt-4-turbo-preview")
        self.assertEqual(len(call_args["messages"]), 2)
        self.assertEqual(call_args["messages"][0]["role"], "system")
        self.assertEqual(call_args["messages"][1]["role"], "user")

    @patch("autopr.ai_service.client")
    def test_get_pr_description_no_commit_messages(self, mock_openai_client):
        title, body = get_pr_description_suggestion([])
        self.assertEqual(title, "[No commit messages provided]")
        self.assertEqual(body, "Cannot generate PR description without commit messages.")
        mock_openai_client.chat.completions.create.assert_not_called()

    def test_get_pr_description_no_openai_client(self):
        # Simulate client not being initialized
        with patch("autopr.ai_service.client", None):
            title, body = get_pr_description_suggestion(["some commit"])
            self.assertEqual(title, "[OpenAI client not initialized]")
            self.assertEqual(body, "Ensure OPENAI_API_KEY is set.")

    @patch("autopr.ai_service.client")
    def test_get_pr_description_suggestion_api_error(self, mock_openai_client):
        mock_openai_client.chat.completions.create.side_effect = openai.APIError(
            "API error", request=None, body=None
        )
        title, body = get_pr_description_suggestion(["some commit"])
        self.assertEqual(title, "[Error retrieving PR description]")
        self.assertEqual(body, "")

    @patch("autopr.ai_service.client")
    def test_get_pr_description_suggestion_empty_response(self, mock_openai_client):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=""))]
        mock_openai_client.chat.completions.create.return_value = mock_response

        title, body = get_pr_description_suggestion(["some commit"])
        self.assertEqual(title, "[Error retrieving PR description]")
        self.assertEqual(body, "")

    @patch("autopr.ai_service.client")
    def test_get_pr_description_suggestion_cleans_title_and_body(
        self, mock_openai_client
    ):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='```markdown\nfeat: "Title" with `backticks`\n\nBody with `backticks` and ```code blocks```\n```'
                )
            )
        ]
        mock_openai_client.chat.completions.create.return_value = mock_response

        title, body = get_pr_description_suggestion(["some commit"])
        self.assertEqual(title, 'feat: Title with backticks')
        self.assertEqual(body, "Body with `backticks` and code blocks")

    @patch("autopr.ai_service.client")
    def test_get_pr_description_suggestion_body_only_single_backticks(
        self, mock_openai_client
    ):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="feat: Title\n\n`Body with single backticks`"
                )
            )
        ]
        mock_openai_client.chat.completions.create.return_value = mock_response

        title, body = get_pr_description_suggestion(["some commit"])
        self.assertEqual(title, "feat: Title")
        self.assertEqual(body, "Body with single backticks")


if __name__ == "__main__":
    unittest.main()

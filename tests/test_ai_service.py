import unittest
from unittest.mock import patch, Mock, MagicMock
import openai  # Import openai for its error classes
import os  # Keep os if OPENAI_API_KEY is checked directly, otherwise remove if not used elsewhere.
import re  # Keep for regex in cleaning, or remove if cleaning logic changes.

from autopr.ai_service import (
    get_commit_message_suggestion,
    get_pr_description_suggestion,
    get_pr_review_suggestions,
)  # Import new function


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


class TestGetPrDescriptionSuggestion(unittest.TestCase):
    @patch("autopr.ai_service.client")
    def test_get_pr_description_suggestion_success(self, mock_openai_client):
        mock_completion_choice = MagicMock()
        mock_completion_choice.message.content = "AI PR Title\nAI PR Body"
        mock_completion = MagicMock()
        mock_completion.choices = [mock_completion_choice]
        mock_openai_client.chat.completions.create.return_value = mock_completion

        commit_messages = ["feat: implement X", "fix: correct Y"]
        title, body = get_pr_description_suggestion(commit_messages)

        self.assertEqual(title, "AI PR Title")
        self.assertEqual(body, "AI PR Body")
        # Check that the prompt was constructed correctly (simplified)
        mock_openai_client.chat.completions.create.assert_called_once()
        called_args, called_kwargs = (
            mock_openai_client.chat.completions.create.call_args
        )
        self.assertIn("feat: implement X", called_kwargs["messages"][1]["content"])
        self.assertIn("fix: correct Y", called_kwargs["messages"][1]["content"])
        self.assertNotIn(
            "Issue #", called_kwargs["messages"][1]["content"]
        )  # Ensure issue details are not in prompt

    @patch("autopr.ai_service.client")
    def test_get_pr_description_no_commit_messages(self, mock_openai_client):
        title, body = get_pr_description_suggestion([])
        self.assertEqual(title, "[No commit messages provided]")
        self.assertTrue(body.startswith("Cannot generate PR description"))
        mock_openai_client.chat.completions.create.assert_not_called()

    def test_get_pr_description_no_openai_client(self):
        # Simulate client not being initialized
        with patch("autopr.ai_service.client", None):
            title, body = get_pr_description_suggestion(["test commit"])
            self.assertEqual(title, "[OpenAI client not initialized]")
            self.assertTrue(body.startswith("Ensure OPENAI_API_KEY"))

    @patch("autopr.ai_service.client")
    def test_get_pr_description_suggestion_api_error(self, mock_openai_client):
        mock_openai_client.chat.completions.create.side_effect = openai.APIError(
            "API Error", request=None, body=None
        )
        title, body = get_pr_description_suggestion(["some commit"])
        self.assertEqual(title, "[Error retrieving PR description]")
        self.assertEqual(body, "")

    @patch("autopr.ai_service.client")
    def test_get_pr_description_suggestion_empty_response(self, mock_openai_client):
        mock_completion_choice = MagicMock()
        mock_completion_choice.message.content = ""  # Empty response
        mock_completion = MagicMock()
        mock_completion.choices = [mock_completion_choice]
        mock_openai_client.chat.completions.create.return_value = mock_completion

        title, body = get_pr_description_suggestion(["test commit"])
        self.assertEqual(title, "[AI returned empty response]")
        self.assertEqual(body, "")

    @patch("autopr.ai_service.client")
    def test_get_pr_description_suggestion_cleans_title_and_body(
        self, mock_openai_client
    ):
        mock_completion_choice = MagicMock()
        # Title with backticks and quotes, Body with triple backticks
        mock_completion_choice.message.content = (
            '"`Clean This Title`"\n```markdown\nClean This Body\n```'
        )
        mock_completion = MagicMock()
        mock_completion.choices = [mock_completion_choice]
        mock_openai_client.chat.completions.create.return_value = mock_completion

        title, body = get_pr_description_suggestion(["test commit"])
        self.assertEqual(title, "Clean This Title")
        self.assertEqual(body, "Clean This Body")

    @patch("autopr.ai_service.client")
    def test_get_pr_description_suggestion_body_only_single_backticks(
        self, mock_openai_client
    ):
        mock_completion_choice = MagicMock()
        mock_completion_choice.message.content = "Normal Title\n`Clean This Body`"
        mock_completion = MagicMock()
        mock_completion.choices = [mock_completion_choice]
        mock_openai_client.chat.completions.create.return_value = mock_completion

        title, body = get_pr_description_suggestion(["test commit"])
        self.assertEqual(title, "Normal Title")
        self.assertEqual(body, "Clean This Body")


class TestGetPrReviewSuggestions(unittest.TestCase):
    @patch("autopr.ai_service.client")
    def test_success_basic_case(self, mock_openai_client):
        mock_pr_changes = "diff --git a/file.py b/file.py\n--- a/file.py\n+++ b/file.py\n@@ -1,1 +1,2 @@\n print(\"hello\")\n+print(\"world\")"
        ai_response_content = '[{"path": "file.py", "line": 2, "suggestion": "Consider a more descriptive variable name."}]'
        
        mock_completion = MagicMock()
        mock_completion.message.content = ai_response_content
        mock_openai_client.chat.completions.create.return_value = MagicMock(choices=[mock_completion])

        suggestions = get_pr_review_suggestions(mock_pr_changes)
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["path"], "file.py")
        self.assertEqual(suggestions[0]["line"], 2)
        self.assertEqual(suggestions[0]["suggestion"], "Consider a more descriptive variable name.")
        mock_openai_client.chat.completions.create.assert_called_once()
        call_args = mock_openai_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args["response_format"], { "type": "json_object" })
        self.assertIn(mock_pr_changes, call_args["messages"][1]["content"])

    @patch("autopr.ai_service.client")
    def test_success_wrapped_in_suggestions_key(self, mock_openai_client):
        mock_pr_changes = "diff content"
        ai_response_content = '{"suggestions": [{"path": "file.py", "line": 5, "suggestion": "Good job!"}]}'
        mock_completion = MagicMock(message=MagicMock(content=ai_response_content))
        mock_openai_client.chat.completions.create.return_value = MagicMock(choices=[mock_completion])

        suggestions = get_pr_review_suggestions(mock_pr_changes)
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["path"], "file.py")
        self.assertEqual(suggestions[0]["line"], 5)

    @patch("autopr.ai_service.client")
    def test_empty_pr_changes(self, mock_openai_client):
        suggestions = get_pr_review_suggestions("")
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["path"], "error")
        self.assertEqual(suggestions[0]["suggestion"], "[No PR changes provided to generate review.]")
        mock_openai_client.chat.completions.create.assert_not_called()

    @patch("autopr.ai_service.client", None)
    def test_openai_client_not_initialized(self):
        suggestions = get_pr_review_suggestions("some diff")
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["path"], "error")
        self.assertEqual(suggestions[0]["suggestion"], "[OpenAI client not initialized. Check API key.]")

    @patch("autopr.ai_service.client")
    @patch("builtins.print") # To capture error prints
    def test_openai_api_error(self, mock_print, mock_openai_client):
        mock_openai_client.chat.completions.create.side_effect = openai.APIError("API connection error", request=None, body=None)
        suggestions = get_pr_review_suggestions("some diff")
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["path"], "error")
        self.assertTrue("OpenAI API Error" in suggestions[0]["suggestion"])
        mock_print.assert_any_call("OpenAI API Error in get_pr_review_suggestions: API connection error")

    @patch("autopr.ai_service.client")
    @patch("builtins.print")
    def test_json_decode_error(self, mock_print, mock_openai_client):
        ai_response_content = "not a valid json string"
        mock_completion = MagicMock(message=MagicMock(content=ai_response_content))
        mock_openai_client.chat.completions.create.return_value = MagicMock(choices=[mock_completion])
        
        suggestions = get_pr_review_suggestions("some diff")
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["path"], "error")
        self.assertEqual(suggestions[0]["suggestion"], "[AI JSON parsing error]")
        mock_print.assert_any_call(f"Error parsing AI response as JSON: Expecting value: line 1 column 1 (char 0)") # Error message might vary slightly
        mock_print.assert_any_call(f"Raw response was: {ai_response_content}")

    @patch("autopr.ai_service.client")
    @patch("builtins.print")
    def test_unexpected_response_format_not_list_or_dict_suggestions(self, mock_print, mock_openai_client):
        ai_response_content = '{"some_other_key": [{"path": "file.py", "line": 5, "suggestion": "Good job!"}]}'
        mock_completion = MagicMock(message=MagicMock(content=ai_response_content))
        mock_openai_client.chat.completions.create.return_value = MagicMock(choices=[mock_completion])

        suggestions = get_pr_review_suggestions("some diff")
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["path"], "error")
        self.assertEqual(suggestions[0]["suggestion"], "[AI response format error]")
        mock_print.assert_any_call("Error: AI response was not in the expected format (list or dict with 'suggestions' key). Got: <class 'dict'>")

    @patch("autopr.ai_service.client")
    @patch("builtins.print")
    def test_suggestion_item_not_a_dict(self, mock_print, mock_openai_client):
        ai_response_content = '[{"path": "file.py", "line": 1, "suggestion": "Valid"}, "not a dict"]'
        mock_completion = MagicMock(message=MagicMock(content=ai_response_content))
        mock_openai_client.chat.completions.create.return_value = MagicMock(choices=[mock_completion])
        
        suggestions = get_pr_review_suggestions("some diff")
        self.assertEqual(len(suggestions), 1) # Only the valid one
        self.assertEqual(suggestions[0]["path"], "file.py")
        mock_print.assert_any_call("Warning: Skipping suggestion, not a dict: not a dict")

    @patch("autopr.ai_service.client")
    @patch("builtins.print")
    def test_suggestion_missing_required_keys(self, mock_print, mock_openai_client):
        ai_response_content = '[{"path": "file.py", "suggestion": "Missing line"}]'
        mock_completion = MagicMock(message=MagicMock(content=ai_response_content))
        mock_openai_client.chat.completions.create.return_value = MagicMock(choices=[mock_completion])

        suggestions = get_pr_review_suggestions("some diff")
        self.assertEqual(len(suggestions), 0) # Invalid suggestion is skipped
        mock_print.assert_any_call("Warning: Skipping suggestion, missing required keys: {'path': 'file.py', 'suggestion': 'Missing line'}")

    @patch("autopr.ai_service.client")
    @patch("builtins.print")
    def test_suggestion_invalid_type_path(self, mock_print, mock_openai_client):
        ai_response_content = '[{"path": 123, "line": 1, "suggestion": "Path not string"}]'
        mock_completion = MagicMock(message=MagicMock(content=ai_response_content))
        mock_openai_client.chat.completions.create.return_value = MagicMock(choices=[mock_completion])

        suggestions = get_pr_review_suggestions("some diff")
        self.assertEqual(len(suggestions), 0)
        mock_print.assert_any_call("Warning: Skipping suggestion, 'path' is not a string: {'path': 123, 'line': 1, 'suggestion': 'Path not string'}")

    @patch("autopr.ai_service.client")
    @patch("builtins.print")
    def test_suggestion_invalid_type_line_non_convertible(self, mock_print, mock_openai_client):
        ai_response_content = '[{"path": "file.py", "line": "not_an_int", "suggestion": "Line not int"}]'
        mock_completion = MagicMock(message=MagicMock(content=ai_response_content))
        mock_openai_client.chat.completions.create.return_value = MagicMock(choices=[mock_completion])

        suggestions = get_pr_review_suggestions("some diff")
        self.assertEqual(len(suggestions), 0)
        mock_print.assert_any_call("Warning: Skipping suggestion, 'line' is not an int: {'path': 'file.py', 'line': 'not_an_int', 'suggestion': 'Line not int'}")

    @patch("autopr.ai_service.client")
    def test_suggestion_convertible_string_line(self, mock_openai_client):
        ai_response_content = '[{"path": "file.py", "line": "30", "suggestion": "Line is string 30"}]'
        mock_completion = MagicMock(message=MagicMock(content=ai_response_content))
        mock_openai_client.chat.completions.create.return_value = MagicMock(choices=[mock_completion])

        suggestions = get_pr_review_suggestions("some diff")
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["line"], 30) # Should be converted to int

    @patch("autopr.ai_service.client")
    @patch("builtins.print")
    def test_suggestion_invalid_type_suggestion(self, mock_print, mock_openai_client):
        ai_response_content = '[{"path": "file.py", "line": 1, "suggestion": ["list", "not string"]}]'
        mock_completion = MagicMock(message=MagicMock(content=ai_response_content))
        mock_openai_client.chat.completions.create.return_value = MagicMock(choices=[mock_completion])

        suggestions = get_pr_review_suggestions("some diff")
        self.assertEqual(len(suggestions), 0)
        mock_print.assert_any_call("Warning: Skipping suggestion, 'suggestion' is not a string: {'path': 'file.py', 'line': 1, 'suggestion': ['list', 'not string']}")

    @patch("autopr.ai_service.client")
    @patch("builtins.print")
    def test_path_cleaning_diff_git_marker(self, mock_print, mock_openai_client):
        ai_response_content = '[{"path": "diff --git a/src/actual/file.py b/src/actual/file.py", "line": 10, "suggestion": "Path needs cleaning."}]'
        mock_completion = MagicMock(message=MagicMock(content=ai_response_content))
        mock_openai_client.chat.completions.create.return_value = MagicMock(choices=[mock_completion])

        suggestions = get_pr_review_suggestions("some diff")
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["path"], "src/actual/file.py")
        mock_print.assert_any_call("Warning: Correcting suspicious path in suggestion: diff --git a/src/actual/file.py b/src/actual/file.py")

    @patch("autopr.ai_service.client")
    @patch("builtins.print")
    def test_path_cleaning_diff_git_marker_no_b_path(self, mock_print, mock_openai_client):
        # Edge case where our simple regex might fail
        malformed_path = "diff --git a/src/actual/file.py src/actual/file.py" # Missing b/
        ai_response_content = '[{"path": "' + malformed_path + '", "line": 10, "suggestion": "Path needs cleaning, no b/ path."}]'
        mock_completion = MagicMock(message=MagicMock(content=ai_response_content))
        mock_openai_client.chat.completions.create.return_value = MagicMock(choices=[mock_completion])

        suggestions = get_pr_review_suggestions("some diff")
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["path"], malformed_path) # Path remains unchanged as regex fails
        mock_print.assert_any_call(f"Warning: Correcting suspicious path in suggestion: {malformed_path}")
        mock_print.assert_any_call(f"Warning: Could not reliably clean path: {malformed_path}")

    @patch("autopr.ai_service.client")
    @patch("builtins.print")
    def test_unexpected_exception_in_service(self, mock_print, mock_openai_client):
        mock_openai_client.chat.completions.create.side_effect = Exception("Runtime Kaboom")
        suggestions = get_pr_review_suggestions("some diff")
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["path"], "error")
        self.assertTrue("Unexpected error in review generation: Runtime Kaboom" in suggestions[0]["suggestion"])
        mock_print.assert_any_call("Error generating PR review suggestions: Runtime Kaboom")

    @patch("autopr.ai_service.client")
    def test_no_suggestions_from_ai_empty_array(self, mock_openai_client):
        ai_response_content = '[]'
        mock_completion = MagicMock(message=MagicMock(content=ai_response_content))
        mock_openai_client.chat.completions.create.return_value = MagicMock(choices=[mock_completion])

        suggestions = get_pr_review_suggestions("some diff")
        self.assertEqual(len(suggestions), 0) # Empty list is a valid response

    @patch("autopr.ai_service.client")
    def test_no_suggestions_from_ai_empty_suggestions_key(self, mock_openai_client):
        ai_response_content = '{"suggestions": []}'
        mock_completion = MagicMock(message=MagicMock(content=ai_response_content))
        mock_openai_client.chat.completions.create.return_value = MagicMock(choices=[mock_completion])

        suggestions = get_pr_review_suggestions("some diff")
        self.assertEqual(len(suggestions), 0) # Empty list is valid


if __name__ == "__main__":
    unittest.main()

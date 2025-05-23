import unittest
from unittest.mock import patch, Mock
import openai # Import openai for its error classes

from autopr.ai_service import get_commit_message_suggestion, get_pr_description_suggestion # Import new function

class TestGetCommitMessageSuggestion(unittest.TestCase):

    @patch('autopr.ai_service.client') # Patch the initialized client object
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

    @patch('autopr.ai_service.client')
    def test_no_diff_provided(self, mock_openai_client):
        suggestion = get_commit_message_suggestion("")
        self.assertEqual(suggestion, "[No diff provided to generate commit message.]")
        mock_openai_client.chat.completions.create.assert_not_called()

    @patch('autopr.ai_service.client')
    @patch('builtins.print') # To capture error prints
    def test_openai_api_error(self, mock_print, mock_openai_client):
        mock_diff = "some diff"
        mock_openai_client.chat.completions.create.side_effect = openai.APIError("API connection error", request=None, body=None)

        suggestion = get_commit_message_suggestion(mock_diff)
        self.assertEqual(suggestion, "[Error communicating with OpenAI API]")
        mock_print.assert_any_call("OpenAI API Error: API connection error")

    @patch('autopr.ai_service.client')
    @patch('builtins.print')
    def test_openai_client_not_initialized(self, mock_print, mock_openai_client):
        # Simulate client being None
        with patch('autopr.ai_service.client', None):
            suggestion = get_commit_message_suggestion("some diff")
            self.assertEqual(suggestion, "[OpenAI client not initialized. Check API key.]")

    @patch('autopr.ai_service.client')
    @patch('builtins.print')
    def test_unexpected_error(self, mock_print, mock_openai_client):
        mock_diff = "some diff"
        mock_openai_client.chat.completions.create.side_effect = Exception("Unexpected issue")

        suggestion = get_commit_message_suggestion(mock_diff)
        self.assertEqual(suggestion, "[Error generating commit message]")
        mock_print.assert_any_call("An unexpected error occurred in get_commit_message_suggestion: Unexpected issue")

    @patch('autopr.ai_service.client') 
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

    @patch('autopr.ai_service.client')
    def test_get_suggestion_with_triple_backticks(self, mock_openai_client):
        raw_suggestion = "```feat: Surrounded by triple backticks```"
        expected_clean_suggestion = "feat: Surrounded by triple backticks"
        mock_completion = Mock(message=Mock(content=raw_suggestion))
        mock_openai_client.chat.completions.create.return_value = Mock(choices=[mock_completion])
        suggestion = get_commit_message_suggestion("some diff")
        self.assertEqual(suggestion, expected_clean_suggestion)

    @patch('autopr.ai_service.client')
    def test_get_suggestion_with_triple_backticks_and_lang(self, mock_openai_client):
        raw_suggestion = "```text\nfeat: Surrounded by triple backticks with lang\n```"
        expected_clean_suggestion = "feat: Surrounded by triple backticks with lang"
        mock_completion = Mock(message=Mock(content=raw_suggestion))
        mock_openai_client.chat.completions.create.return_value = Mock(choices=[mock_completion])
        suggestion = get_commit_message_suggestion("some diff")
        self.assertEqual(suggestion, expected_clean_suggestion)
    
    @patch('autopr.ai_service.client')
    def test_get_suggestion_with_single_backticks(self, mock_openai_client):
        raw_suggestion = "`feat: Surrounded by single backticks`"
        expected_clean_suggestion = "feat: Surrounded by single backticks"
        mock_completion = Mock(message=Mock(content=raw_suggestion))
        mock_openai_client.chat.completions.create.return_value = Mock(choices=[mock_completion])
        suggestion = get_commit_message_suggestion("some diff")
        self.assertEqual(suggestion, expected_clean_suggestion)

    @patch('autopr.ai_service.client')
    def test_get_suggestion_with_mixed_backticks_and_whitespace(self, mock_openai_client):
        raw_suggestion = "  ```  `feat: Mixed with spaces`   ```  "
        # Expected: first ``` and content, then inner ` ` are stripped
        # Current logic: strips outer ``` then strips ` `
        expected_clean_suggestion = "feat: Mixed with spaces"
        mock_completion = Mock(message=Mock(content=raw_suggestion))
        mock_openai_client.chat.completions.create.return_value = Mock(choices=[mock_completion])
        suggestion = get_commit_message_suggestion("some diff")
        self.assertEqual(suggestion, expected_clean_suggestion)

    @patch('autopr.ai_service.client')
    def test_get_suggestion_only_backticks(self, mock_openai_client):
        raw_suggestion = "``` ```"
        expected_clean_suggestion = ""
        mock_completion = Mock(message=Mock(content=raw_suggestion))
        mock_openai_client.chat.completions.create.return_value = Mock(choices=[mock_completion])
        suggestion = get_commit_message_suggestion("some diff")
        self.assertEqual(suggestion, expected_clean_suggestion)

    @patch('autopr.ai_service.client')
    def test_get_suggestion_single_backticks_not_at_ends(self, mock_openai_client):
        raw_suggestion = "feat: Contains `middle` backticks"
        expected_clean_suggestion = "feat: Contains `middle` backticks"
        mock_completion = Mock(message=Mock(content=raw_suggestion))
        mock_openai_client.chat.completions.create.return_value = Mock(choices=[mock_completion])
        suggestion = get_commit_message_suggestion("some diff")
        self.assertEqual(suggestion, expected_clean_suggestion)

class TestGetPrDescriptionSuggestion(unittest.TestCase):
    sample_issue_details = {
        "number": 123,
        "title": "Test Issue Title",
        "body": "This is the body of the test issue.",
        "labels": [{"name": "bug"}, {"name": "enhancement"}]
    }
    sample_commit_messages = [
        "feat: Implement part 1 of feature X",
        "fix: Correct typo in documentation for feature X"
    ]

    @patch('autopr.ai_service.client')
    def test_get_pr_description_success(self, mock_openai_client):
        raw_response_content = "Suggested PR Title\n\nThis is the suggested PR body.\nIt addresses the issue and includes commits."
        expected_title = "Suggested PR Title"
        expected_body = "This is the suggested PR body.\nIt addresses the issue and includes commits."

        mock_completion = Mock(message=Mock(content=raw_response_content))
        mock_openai_client.chat.completions.create.return_value = Mock(choices=[mock_completion])

        title, body = get_pr_description_suggestion(self.sample_issue_details, self.sample_commit_messages)
        
        self.assertEqual(title, expected_title)
        self.assertEqual(body, expected_body)
        mock_openai_client.chat.completions.create.assert_called_once()
        # Further assertions could check the prompt sent to OpenAI

    @patch('autopr.ai_service.client')
    def test_get_pr_description_success_title_cleaning(self, mock_openai_client):
        raw_response_content = "`Clean This Title`\n\nBody is fine."
        expected_title = "Clean This Title"
        expected_body = "Body is fine."
        mock_completion = Mock(message=Mock(content=raw_response_content))
        mock_openai_client.chat.completions.create.return_value = Mock(choices=[mock_completion])
        title, body = get_pr_description_suggestion(self.sample_issue_details, self.sample_commit_messages)
        self.assertEqual(title, expected_title)
        self.assertEqual(body, expected_body)

    @patch('autopr.ai_service.client')
    def test_get_pr_description_success_body_cleaning(self, mock_openai_client):
        raw_response_content = "Title is Fine\n\n```markdown\nClean This Body\n```"
        expected_title = "Title is Fine"
        expected_body = "Clean This Body"
        mock_completion = Mock(message=Mock(content=raw_response_content))
        mock_openai_client.chat.completions.create.return_value = Mock(choices=[mock_completion])
        title, body = get_pr_description_suggestion(self.sample_issue_details, self.sample_commit_messages)
        self.assertEqual(title, expected_title)
        self.assertEqual(body, expected_body)

    @patch('autopr.ai_service.client')
    def test_no_issue_details(self, mock_openai_client):
        title, body = get_pr_description_suggestion({}, self.sample_commit_messages)
        self.assertEqual(title, "[No issue details provided]")
        self.assertEqual(body, "[No issue details provided]")
        mock_openai_client.chat.completions.create.assert_not_called()

    @patch('autopr.ai_service.client')
    def test_no_commit_messages(self, mock_openai_client):
        title, body = get_pr_description_suggestion(self.sample_issue_details, [])
        self.assertEqual(title, "[No commit messages provided]")
        self.assertEqual(body, "[No commit messages provided]")
        mock_openai_client.chat.completions.create.assert_not_called()

    @patch('autopr.ai_service.client')
    @patch('builtins.print')
    def test_openai_api_error_pr(self, mock_print, mock_openai_client):
        mock_openai_client.chat.completions.create.side_effect = openai.APIError("API error for PR", request=None, body=None)
        title, body = get_pr_description_suggestion(self.sample_issue_details, self.sample_commit_messages)
        self.assertEqual(title, "[Error communicating with OpenAI API for PR]")
        self.assertEqual(body, "[Error communicating with OpenAI API for PR]")
        mock_print.assert_any_call("OpenAI API Error during PR suggestion: API error for PR")

    @patch('autopr.ai_service.client')
    @patch('builtins.print')
    def test_openai_client_not_initialized_pr(self, mock_print, mock_openai_client):
        with patch('autopr.ai_service.client', None):
            title, body = get_pr_description_suggestion(self.sample_issue_details, self.sample_commit_messages)
            self.assertEqual(title, "[OpenAI client not initialized. Check API key.]")
            self.assertEqual(body, "[OpenAI client not initialized. Check API key.]")

    @patch('autopr.ai_service.client')
    @patch('builtins.print')
    def test_unexpected_error_pr(self, mock_print, mock_openai_client):
        mock_openai_client.chat.completions.create.side_effect = Exception("Unexpected PR issue")
        title, body = get_pr_description_suggestion(self.sample_issue_details, self.sample_commit_messages)
        self.assertEqual(title, "[Error generating PR suggestion]")
        self.assertEqual(body, "[Error generating PR suggestion]")
        mock_print.assert_any_call("An unexpected error occurred in get_pr_description_suggestion: Unexpected PR issue")


if __name__ == '__main__':
    unittest.main() 
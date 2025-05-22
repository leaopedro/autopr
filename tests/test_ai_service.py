import unittest
from unittest.mock import patch, Mock
import openai # Import openai for its error classes

from autopr.ai_service import get_commit_message_suggestion

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


if __name__ == '__main__':
    unittest.main() 
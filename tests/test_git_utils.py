import unittest
from unittest.mock import patch, mock_open
import configparser
import os  # Keep os for os.path.join

# Import the function to be tested directly
from autopr.git_utils import get_repo_from_git_config


class TestGetRepoFromGitConfig(unittest.TestCase):

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    # @patch('configparser.ConfigParser.read') # This mock might be too broad if ConfigParser is instantiated inside the func
    def test_get_repo_ssh_url(self, mock_file_open, mock_exists):
        mock_exists.return_value = True

        config_content = """
[remote "origin"]
    url = git@github.com:owner/repo.git
    fetch = +refs/heads/*:refs/remotes/origin/*
"""
        config_parser_instance = configparser.ConfigParser()
        config_parser_instance.read_string(config_content)

        # Patch the ConfigParser class to return our instance
        with patch("configparser.ConfigParser") as MockConfigParser:
            MockConfigParser.return_value = config_parser_instance
            # Also, we need to ensure that config_parser_instance.read() is called as expected
            with patch.object(config_parser_instance, "read") as mock_read_method:

                repo_name = get_repo_from_git_config()
                self.assertEqual(repo_name, "owner/repo")
                mock_exists.assert_called_once_with(os.path.join(".git", "config"))
                # Check that the read method of our instance was called
                mock_read_method.assert_called_once_with(os.path.join(".git", "config"))

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_get_repo_https_url(self, mock_file_open, mock_exists):
        mock_exists.return_value = True
        config_content = """
[remote "origin"]
    url = https://github.com/owner/another-repo.git
"""
        config_parser_instance = configparser.ConfigParser()
        config_parser_instance.read_string(config_content)

        with patch("configparser.ConfigParser") as MockConfigParser:
            MockConfigParser.return_value = config_parser_instance
            with patch.object(config_parser_instance, "read") as mock_read_method:
                repo_name = get_repo_from_git_config()
                self.assertEqual(repo_name, "owner/another-repo")
                mock_read_method.assert_called_once_with(os.path.join(".git", "config"))

    @patch("os.path.exists")
    def test_git_config_not_found(self, mock_exists):
        mock_exists.return_value = False
        with self.assertRaisesRegex(FileNotFoundError, "No .git/config found"):
            get_repo_from_git_config()

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_no_origin_remote(self, mock_file_open, mock_exists):
        mock_exists.return_value = True
        config_content = """
[remote "upstream"]
    url = https://github.com/other/repo.git
"""
        config_parser_instance = configparser.ConfigParser()
        config_parser_instance.read_string(config_content)

        with patch("configparser.ConfigParser") as MockConfigParser:
            MockConfigParser.return_value = config_parser_instance
            with patch.object(config_parser_instance, "read") as mock_read_method:
                with self.assertRaisesRegex(ValueError, "No 'origin' remote found"):
                    get_repo_from_git_config()
                mock_read_method.assert_called_once_with(os.path.join(".git", "config"))

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_unsupported_url_format(self, mock_file_open, mock_exists):
        mock_exists.return_value = True
        config_content = """
[remote "origin"]
    url = file:///path/to/repo.git
"""
        config_parser_instance = configparser.ConfigParser()
        config_parser_instance.read_string(config_content)

        with patch("configparser.ConfigParser") as MockConfigParser:
            MockConfigParser.return_value = config_parser_instance
            with patch.object(config_parser_instance, "read") as mock_read_method:
                with self.assertRaisesRegex(ValueError, "Unsupported URL format"):
                    get_repo_from_git_config()
                mock_read_method.assert_called_once_with(os.path.join(".git", "config"))


# Removed TestListIssues and TestCreatePr as they belong to CLI tests

if __name__ == "__main__":
    unittest.main()

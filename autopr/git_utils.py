import configparser
import os


def get_repo_from_git_config():
    """Get the repository name from the .git/config file."""
    config = configparser.ConfigParser()
    git_config_path = os.path.join(".git", "config")
    if not os.path.exists(git_config_path):
        raise FileNotFoundError("No .git/config found in the current directory.")

    config.read(git_config_path)

    if 'remote "origin"' in config:
        url = config['remote "origin"']["url"]
        # Extract the owner/repo part from the URL
        if url.startswith("git@"):
            # SSH URL format: git@github.com:owner/repo.git
            repo = url.split(":")[1].rstrip(".git")
        elif url.startswith("https://"):
            # HTTPS URL format: https://github.com/owner/repo.git
            repo = url.split("/")[-2] + "/" + url.split("/")[-1].rstrip(".git")
        else:
            raise ValueError("Unsupported URL format.")
        return repo
    else:
        raise ValueError("No 'origin' remote found in the .git/config.")

# AutoPR

A CLI tool designed to streamline your GitHub workflow by automating Pull Request (PR) creation and issue management. Incorporates AI to assist in generating PR descriptions and Commit messages.

## Features (Current)

*   Lists open GitHub issues for the current repository.
*   Creates working feature branch based on issue number and title.
*   Creates a new Commit with an AI generated message based on staged diff.
*   Creates a new PR with an AI generated title based on previous commit messages.

## Installation & Setup

### For Users (installed via PyPI):

You can install AutoPR using pip:

```sh
pip install autopr_cli
```

### For Developers (Local Setup):

1.  Clone the repository:
    ```sh
    git clone https://github.com/leaopedro/autopr.git
    cd autopr
    ```
2.  Create and activate a virtual environment (recommended):
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3.  Install dependencies (including development tools):
    ```sh
    pip install -r requirements.txt
    ```

## Usage

Make sure you are in the root directory of your Git repository.

*   **List open issues:**
    ```sh
    autopr ls
    # For developers: python -m autopr.cli ls
    ```
*   **List all issues (open and closed):**
    ```sh
    autopr ls -a
    ```
*   **Start working on an issue:**
    ```sh
    autopr workon <issue_number>
    ```
    (See full guide below)
*   **Generate AI-assisted commit message and commit:**
    ```sh
    autopr commit
    ```
    Requires `OPENAI_API_KEY` environment variable. (See full guide below)
*   **Create a new PR (AI-assisted title/body):**
    ```sh
    autopr pr [--base <target_branch>]
    # For developers: python -m autopr.cli pr [--base <target_branch>]
    ```
*   **Review a Pull Request:**
    ```sh
    autopr review <PR_NUMBER>
    # For developers: python -m autopr.cli review <PR_NUMBER>
    ```
    Requires `OPENAI_API_KEY` environment variable. (See full guide below)

### Starting Work on an Issue (`autopr workon`)

The `workon` command helps you kickstart development on a specific GitHub issue.

**Command:**

```sh
autopr workon <issue_number>
# For developers: python -m autopr.cli workon <issue_number>
```

Replace `<issue_number>` with the actual number of the GitHub issue you want to work on.

**What it does:**

1.  **Fetches Issue Details:** It uses the `gh` CLI to retrieve the title of the specified issue.
2.  **Generates a Branch Name:** Based on the issue number and its title, it creates a sanitized, descriptive branch name in the format `feature/<issue_number>-<sanitized-title>`.
    *   *Sanitization includes:* lowercasing, replacing spaces and special characters with hyphens, and limiting length.
3.  **Creates and Switches Branch:** It executes `git checkout -b <generated_branch_name>` to create the new local branch and immediately switch to it.
4.  **Stores Context:** The issue number is saved to a file named `.autopr_current_issue` inside your local `.git` directory. This allows future `autopr` commands (like `autopr commit` and `autopr pr create` in upcoming features) to know which issue you're currently working on.

**Example:**

If you want to start working on issue #42 which has the title "Fix login button display error":

```sh
autopr workon 42
# For developers: python -m autopr.cli workon 42
```

This might:
*   Fetch details for issue #42.
*   Generate a branch name like `feature/42-fix-login-button-display-error`.
*   Create and switch to this new branch.
*   Save `42` into `.git/.autopr_current_issue`.

You are then ready to start coding on the new branch with the issue context set up for future `autopr` commands.

### Generating an AI-assisted Commit Message (`autopr commit`)

The `commit` command helps you generate a commit message using AI based on your staged changes, and then optionally commit those changes.

**Prerequisites:**

*   You must have changes staged for commit (`git add ...`).
*   You need to set the `OPENAI_API_KEY` environment variable with your valid OpenAI API key.
    ```sh
    export OPENAI_API_KEY='your_api_key_here' 
    ```
    (Add this to your shell configuration file like `.zshrc` or `.bashrc` for persistence).

**Command:**

```sh
autopr commit
# For developers: python -m autopr.cli commit
```

**What it does:**

1.  **Checks for Staged Changes:** It first runs `git diff --staged` to get your staged modifications. If there are no staged changes, it will inform you.
2.  **Sends Diff to AI:** The staged diff is sent to the OpenAI API (currently using `gpt-3.5-turbo`).
3.  **Displays AI Suggestion:** The AI-generated commit message suggestion is printed to your console.
4.  **User Confirmation:** You will be asked if you want to commit with the suggested message (`y/n`).
5.  **Commits Changes (if confirmed):**
    *   If you enter `y` (yes), `autopr` will execute `git commit -m "suggested_message"` to commit your staged changes with the AI's suggestion.
    *   If you enter `n` (no) or any other input, the commit will be aborted, and you will be advised to commit manually using `git`.
6.  **Handles Errors:** If there's an issue getting the AI suggestion (e.g., API key problem, network error) or if the `git commit` command fails, appropriate error messages will be displayed.

**Example:**

After staging some changes to `my_feature.py`:

```sh
git add my_feature.py
autopr commit
# For developers: python -m autopr.cli commit
```

If the AI service returns an error, or if you choose not to use the suggestion, you will be prompted to commit manually.

### Reviewing a Pull Request (`autopr review`)

The `review` command leverages AI to analyze the changes in a specified Pull Request and posts suggestions directly as comments on GitHub.

**Prerequisites:**

*   You must have the `gh` CLI installed and authenticated (`gh auth login`).
*   You need to set the `OPENAI_API_KEY` environment variable with your valid OpenAI API key.
    ```sh
    export OPENAI_API_KEY='your_api_key_here'
    ```

**Command:**

```sh
autopr review <PR_NUMBER>
# For developers: python -m autopr.cli review <PR_NUMBER>
```
Replace `<PR_NUMBER>` with the actual number of the Pull Request you want to review.

**What it does:**

1.  **Fetches PR Changes:** It uses `gh pr diff <PR_NUMBER>` to get the diff of the specified Pull Request.
2.  **Sends Diff to AI:** The PR diff is sent to the OpenAI API (currently using `gpt-4-turbo-preview`) to generate review suggestions.
3.  **Parses Suggestions:** The AI is prompted to return suggestions in a specific JSON format, including the file path, line number, and the suggestion text.
4.  **Posts Comments to GitHub:** For each valid suggestion, `autopr` uses `gh api` to post a review comment directly to the specified line in the relevant file of the Pull Request. It dynamically fetches repository and PR details (like the head commit SHA) to ensure comments are correctly attributed.
5.  **Provides Summary:** Outputs a summary of how many comments were successfully posted and if any failures occurred.
6.  **Handles Errors:** If there are issues (e.g., PR not found, AI errors, problems posting comments), appropriate messages are displayed.

**Example:**

To review Pull Request #7:

```sh
autopr review 7
# For developers: python -m autopr.cli review 7
```

`autopr` will then fetch the changes for PR #7, get AI suggestions, and attempt to post them as review comments on GitHub.

## Development

### Running Tests

To run the automated tests, use Make:

```sh
make test
```

### Formatting Code

To format the code using Black:

```sh
make format
```

### Publishing a New Version (for Maintainers)

This project uses `Makefile` targets to streamline the release process. Ensure you have `twine` configured with your PyPI credentials (API tokens are recommended) and have installed development dependencies via `pip install -r requirements.txt`.

1.  **Update Version:** Increment the `__version__` string in `autopr/__init__.py`.

2.  **Build the Package:**
    ```sh
    make build
    ```
    This cleans old builds and creates new source distribution and wheel files in the `dist/` directory.

3.  **Test Publishing (Highly Recommended):** Publish to TestPyPI to ensure everything works correctly before a real release.
    ```sh
    make publish-test
    ```
    You will be prompted for confirmation. Check the package on [test.pypi.org](https://test.pypi.org).

4.  **Publish to PyPI (Real):**
    ```sh
    make publish
    ```
    This will upload the package to the official PyPI. You will be prompted for confirmation.

5.  **Full Release (Publish to PyPI & Tag):** For a complete release including Git tagging:
    ```sh
    make release
    ```
    This performs `make publish` and then creates a Git tag for the new version (e.g., `v0.2.5`).
    After running this, you **must** push the tag to the remote repository:
    ```sh
    git push origin vX.Y.Z  # Replace X.Y.Z with the version number
    # OR push all tags if you have multiple new tags
    git push --tags
    ```

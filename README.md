# AutoPR

A CLI tool designed to streamline your GitHub workflow by automating Pull Request (PR) creation and issue management. Future versions will incorporate AI to assist in generating PR descriptions.

## Features (Current)

*   List open GitHub issues for the current repository.
*   List all (open and closed) GitHub issues using the `-a` flag.
*   Create a new PR with a specified title.
*   Automatically detects the GitHub repository from your local .git configuration.

## Installation & Setup

### For Users (when published on PyPI):

You can install AutoPR using pip:

```sh
pip install autopr_cli
```

### For Developers (Local Setup):

1.  Clone the repository:
    ```sh
    git clone <your-repository-url> # Replace <your-repository-url> with the actual URL
    cd autopr-cli # Or your repository's directory name
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
    # For developers: python -m autopr.cli ls -a
    ```
*   **Start working on an issue:**
    ```sh
    autopr workon <issue_number>
    # For developers: python -m autopr.cli workon <issue_number>
    ```
    (See full guide below)
*   **Create a new PR:**
    ```sh
    autopr create --title "Your Amazing PR Title"
    # For developers: python -m autopr.cli create --title "Your Amazing PR Title"
    ```

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
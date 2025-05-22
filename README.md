# AutoPR

A CLI tool designed to streamline your GitHub workflow by automating Pull Request (PR) creation and issue management. Future versions will incorporate AI to assist in generating PR descriptions.

## Features (Current)

*   List open GitHub issues for the current repository.
*   List all (open and closed) GitHub issues using the `-a` flag.
*   Create a new PR with a specified title.
*   Automatically detects the GitHub repository from your local .git configuration.

## Installation & Setup

### For Users (if published on PyPI):

You can install AutoPR using pip (once published):

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
    python run_cli.py ls
    ```
*   **List all issues (open and closed):**
    ```sh
    python run_cli.py ls -a
    ```
*   **Create a new PR:**
    ```sh
    python run_cli.py create --title "Your Amazing PR Title"
    ```

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
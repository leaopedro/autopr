# AutoPR

A CLI tool designed to streamline your GitHub workflow by automating Pull Request (PR) creation and issue management. Future versions will incorporate AI to assist in generating PR descriptions.

## Features (Current)

*   List open GitHub issues for the current repository.
*   List all (open and closed) GitHub issues using the `-a` flag.
*   Create a new PR with a specified title.
*   Automatically detects the GitHub repository from your local .git configuration.

## Installation & Setup

### For Users (if published on PyPI):

You can install AutoPR using pip:

```sh
pip install autopr_cli
```

### For Developers (Local Setup):

1.  Clone the repository:
    ```sh
    git clone <your-repository-url>
    cd autopr
    ```
2.  Create and activate a virtual environment (recommended):
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3.  Install dependencies:
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

## Running Tests

To run the automated tests, use Make:

```sh
make test
```

## To publish a new version (if applicable):

After changes are done, run the following:

1.  Build the package:
    ```sh
    python setup.py sdist bdist_wheel
    ```

2.  Upload:
    ```sh
    twine upload dist/*
    ```
# AutoPR: Your AI-Powered GitHub Assistant

AutoPR is a command-line tool that uses AI to help you with common GitHub tasks like managing issues, writing commit messages, creating pull requests, and even reviewing code. It's like having a smart assistant right in your terminal!

## What Can AutoPR Do For You?

Here's a look at how AutoPR can make your GitHub workflow smoother and faster.

*(Make sure you're in the main directory of your Git project when running these commands!)*

### 1. See What Needs Doing: `autopr ls`

Want to quickly see what issues are open in your project?

*   **See all open issues:**
    ```sh
    autopr ls
    ```
*   **See absolutely *all* issues (open and closed):**
    ```sh
    autopr ls -a
    # or
    autopr ls --all
    ```
    If there's nothing matching your filters, AutoPR will let you know.

### 2. Grab an Issue and Get to Work: `autopr workon <issue_number>`

Ready to tackle an issue? `autopr workon` gets you set up in a flash.

**Command:**
```sh
autopr workon <issue_number> 
# Example: autopr workon 101
```
Replace `<issue_number>` with the actual number of the GitHub issue.

**What it does for you:**

1.  **Finds the Issue:** Looks up the issue on GitHub to get its title.
2.  **Creates a Smart Branch Name:** Makes a new branch like `feature/101-fix-that-tricky-bug` from the issue number and title. (It cleans up the title to make it a good branch name – all lowercase, hyphens for spaces, etc.)
3.  **Switches to Your New Branch:** Runs `git checkout -b ...` so you're ready to code.
4.  **Remembers What You're Working On:** Saves the issue number in `.git/.autopr_current_issue`. This helps other AutoPR commands know the context of your work.

**Example:**
If issue #42 is "Fix login button display error":
```sh
autopr workon 42
```
AutoPR will create and switch to a branch like `feature/42-fix-login-button-display-error` and remember that you're working on issue 42.

### 3. Commit Your Awesome Changes (with AI Help!): `autopr commit`

You've staged your changes (`git add .`), and now it's time to commit. Let AutoPR help you write a great commit message!

**Prerequisites:**
*   You have changes staged for commit.
*   You need an `OPENAI_API_KEY` set in your environment.
    ```sh
    export OPENAI_API_KEY='your_api_key_here' 
    ```
    (Tip: Add this to your `.zshrc` or `.bashrc` so you don't have to set it every time.)

**Command:**
```sh
autopr commit
```

**What it does for you:**

1.  **Checks Your Staged Work:** Looks at what you've staged with `git diff --staged`.
2.  **Asks AI for a Commit Message:** Sends this "diff" to an AI (currently GPT-3.5 Turbo) to suggest a commit message.
3.  **Shows You the Suggestion:** Prints the AI's idea to your console.
4.  **You Decide:** Asks if you want to use it (`y/n`).
    *   **`y` (yes):** AutoPR runs `git commit -m "AI's clever message"` for you.
    *   **`n` (no):** No problem! AutoPR will tell you to commit manually with `git commit`.

**Example:**
After `git add my_amazing_feature.py`:
```sh
autopr commit
```
AutoPR will show you a suggested message. If you like it, hit `y`, and you're committed!

### 4. Create a Pull Request (AI-Assisted Title & Body): `autopr pr`

Ready to share your work? `autopr pr` helps you draft a Pull Request with an AI-generated title and description based on your commits and the original issue.

**Prerequisites:**
*   You've committed your changes to your local branch.
*   You have that `OPENAI_API_KEY` environment variable set.
*   It helps if you started with `autopr workon <issue_number>` so AutoPR can link the PR back to the issue.

**Command:**
```sh
autopr pr [--base <target_branch>]
# Example: autopr pr
# Example: autopr pr --base develop
```
*   `--base <target_branch>`: Tell AutoPR where your PR should merge into. If you don't say, it defaults to `main`.

**What it does for you:**

1.  **Gathers Your Commits:** Looks at all the commits you've made on your current branch since you branched off from `main` (or your specified `--base` branch).
2.  **Remembers the Issue (if you used `workon`):** If you used `autopr workon`, it will try to fetch the original issue's title and description from GitHub.
3.  **Asks AI for a PR Title & Body:** Sends your commit messages (and issue details, if found) to an AI (GPT-3.5 Turbo) to draft a title and body for your PR.
4.  **Shows You the Draft:** Prints the AI's suggested title and body.
5.  **You Decide:** Asks if you want to create the PR on GitHub with this draft (`y/n`).
    *   **`y` (yes):** AutoPR uses `gh pr create ...` to open the PR on GitHub, linking it to the issue if possible.
    *   **`n` (no):** No worries! AutoPR will suggest you create the PR manually.

**Example:**
You've made some commits on your `feature/42-new-login-flow` branch.
```sh
autopr pr 
```
AutoPR will gather your work, ask the AI for a good PR title and body, show them to you, and then create the PR if you say yes!

### 5. Get an AI Code Review: `autopr review <PR_NUMBER>`

Want a second pair of (AI) eyes on a Pull Request? `autopr review` uses AI to analyze the changes and post suggestions directly as comments on GitHub.

**Prerequisites:**
*   You have the `gh` CLI installed and logged in (`gh auth login`).
*   Yep, you need that `OPENAI_API_KEY` again.

**Command:**
```sh
autopr review <PR_NUMBER>
# Example: autopr review 7
```
Replace `<PR_NUMBER>` with the number of the PR you want to review.

**What it does for you:**

1.  **Fetches the PR's Changes:** Uses `gh pr diff <PR_NUMBER>` to get all the code changes.
2.  **AI Analyzes the Code:** Sends the diff to a powerful AI (GPT-4 Turbo Preview) to look for potential improvements or issues.
3.  **Posts Suggestions on GitHub:** If the AI has suggestions, AutoPR posts them as comments directly on the relevant lines of code in the PR on GitHub.
4.  **Tells You What Happened:** Gives you a summary of how many comments it posted.

**Example:**
To get AI feedback on Pull Request #7:
```sh
autopr review 7
```
AutoPR will fetch the PR, let the AI review it, and post comments on GitHub.

## Getting Started: Installation

Ready to try AutoPR?

### For Most Users (Install from PyPI)

The easiest way is with pip:
```sh
pip install autopr_cli
```
Then you can run commands like `autopr ls`.

### For Developers (If you want to contribute or tinker)

1.  **Get the Code:**
    ```sh
    git clone https://github.com/leaopedro/autopr.git
    cd autopr
    ```
2.  **Set up a Virtual Environment (Good Practice!):**
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install Everything Needed:**
    ```sh
    pip install -r requirements.txt 
    ```
    Now you can run commands like `python -m autopr.cli ls`.

## For Developers: Contributing to AutoPR

If you're working on AutoPR itself:

### Running Tests

Make sure everything still works:
```sh
make test
```

### Keeping Code Tidy (Formatting)

We use Black to format our Python code:
```sh
make format
```

### Publishing a New Version (For Maintainers)

We have a `Makefile` to help with releases. You'll need `twine` and your PyPI credentials.

1.  **Update Version:** Change `__version__` in `autopr/__init__.py`.
2.  **Build:** `make build` (creates distributable files in `dist/`)
3.  **Test on TestPyPI (Important!):** `make publish-test`
4.  **Publish for Real on PyPI:** `make publish`
5.  **Full Release (Publish & Tag):** `make release` (does `publish` then tags the version in Git).
    *   **Crucial:** After `make release`, push the tag: `git push origin vX.Y.Z` (or `git push --tags`).

---

*Note: For developer commands like `python -m autopr.cli ...`, you can create an alias in your shell (e.g., in `.zshrc` or `.bashrc`) to make them shorter, like `alias dev-autopr="python -m autopr.cli"`.*

# autopr/ai_service.py
import os
import openai
import re # Import re for regex operations

# Initialize OpenAI client. API key is read from environment variable OPENAI_API_KEY by default.
# It's good practice to handle potential missing key if you want to provide a graceful fallback or error.
# For this iteration, we assume the key is set if this module is used.
try:
    client = openai.OpenAI()
except openai.OpenAIError as e:
    # This might happen if OPENAI_API_KEY is not set or other configuration issues.
    print(f"OpenAI SDK Initialization Error: {e}")
    print("Please ensure your OPENAI_API_KEY environment variable is set correctly.")
    client = None # Set client to None so calls can check


def get_commit_message_suggestion(diff: str) -> str:
    """
    Gets a commit message suggestion from OpenAI based on the provided diff.
    """
    if not client:
        return "[OpenAI client not initialized. Check API key.]"
    if not diff:
        return "[No diff provided to generate commit message.]"

    try:
        prompt_message = (
            f"Generate a sthraightforward, conventional one-line commit message (max 72 chars for the subject line) that best reflects a resume of all the changes"
            f"for the following git diff (read carefully):\n\n```diff\n{diff}\n```\n\n"
            f"The commit message should follow standard conventions, such as starting with a type "
            f"(e.g., feat:, fix:, docs:, style:, refactor:, test:, chore:). You can ignore version updates if they are not relevant to the changes. "
            f"Do not include any other text or symbols or formatting (like '```', '```diff', etc.) in the commit message, just the plain text message and nothing else."
        )

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates commit messages."},
                {"role": "user", "content": prompt_message}
            ],
            max_tokens=100,
            temperature=0.7 # creativity vs. determinism
        )
        suggestion = response.choices[0].message.content.strip()
        # Regex to remove triple backticks (and optional language specifier) or single backticks
        # that surround the entire string. Also handles optional leading/trailing whitespace around them.
        # Pattern: ^\s* (?: (?:```(?:\w+)?\n(.*?)```) | (?:`(.*?)`) ) \s* $
        # This was getting too complex, let's simplify the approach for now.

        # Iteratively strip common markdown code block markers
        # Order matters: longer sequences first
        cleaned_suggestion = suggestion
        # Case 1: ```lang\nCODE\n```
        match = re.match(r"^\s*```[a-zA-Z]*\n(.*?)\n```\s*$", cleaned_suggestion, re.DOTALL)
        if match:
            cleaned_suggestion = match.group(1).strip()
        else:
            # Case 2: ```CODE``` (no lang, no newlines inside)
            match = re.match(r"^\s*```(.*?)```\s*$", cleaned_suggestion, re.DOTALL)
            if match:
                cleaned_suggestion = match.group(1).strip()
        
        # Case 3: `CODE` (single backticks)
        # This should only apply if triple backticks didn't match, 
        # or to clean up remnants if the AI puts single inside triple for some reason.
        # However, to avoid stripping intended inline backticks, only strip if they are the *very* start and end
        # of what's left.
        if cleaned_suggestion.startswith('`') and cleaned_suggestion.endswith('`'):
             # Check if these are the *only* backticks or if they genuinely surround the whole content
            temp_stripped = cleaned_suggestion[1:-1]
            if '`' not in temp_stripped: # If no more backticks inside, it was a simple `code`
                cleaned_suggestion = temp_stripped.strip()
            # else: it might be `code` with `inner` backticks, which is complex, leave as is for now.

        return cleaned_suggestion
    except openai.APIError as e:
        print(f"OpenAI API Error: {e}")
        return "[Error communicating with OpenAI API]"
    except Exception as e:
        print(f"An unexpected error occurred in get_commit_message_suggestion: {e}")
        return "[Error generating commit message]"

def get_pr_description_suggestion(issue_details: dict, commit_messages: list[str]) -> tuple[str, str]:
    """Generates a PR title and body using OpenAI based on issue details and commit messages."""
    if not client:
        return "[OpenAI client not initialized. Check API key.]", "[OpenAI client not initialized. Check API key.]"

    if not issue_details:
        return "[No issue details provided]", "[No issue details provided]"
    if not commit_messages:
        return "[No commit messages provided]", "[No commit messages provided]"

    try:
        # Construct a detailed prompt for the AI
        issue_title = issue_details.get('title', 'N/A')
        issue_body = issue_details.get('body', 'N/A')
        issue_number = issue_details.get('number', 'N/A')
        # Format labels nicely if they exist
        labels = [label['name'] for label in issue_details.get('labels', [])]
        labels_str = f"Labels: {', '.join(labels)}" if labels else "Labels: None"

        commits_str = "\n".join(f"- {msg}" for msg in commit_messages)

        prompt = (
            f"Given the following GitHub issue and commit messages, please generate a suitable Pull Request title and body.\n\n"
            f"Issue #{issue_number}: {issue_title}\n"
            f"{labels_str}\n"
            f"Issue Description:\n---\n{issue_body}\n---\n\n"
            f"Commit Messages on the branch:\n---\n{commits_str}\n---\n\n"
            f"Based on all the above, suggest a concise PR title (around 70 characters or less) and a comprehensive PR body.\n"
            f"The PR body should summarize the changes and how they address the issue. It can reference the issue number (e.g., Closes #{issue_number}). "
            f"Format the PR body using Markdown.\n\n"
            f"Return ONLY the PR title on the first line, then a single newline, then the PR body. "
            f"Do not include any other explanatory text before the title or after the body."
        )

        response = client.chat.completions.create(
            model="gpt-4-turbo", # Or your preferred model for more complex generation
            messages=[
                {"role": "system", "content": "You are an expert assistant that generates Pull Request titles and bodies."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500, # Allow more tokens for PR body
            temperature=0.7
        )

        raw_suggestion = response.choices[0].message.content.strip()
        
        # Split the response into title and body
        # Expecting title on the first line, then a newline, then body
        parts = raw_suggestion.split('\n', 1)
        suggested_title = parts[0].strip()
        suggested_body = parts[1].strip() if len(parts) > 1 else ""

        # Basic cleaning for title (similar to commit message cleaning, just in case)
        if suggested_title.startswith("```"):
            title_match = re.match(r"^\s*```[a-zA-Z]*\n(.*?)\n```\s*$", suggested_title, re.DOTALL) or \
                          re.match(r"^\s*```(.*?)```\s*$", suggested_title, re.DOTALL)
            if title_match: suggested_title = title_match.group(1).strip()
        if suggested_title.startswith('`') and suggested_title.endswith('`') and suggested_title.count('`') == 2:
            suggested_title = suggested_title[1:-1]

        # The body is Markdown, so we don't want to strip its formatting aggressively.
        # However, if the entire body is wrapped in ```, we might strip that.
        if suggested_body.startswith("```") and suggested_body.endswith("```"):
            # Check if it's a code block with a language specifier on the first line
            body_match_lang = re.match(r"^```[a-zA-Z]*\n(.*?)\n```$", suggested_body, re.DOTALL)
            if body_match_lang:
                suggested_body = body_match_lang.group(1).strip() # Keep inner content
            else:
                # Check if it's just ```BODY```
                body_match_simple = re.match(r"^```(.*?)```$", suggested_body, re.DOTALL)
                if body_match_simple:
                    suggested_body = body_match_simple.group(1).strip()
            # If neither, it might be intentional triple backticks, leave them.

        return suggested_title, suggested_body

    except openai.APIError as e:
        print(f"OpenAI API Error during PR suggestion: {e}")
        return "[Error communicating with OpenAI API for PR]", "[Error communicating with OpenAI API for PR]"
    except Exception as e:
        print(f"An unexpected error occurred in get_pr_description_suggestion: {e}")
        return "[Error generating PR suggestion]", "[Error generating PR suggestion]" 
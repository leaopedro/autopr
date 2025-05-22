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
    """
    Placeholder for AI service call to get PR title and body suggestion.
    """
    # In a real scenario, this would call an LLM API.
    return "[AI Suggested PR Title]", "[AI Suggested PR Body]" 
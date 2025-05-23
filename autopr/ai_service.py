# autopr/ai_service.py
import os
import openai
import re  # Import re for regex operations
import json

# Initialize OpenAI client. API key is read from environment variable OPENAI_API_KEY by default.
# It's good practice to handle potential missing key if you want to provide a graceful fallback or error.
# For this iteration, we assume the key is set if this module is used.
try:
    client = openai.OpenAI()
except openai.OpenAIError as e:
    # This might happen if OPENAI_API_KEY is not set or other configuration issues.
    print(f"OpenAI SDK Initialization Error: {e}")
    print("Please ensure your OPENAI_API_KEY environment variable is set correctly.")
    client = None  # Set client to None so calls can check


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
                {
                    "role": "system",
                    "content": "You are a helpful assistant that generates commit messages.",
                },
                {"role": "user", "content": prompt_message},
            ],
            max_tokens=100,
            temperature=0.7,  # creativity vs. determinism
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
        match = re.match(
            r"^\s*```[a-zA-Z]*\n(.*?)\n```\s*$", cleaned_suggestion, re.DOTALL
        )
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
        if cleaned_suggestion.startswith("`") and cleaned_suggestion.endswith("`"):
            # Check if these are the *only* backticks or if they genuinely surround the whole content
            temp_stripped = cleaned_suggestion[1:-1]
            if (
                "`" not in temp_stripped
            ):  # If no more backticks inside, it was a simple `code`
                cleaned_suggestion = temp_stripped.strip()
            # else: it might be `code` with `inner` backticks, which is complex, leave as is for now.

        return cleaned_suggestion
    except openai.APIError as e:
        print(f"OpenAI API Error: {e}")
        return "[Error communicating with OpenAI API]"
    except Exception as e:
        print(f"An unexpected error occurred in get_commit_message_suggestion: {e}")
        return "[Error generating commit message]"


def get_pr_description_suggestion(
    issue_details: dict, commit_messages: list[str]
) -> tuple[str, str]:
    """
    Placeholder for AI service call to get PR title and body suggestion.
    """
    # In a real scenario, this would call an LLM API.
    return "[AI Suggested PR Title]", "[AI Suggested PR Body]"


def get_pr_review_suggestions(pr_changes: str) -> list[dict[str, str | int]]:
    """
    Analyzes PR changes and generates review suggestions.

    Args:
        pr_changes: The diff of the PR changes.

    Returns:
        A list of dictionaries containing review suggestions, each with:
        - path: The path to the file being commented on
        - line: The line number to comment on
        - suggestion: The review suggestion text
    """
    try:
        # Construct the prompt for the AI
        prompt = f"""You are a code reviewer. Analyze the following PR changes and provide specific, actionable suggestions for improvement.
For each suggestion, provide:
1. The file path
2. The line number to comment on
3. A clear, constructive suggestion

Focus on:
- Code quality and readability
- Potential bugs or edge cases
- Performance considerations
- Best practices
- Documentation needs

Format each suggestion as a JSON object with 'path', 'line', and 'suggestion' fields.
Return a JSON array of these objects.

PR Changes:
{pr_changes}

Suggestions:"""

        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a code reviewer providing specific, actionable suggestions for PR changes. Return only valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        # Extract and parse the response
        suggestions_text = response.choices[0].message.content.strip()

        # Clean up the response (remove markdown code blocks if present)
        suggestions_text = re.sub(r"^```(?:json)?\n", "", suggestions_text)
        suggestions_text = re.sub(r"\n```$", "", suggestions_text)

        # Parse the JSON response
        suggestions = json.loads(suggestions_text)

        # Validate the suggestions format
        if not isinstance(suggestions, list):
            print("Error: AI response was not a list of suggestions")
            return []

        valid_suggestions = []
        for suggestion in suggestions:
            if not isinstance(suggestion, dict):
                continue

            # Check for required fields
            if not all(key in suggestion for key in ["path", "line", "suggestion"]):
                continue

            # Validate types
            if not isinstance(suggestion["path"], str):
                continue
            if not isinstance(suggestion["line"], int):
                continue
            if not isinstance(suggestion["suggestion"], str):
                continue

            valid_suggestions.append(suggestion)

        return valid_suggestions

    except json.JSONDecodeError as e:
        print(f"Error parsing AI response as JSON: {e}")
        return []
    except Exception as e:
        print(f"Error generating PR review suggestions: {e}")
        return []

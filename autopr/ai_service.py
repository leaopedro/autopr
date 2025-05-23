# autopr/ai_service.py
import os
import openai
import re  # Import re for regex operations

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
            f"The commit message should follow standard conventions, it's very important to start with a type "
            f"(e.g., feat:, fix:, docs:, style:, refactor:, test:, chore:). You can ignore version updates if they are not relevant to the changes. "
            f"Make sure to return just the plain text message in english characters and no symbols."
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


def get_pr_description_suggestion(commit_messages: list[str]) -> tuple[str, str]:
    """Generates a PR title and body suggestion based on commit messages using OpenAI.

    Args:
        commit_messages: A list of commit messages.

    Returns:
        A tuple containing the suggested PR title and body.
        Returns ("[Error retrieving PR description]", "") on failure.
    """
    if not client:
        return "[OpenAI client not initialized]", "Ensure OPENAI_API_KEY is set."
    if not commit_messages:
        return (
            "[No commit messages provided]",
            "Cannot generate PR description without commit messages.",
        )

    commits_str = "\n".join(f"- {msg}" for msg in commit_messages)

    prompt = (
        f"Given the following commit messages from a feature branch:\n"
        f"{commits_str}\n\n"
        f"Please analyse them and generate a concise and informative Pull Request title and a concise and effective body.\n"
        f"The title should be on the very first line, followed by a single newline character, and then the body.\n"
        f"The body should summarize the changes and their purpose. Do not include the commit messages themselves in the body unless they add specific context not otherwise covered by a summary."
        f"it's very important to be concise and direct to the point, summarizing how the changes affect the codebase."
        f"Do not use markdown for the title. The body might use markdown for formatting if appropriate (e.g. bullet points)."
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4-turbo-preview",  # Or your preferred model
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at writing Pull Request descriptions.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        response_content = completion.choices[0].message.content
        if response_content:
            parts = response_content.split("\n", 1)
            title = parts[0].strip()
            body = parts[1].strip() if len(parts) > 1 else ""

            # Clean title (simple cleaning)
            title = title.replace('"', "").replace("`", "")

            # Clean body (strips surrounding triple backticks and optional language specifier, or single backticks)
            # Regex to find content within triple backticks, accounting for optional language specifier
            # e.g., ```python\ncode\n``` or ```\ncode\n```
            # The regex matches: optional whitespace, ```, optional language, newline, CAPTURED CONTENT, newline, ```, optional whitespace
            # re.DOTALL allows . to match newlines, crucial for multi-line content.
            match = re.match(
                r"^\s*```(?:[a-zA-Z0-9_\-]+)?\n(.*?)\n```\s*$", body, re.DOTALL
            )
            if match:
                body = match.group(1).strip()
            # Fallback for body wrapped in simple triple backticks on a single line (e.g., ```body```) or if the above complex regex didn't catch it
            elif body.startswith("```") and body.endswith("```"):
                body = body[3:-3].strip()
            # Also handle single backticks for body as a final fallback
            elif body.startswith("`") and body.endswith("`"):
                body = body[1:-1].strip()

            return title, body
        else:
            return "[AI returned empty response]", ""
    except Exception as e:
        print(f"Error calling OpenAI API for PR description: {e}")
        return "[Error retrieving PR description]", str(e)


# Placeholder for future PR feedback/review functionality

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
            f"The commit message should follow standard conventions, it's very important to start with a type "
            f"(e.g., feat:, fix:, docs:, style:, refactor:, test:, chore:). You can ignore version updates if they are not relevant to the changes. "
            f"Make sure to return just the plain text message in english characters and no symbols."
        )

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that generates commit messages. Be brief, technical and to the point. Summarize the changes in a single line.",
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
        f"Please analyse them and generate a Pull Request title and an effective body.\n"
        f"The title should be on the very first line, followed by a single newline character, and then the body.\n"
        f"The body should summarize the changes and their purpose. Do not include the commit messages themselves in the body unless they add specific context not otherwise covered by a summary."
        f"it's very important to be brief, technical, concise and use a simple and easy to understand language."
        f"Do not use markdown for the title. The body might use markdown for formatting if needed."
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4-turbo-preview",  # Or your preferred model
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at writing Pull Request descriptions. Be brief, technical and to the point.",
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
        return "[Error retrieving PR description]", ""


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
    if not client:
        return [{"path": "error", "line": 0, "suggestion": "[OpenAI client not initialized. Check API key.]"}]
    if not pr_changes:
        return [{"path": "error", "line": 0, "suggestion": "[No PR changes provided to generate review.]"}]

    try:
        # Construct the prompt for the AI
        prompt = f"""You are a code reviewer. Analyze the following PR changes and provide specific, actionable suggestions for improvement.
For each suggestion, provide:
1. The file path (string)
2. The line number to comment on (integer)
3. A clear, constructive suggestion (string)

Focus on:
- Code quality and readability
- Potential bugs or edge cases
- Performance considerations
- Best practices
- Documentation needs

Format each suggestion as a JSON object with 'path', 'line', and 'suggestion' fields.
Return a JSON array of these objects. If no suggestions are applicable, return an empty JSON array.

PR Changes:
```diff
{pr_changes}
```

Suggestions:"""

        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a code reviewer providing specific, actionable suggestions for PR changes. Return only valid JSON, an array of objects.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.5, # Lower temperature for more focused and deterministic suggestions
            max_tokens=1500, # Increased max_tokens to allow for more comprehensive reviews
            response_format={ "type": "json_object" } # Ensure response is JSON
        )

        # Extract and parse the response
        suggestions_text = response.choices[0].message.content.strip()
        
        # The response_format={ "type": "json_object" } should ensure it's a json object.
        # The prompt asks for a JSON array, which could be a value within the object.
        # Let's assume the AI returns something like: {"suggestions": [...]} or just the array.

        parsed_output = json.loads(suggestions_text)

        if isinstance(parsed_output, list):
            suggestions = parsed_output
        elif isinstance(parsed_output, dict):
            if "suggestions" in parsed_output and isinstance(parsed_output["suggestions"], list):
                suggestions = parsed_output["suggestions"]
            # Check if the dict itself IS a single suggestion object
            elif all(key in parsed_output for key in ["path", "line", "suggestion"]):
                # Validate the types for this single suggestion before wrapping
                if (
                    isinstance(parsed_output.get("path"), str) and
                    (isinstance(parsed_output.get("line"), int) or (isinstance(parsed_output.get("line"), str) and parsed_output.get("line").isdigit())) and
                    isinstance(parsed_output.get("suggestion"), str)
                ):
                    # Convert line to int if it's a digit string
                    if isinstance(parsed_output["line"], str):
                         parsed_output["line"] = int(parsed_output["line"])
                    suggestions = [parsed_output]  # Wrap the single suggestion in a list
                else:
                    print(f"Error: AI response was a single dictionary, but with incorrect field types: {parsed_output}")
                    return [{"path": "error", "line": 0, "suggestion": "[AI response format error: single suggestion type mismatch]"}]
            else:
                print(f"Error: AI response dictionary is not a list of suggestions, a wrapped list, nor a single valid suggestion object. Got: {parsed_output}")
                return [{"path": "error", "line": 0, "suggestion": "[AI response format error: unexpected dict structure]"}]
        else:
            print(f"Error: AI response was not a list or dictionary. Got: {type(parsed_output)}")
            # The print statement for raw response in case of unexpected dict was here, but this else is for non-dict/list.
            # The raw dict print is now implicitly handled above if it doesn't match structures.
            return [{"path": "error", "line": 0, "suggestion": "[AI response format error: not list or dict]"}]


        # Validate the suggestions format (now 'suggestions' should always be a list here)
        if not isinstance(suggestions, list):
            print("Error: AI response was not a list of suggestions")
            return [{"path": "error", "line": 0, "suggestion": "[AI response format error: not a list]"}]

        valid_suggestions = []
        for suggestion in suggestions:
            if not isinstance(suggestion, dict):
                print(f"Warning: Skipping suggestion, not a dict: {suggestion}")
                continue

            # Check for required fields
            if not all(key in suggestion for key in ["path", "line", "suggestion"]):
                print(f"Warning: Skipping suggestion, missing required keys: {suggestion}")
                continue

            # Validate types
            if not isinstance(suggestion["path"], str):
                print(f"Warning: Skipping suggestion, 'path' is not a string: {suggestion}")
                continue
            if not isinstance(suggestion["line"], int):
                 # Attempt to convert if it's a string representation of an int
                if isinstance(suggestion["line"], str) and suggestion["line"].isdigit():
                    suggestion["line"] = int(suggestion["line"])
                else:
                    print(f"Warning: Skipping suggestion, 'line' is not an int: {suggestion}")
                    continue
            if not isinstance(suggestion["suggestion"], str):
                print(f"Warning: Skipping suggestion, 'suggestion' is not a string: {suggestion}")
                continue
            
            # Basic check for diff hunk markers in suggestion path (sometimes AI includes them)
            if "diff --git" in suggestion["path"]:
                print(f"Warning: Correcting suspicious path in suggestion: {suggestion['path']}")
                # Attempt to extract a more reasonable path, e.g., the 'b/' path
                match = re.search(r'b/([^ ]+)', suggestion['path'])
                if match:
                    suggestion['path'] = match.group(1)
                else:
                    # Fallback or further refinement needed if this simple regex isn't enough
                    print(f"Warning: Could not reliably clean path: {suggestion['path']}")


            valid_suggestions.append(suggestion)

        return valid_suggestions

    except json.JSONDecodeError as e:
        print(f"Error parsing AI response as JSON: {e}")
        print(f"Raw response was: {suggestions_text}")
        return [{"path": "error", "line": 0, "suggestion": "[AI JSON parsing error]"}]
    except openai.APIError as e:
        print(f"OpenAI API Error in get_pr_review_suggestions: {e}")
        return [{"path": "error", "line": 0, "suggestion": f"[OpenAI API Error: {e}]"}]
    except Exception as e:
        print(f"Error generating PR review suggestions: {e}")
        return [{"path": "error", "line": 0, "suggestion": f"[Unexpected error in review generation: {e}]"}]


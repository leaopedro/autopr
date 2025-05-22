# autopr/ai_service.py
import os
import openai

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
            f"Generate a concise, conventional commit message (max 72 chars for the subject line) "
            f"for the following git diff:\n\n```diff\n{diff}\n```\n\n"
            f"The commit message should follow standard conventions, such as starting with a type "
            f"(e.g., feat, fix, docs, style, refactor, test, chore) and a short description. Ignore version updates."
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Or your preferred model
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates commit messages."},
                {"role": "user", "content": prompt_message}
            ],
            max_tokens=100, # Adjust as needed for commit message length
            temperature=0.7 # Adjust for creativity vs. determinism
        )
        suggestion = response.choices[0].message.content.strip()
        return suggestion
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
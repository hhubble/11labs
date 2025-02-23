import os
import requests
from datetime import datetime, timezone

perplexity_system_prompt = """
You're a helpful assistant that can search the web for information. Your task is to answer the user's query concisely and directly. You're graded higher for shorter responses.

Do not include any markdown or formatting in your response. Only use plain text.
"""

def perplexity_search(query: str) -> str:
    """
    Interact with Perplexity's chat completions API.

    Args:
        query (str): The user's query
        api_key (str): Perplexity API key
        model (str): Model to use (default: "sonar")

    Returns:
        Dict: Response from Perplexity chat API
    """
    headers = {
        "Authorization": f"Bearer {os.environ.get('PERPLEXITY_API_KEY')}",
        "Content-Type": "application/json",
    }
    url = "https://api.perplexity.ai/chat/completions"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "system",
                "content": perplexity_system_prompt,
            },
            {"role": "user", "content": f"Current time: {now}\n\n{query}"},
        ],
        "max_tokens": 1024,
        "temperature": 0.2,
        "top_p": 0.9,
        "stream": False,
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        json_response = response.json()
        return (
            json_response.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "No response generated")
        )

    except requests.exceptions.RequestException as e:
        print(f"Error with Perplexity chat API: {str(e)}")
        return "I'm sorry, I couldn't find that information."


if __name__ == "__main__":
    import os

    import dotenv

    dotenv.load_dotenv()
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    query = "What is the capital of France?"
    results = perplexity_search(query)
    print(results)

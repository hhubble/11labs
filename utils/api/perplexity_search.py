from typing import Dict, List, Optional

import requests


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

    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "Be very concise and don't use markdown. Just return the pure text.",
            },
            {"role": "user", "content": query},
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

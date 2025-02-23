import asyncio
from typing import List

import litellm
from pydantic import BaseModel

from utils.api.google import GoogleAPI


async def generate_summary(transcript: str) -> str:
    """
    Generate a summary of the transcript using Groq LLM.
    """
    prompt = """You are a professional meeting summarizer. Given the following meeting transcript, create a concise summary that focuses on:
- Specific decisions made
- Concrete action items and deadlines
- Key numerical data or metrics discussed
- Important updates or changes
- Critical issues raised

Focus on precise details rather than broad themes. Be direct and specific. Ensure you don't use markdown, just use normal text.

Meeting Transcript:
{transcript}

Summary:"""

    response = await litellm.acompletion(
        model="groq/llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt.format(transcript=transcript)}],
        temperature=0.2,
    )

    return response.choices[0].message.content


class ActionItems(BaseModel):
    items: List[str]


async def generate_action_items(transcript: str) -> list[str]:
    """
    Generate a list of action items and todos from the transcript using Groq LLM.
    Returns a list of strings.
    """
    prompt = """From the following meeting transcript, extract a clear list of action items. For each item include:
- The specific task to be completed
- Who is responsible (if mentioned)
- Deadline or timeframe (if mentioned)

Format each item as: "Task description (owner if mentioned, deadline if mentioned)"

The key should be 'action_items'

Return ONLY a JSON array of strings, with no additional explanation.

Meeting Transcript:
{transcript}"""

    response = await litellm.acompletion(
        model="groq/llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": prompt.format(transcript=transcript)},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    import json

    result = json.loads(response.choices[0].message.content)
    return result.get("action_items", [])


async def send_post_meeting_email(full_transcript):
    from utils.post_meeting_items import generate_action_items, generate_summary

    summary, action_items = await asyncio.gather(
        generate_summary(full_transcript), generate_action_items(full_transcript)
    )

    # Format action items with proper HTML
    formatted_action_items = "\n".join(
        f"<div style='margin-bottom: 12px;'>• {item}</div>" for item in action_items
    )

    email_body = f"""
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #1d1d1f; font-weight: 500; font-size: 24px; margin-bottom: 24px;">Meeting Summary</h2>
    <div style="background: #f5f5f7; border-radius: 12px; padding: 24px; margin-bottom: 32px;">
        {summary}
    </div>

    <h2 style="color: #1d1d1f; font-weight: 500; font-size: 24px; margin-bottom: 24px;">Action Items</h2>
    <div style="background: #f5f5f7; border-radius: 12px; padding: 24px; margin-bottom: 32px;">
        {formatted_action_items}
    </div>

    <p style="color: #666; font-style: italic; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; text-align: center; font-size: 0.9em;">
        Generated with ❤️ at the ElevenLabs x a16z Hackathon in SF
    </p>
</body>
</html>
"""

    google_api = GoogleAPI()
    google_api.authenticate()
    google_api.send_email(
        to="wylansford@gmail.com",
        subject="Meeting Summary & Action Items",
        body=email_body,
        is_html=True,
    )


if __name__ == "__main__":
    asyncio.run(
        send_post_meeting_email(
            "This is a full transcript. Over the day we need to send emails and go to the studio to finish all of our pottery work"
        )
    )

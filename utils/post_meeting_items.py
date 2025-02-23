import asyncio

import litellm
from api.google import GoogleAPI


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

Focus on precise details rather than broad themes. Be direct and specific.

Meeting Transcript:
{transcript}

Summary:"""

    response = await litellm.acompletion(
        model="groq/llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt.format(transcript=transcript)}],
        temperature=0.2,
    )

    return response.choices[0].message.content


async def generate_action_items(transcript: str) -> str:
    """
    Generate a list of action items and todos from the transcript using Groq LLM.
    """
    prompt = """You are an action item extractor. From the following meeting transcript, create a clear list of action items. Focus exclusively on:
- Specific tasks that need to be completed
- Who is responsible for each task (if mentioned)
- Deadlines or timeframes (if mentioned)
- Concrete deliverables
- Follow-up items

Format each action item as a bullet point starting with "TODO:". If an owner or deadline is mentioned, include them in parentheses.

Do not include:
- General discussion points
- Concepts or themes
- Past accomplishments
- Information sharing without actions

Meeting Transcript:
{transcript}

Action Items:"""

    response = await litellm.acompletion(
        model="groq/llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt.format(transcript=transcript)}],
        temperature=0.2,  # Lower temperature for more focused, consistent output
    )

    return response.choices[0].message.content


async def send_post_meeting_email(full_transcript):
    from utils.post_meeting_items import generate_action_items, generate_summary

    summary, action_items = await asyncio.gather(
        generate_summary(full_transcript), generate_action_items(full_transcript)
    )

    print(f"Summary: {summary}")
    print(f"Action Items: {action_items}")

    google_api = GoogleAPI()
    google_api.authenticate()
    google_api.send_email(
        to="haz@pally.com",
        subject="Meeting Action Items",
        body=f"Summary: {summary}\nAction Items: {action_items}",
    )


if __name__ == "__main__":
    asyncio.run(
        send_post_meeting_email(
            "This is a full transcript. Over the day we need to send emails and go to the studio to finish all of our pottery work"
        )
    )

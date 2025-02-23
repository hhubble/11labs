import litellm


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

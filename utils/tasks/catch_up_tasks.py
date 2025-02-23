import os

import litellm


async def handle_catch_me_up(transcript: str) -> None:
    catch_up_prompt = """You are a helpful assistant that creates extremely concise meeting summaries. 
    Focus only on the key decisions and major points that a colleague would care about.
    Write like a human would message their coworker - be casual but professional.
    Limit your response to 2 sentences maximum.
    Don't use phrases like "In this meeting" or "The discussion covered" - just get straight to the point."""

    messages = [
        {
            "role": "system",
            "content": catch_up_prompt,
        },
        {
            "role": "user",
            "content": transcript,
        },
    ]

    response = await litellm.acompletion(
        model="groq/mixtral-8x7b-32768",  # or your preferred model
        messages=messages,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    return response.choices[0].message.content


import asyncio

if __name__ == "__main__":
    result = asyncio.run(
        handle_catch_me_up("""Alice: Hi everyone, thanks for joining today's product strategy meeting.
    
    Bob: Thanks Alice. I've prepared the Q3 roadmap slides.
    
    Alice: Great. Our main goal today is to finalize the feature priorities and discuss the new pricing model.
    
    Carol: I've analyzed competitor pricing. Most are charging $20-30 per user monthly for similar features.
    
    Bob: Based on our cost analysis, I propose we start at $25/user/month for the basic tier.
    
    Alice: Makes sense. What about the enterprise tier?
    
    Carol: Enterprise should be $45/user/month with added security features and priority support.
    
    Dave: My team can deliver the security features by end of Q3, but we'll need to hire two more engineers.
    
    Alice: Approved. Let's post those job listings this week.
    
    Bob: For feature priorities, I suggest we focus on SSO integration first, then the API improvements.
    
    Carol: Agreed. Our enterprise customers have been asking for SSO the most.
    """)
    )
    print(result)

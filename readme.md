## Inspiration

Meeting bots are shit. They're static. No one likes them. They just join the meeting and take up space. Yes, the transcription is useful, but the user experience is bad.

But what if they could do more than just take notes? What if they were interactive, could actually *participate* in the meeting, and even take action? Now they would be worth the space they take up…

## What it does

"Hey ElevenLabs..." is an in-meeting AI agent/executive assistant that is more than just a note-taker; it's a participant. You can call on it at anytime with "Hey ElevenLabs..." and the agent can respond, take action, and help all the participants stay present and in-flow.

Specific tasks the agent can do include: search the web, create a linear task, create a note in notion, send an email, create a calendar event, brainstorm ideas, catch you up on the discussion so far, record action items, record the full transcription, and even order stuff on amazon.

It responds and takes action immediately, with almost zero latency.

## How we built it

We created a google profile for the bot ([elevenlabsbot@gmail.com](mailto:elevenlabsbot@gmail.com)), which uses Selenium to join your meetings. Then we record and stream the ongoing device audio and transcribe (speech-to-text) with Deepgram via an ongoing WebSocket. We utilise the Deepgram 'is_final' flag to know when the user stops speaking and send each chunk to the agent for processing.

The agent decides if it should take action, request more information, or respond directly. We use llama-3.3-70b-versatile on Groq for fast inference. We then use ElevenLabs to turn the text response into speech, and feed this into the bot's microphone in the meeting.

We knew latency would be key, so we used PostHog to track LLM observability, and ensure the whole loop (record > transcribe > agent > respond > act) takes less than 1s.

## Challenges we ran into

The key issue was managing latency. A lot of our time went into ensuring the whole pipeline streamed as much as possible, and used tools like WebSockets to manage this.

Another challenge was creating the meeting bot itself. Google doesn't have an API for this so we had to build a reactive web agent that could log in to google and join the meeting autonomously without being blocked by Google's anti-bot protections.

One last issue was that because we're streaming so much, we had to ensure the agent knew when to respond vs when it was already taking action, or else it would often answer the same question multiple times. We dealt with this through efficient state and bypass management.

## Accomplishments that we're proud of

- Integrating so many different tools and actions: Gmail, Google Calendar, Notion, Linear, Perplexity, Transcriptions, Action Items, Brainstorming, catch-me-up, and more.
- Keeping latency so low, so it feels responsive and dynamic to the users' needs.

## What we learned

We learned a ton about creating low-latency agents, websockets, dealing with audio files, function calling, agent architecture and creating an autonomous web agent.

## What's next for "Hey ElevenLabs..."

We think this has a lot of real-world value, and so we plan to package this up into an opensource product that anyone can use for themselves. Technically the key requirement remaining to do this is to ensure the bot can run on a virtual machine, access the users' calendar, and join meetings directly. We would also like to give a face to the agent, using HeyGen or similar.

import asyncio
from datetime import datetime, timedelta

from google_actions import GoogleAPI

link = "pizza-demo-delight.lovable.app"


async def schedule_send_message(message: str, user_id: str) -> None:
    # Wait for 2 minutes
    # Such a shitty way to do this, but it works for the demo :D
    await asyncio.sleep(25)  # 120 seconds = 2 minutes

    print("Sending email...")
    # Initialize Google API and authenticate
    google_api = GoogleAPI()
    google_api.authenticate()

    # Send the email
    google_api.send_email(
        to=user_id,  # Assuming user_id is the email address
        subject="Website Complete!",
        body=message,
    )


if __name__ == "__main__":
    # Example usage:
    asyncio.run(
        schedule_send_message(
            f"Hey! I finished the website. Check it out here: {link}",
            "wylansford@gmail.com",
        )
    )

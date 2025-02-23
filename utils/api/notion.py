from notion_client import Client
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize the Notion client
notion = Client(auth=os.environ["NOTION_TOKEN"])


def create_note(title: str, content: str) -> dict:
    """
    Create a new note in a Notion database
    
    Args:
        title (str): Title of the note
        content (str): Content of the note
        database_id (str): ID of the Notion database to add the note to
        
    Returns:
        dict: Response from Notion API containing the created page details
    """
    new_page = {
        "parent": {"database_id": os.environ["NOTION_DATABASE_ID"]},
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            "Created": {
                "date": {
                    "start": datetime.now(timezone.utc).isoformat()
                }
            }
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "text": {
                                "content": content
                            }
                        }
                    ]
                }
            }
        ]
    }
    
    return notion.pages.create(**new_page)

if __name__ == "__main__":
    create_note("Test Note", "This is a test note")

import os

import requests

TEAM_ID = "327a3776-ea3d-4af0-a7f4-6a0bc8dd8dbf"


def create_linear_issue(
    title: str, description: str, priority: int = None, due_date: str = None
) -> dict:
    """
    Create a new Linear issue using the GraphQL API.

    Args:
        api_key (str): Linear API key for authentication
        team_id (str): ID of the team to create the issue in
        title (str): Title of the issue
        description (str, optional): Description of the issue in markdown format
        priority (int, optional): Priority level (0-4, where 1 is urgent, 2 is high, 3 is normal, 4 is low)
        due_date (str, optional): Due date in ISO 8601 format (e.g., "2024-03-25")

    Returns:
        dict: Response containing the created issue data if successful
    """
    url = "https://api.linear.app/graphql"

    # Construct the mutation query
    mutation = """
    mutation IssueCreate($input: IssueCreateInput!) {
        issueCreate(input: $input) {
            success
            issue {
                id
                title
                description
            }
        }
    }
    """

    # Prepare the variables for the mutation
    variables = {
        "input": {
            "teamId": TEAM_ID,
            "title": title,
        }
    }

    # Add optional parameters if provided
    if description:
        variables["input"]["description"] = description
    if priority is not None:
        variables["input"]["priority"] = priority
    if due_date:
        variables["input"]["dueDate"] = due_date

    # Prepare the request headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": os.environ.get("LINEAR_API_KEY"),
    }

    # Make the request
    response = requests.post(url, headers=headers, json={"query": mutation, "variables": variables})

    # Return the response data
    return response.json()  # Return the response data


def get_linear_teams() -> dict:
    """
    Get all teams from Linear using the GraphQL API.

    Returns:
        dict: Response containing the teams data if successful
    """
    url = "https://api.linear.app/graphql"

    # Construct the query
    query = """
    query Teams {
        teams {
            nodes {
                id
                name
            }
        }
    }
    """

    # Prepare the request headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": os.environ.get("LINEAR_API_KEY"),
    }

    # Make the request
    response = requests.post(url, headers=headers, json={"query": query})

    # Return the response data
    return response.json()


if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()
    # # Example usage
    # teams_result = get_linear_teams()
    # if teams_result.get("data", {}).get("teams", {}).get("nodes"):
    #     print("Teams retrieved successfully!")
    #     for team in teams_result["data"]["teams"]["nodes"]:
    #         print(f"Team: {team['name']}, ID: {team['id']}")
    # else:
    #     print("Failed to get teams:", teams_result.get("errors"))

    # Original example usage
    title = "New bug report"
    description = "Bug found in login flow"

    result = create_linear_issue(title, description, priority=1, due_date="2025-03-25")
    if result.get("data", {}).get("issueCreate", {}).get("success"):
        print("Issue created successfully!")
        print(f"Issue ID: {result['data']['issueCreate']['issue']['id']}")
    else:
        print("Failed to create issue:", result.get("errors"))

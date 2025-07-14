from bs4 import BeautifulSoup

from dotenv import load_dotenv

import requests

import argparse

import httpx

import os

import threading

load_dotenv()

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/58.0.3029.110 Safari/537.36"
    )
}

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def extract_userdata(username: str):
    """
    Purpose: Scraps the userdata from https://www.reddit.com/user/{username}/
    Args: username (str)
    Returns: scraped data (str)
    """

    print(f"extracting userprofile of {username}")

    url: str = f"https://www.reddit.com/user/{username}/"

    try:
        result = requests.get(url, headers=headers)

        soup = BeautifulSoup(result.text, "html.parser")
        data = soup.find_all("div", class_="subgrid-container")
        with open("test.txt", "w") as f:
            f.write(str(data))
        return str(data)
    except Exception as e:
        return f"Failed to fetch {username} data with error {e}"


def build_prompt(username):
    userdata = extract_userdata(username=username)
    print("prompt building")
    return f"""
Analyze the user and following Reddit posts and
comments by user '{username}' and build a detailed user persona.

Include:
- Age range
- Gender
- Occupation
- Interests
- Personality traits
- Political or philosophical leanings
- Writing style or tone
- Preferred subreddits
- Other relevant characteristics

Text:
{userdata}
"""


def get_llm_analyzed(prompt: str, model: str = "deepseek/deepseek-r1-0528"):
    """
    Purpose: communicates with model available on openrouter
    Args: prompt (str), model (str): deepseek/deepseek-r1-0528
    Returns: llm generated user persona
    """
    if not OPENROUTER_API_KEY:
        return "Error: OPENROUTER_API_KEY not found in environment variables"
    
    print("processing user information in llm, it might take some time")

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "RedditPersonaBuilder"
    }

    if not model:
        model = "deepseek/deepseek-r1-0528"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You're an expert in user behavior profiling."
            },
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2000,
        "temperature": 0.7
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        print(f"HTTP Status Error: {e.response.status_code}")
        print(f"Response text: {e.response.text}")
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        print(f"Request Error: {e}")
        return f"Request failed: {e}"
    except Exception as e:
        print(f"Unexpected error: {e}")
        return f"Unexpected error: {e}"


def create_file(data: str, username: str):
    """
    Purpose: Creates txt file with by username and adds data to it
    Args: data (str), username (str)
    """

    os.makedirs("out", exist_ok=True)

    txtfilename = f"out/persona_{username}.txt"
    mdfilename = f"out/persona_{username}.md"

    def write_txt_file():
        with open(txtfilename, "w", encoding="utf-8") as file:
            file.write(data)
        print(f"{txtfilename} created successfully")

    def write_md_file():
        with open(mdfilename, "w", encoding="utf-8") as file:
            file.write(data)
        print(f"{mdfilename} created successfully")

    txt_thread = threading.Thread(target=write_txt_file)
    md_thread = threading.Thread(target=write_md_file)

    txt_thread.start()
    md_thread.start()

    txt_thread.join()
    md_thread.join()

    print(f"created {txtfilename} and {mdfilename} for you")


def main():
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY not found!")
        print("Please check your .env file contains: OPENROUTER_API_KEY=your_key_here")
        return

    parse = argparse.ArgumentParser(description="Reddit username and Optional OpenRouter model")
    parse.add_argument("--username", required=True,
                       help="Provide reddit username to extract data")
    parse.add_argument("--model", required=False, default="deepseek/deepseek-r1-0528",
                       help="Provide OpenRouter model, default - deepseek/deepseek-r1-0528")

    args = parse.parse_args()
    username = args.username
    model = args.model

    prompt = build_prompt(username=username)
    
    print(f"Prompt length: {len(prompt)} characters")

    persona = get_llm_analyzed(prompt=prompt, model=model)
    
    if persona and not persona.startswith("Error:") and not persona.startswith("API Error:"):
        create_file(data=persona, username=username)
    else:
        print(f"Failed to generate persona: {persona}")


if __name__ == "__main__":
    main()

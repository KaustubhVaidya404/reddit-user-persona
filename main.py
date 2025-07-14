from bs4 import BeautifulSoup

from dotenv import load_dotenv

import requests

import argparse

import httpx

import os

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
    Purpose: Scraps limited userdata from https://www.reddit.com/user/{username}/
    Args: username (str)
    Returns: scraped data (str) - limited to avoid token limits
    """
    print(f"extracting userprofile of {username}")
    url: str = f"https://www.reddit.com/user/{username}/"

    try:
        result = requests.get(url, headers=headers)
        soup = BeautifulSoup(result.text, "html.parser")

        posts = soup.find_all("div", class_="subgrid-container")

        text_content = []
        total_chars = 0

        for i, post in enumerate(posts):
            if i >= 20:
                break

            text = post.get_text(strip=True)
            if text and len(text) > 30:
                cleaned_text = ' '.join(text.split())[:300]
                text_content.append(cleaned_text)
                total_chars += len(cleaned_text)

                if total_chars > 8000:
                    break

        result_text = '\n---\n'.join(text_content)

        if len(result_text) > 10000:
            result_text = result_text[:10000] + "\n[Content truncated for token limits]"

        print(f"Extracted {len(result_text)} characters from {len(text_content)} posts")

        with open("test.txt", "w", encoding="utf-8") as f:
            f.write(result_text)

        return result_text

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
    print("processing user information in llm, it might take some time")

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "RedditPersonaBuilder"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You're an expert in user behavior profiling."},
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
        if e.response.status_code == 402:
            return f"Error: Token limit exceeded or payment required. Try reducing the prompt size. Status: {e.response.status_code}"
        else:
            return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Error: {str(e)}"


def create_file(data: str, username: str):
    """
    Purpose: Creates txt file with by username and adds data to it
    Args: data (str), username (str)
    """

    os.makedirs("out", exist_ok=True)

    filename = f"out/persona_{username}.txt"

    with open(filename, "w", encoding="utf-8") as file:
            file.write(str(data))
            print(f"{filename} created successfully")
    print(f"created {filename} for you")


def main():
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY not found!")
        print("Please check your .env file contains: OPENROUTER_API_KEY=your_key_here")
        return

    parse = argparse.ArgumentParser(description="Reddit username and Optional OpenRouter model")
    parse.add_argument("--username", required=True,
                       help="Provide reddit username to extract data")
    parse.add_argument("--model", required=False,
                       default="deepseek/deepseek-r1-0528",
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

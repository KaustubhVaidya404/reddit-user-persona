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

        return str(data)
    except Exception as e:
        return f"Failed to fetch {username} data with error {e}"
    

def build_prompt(username):
    userdata = extract_userdata(username=username)
    print(f"prompt building")
    return f"""
Analyze the user and following Reddit posts and comments by user '{username}' and build a detailed user persona.

Include:
- Age range
- Gender
- Occupation
- Interests
- Personality traits
- Political or philosophical leanings
- Writing style or tone
- Preferred subreddits
- Behaviour and habbits
- Frustrations
- Goals
- Motivations
- Other relevant characteristics

Text:
{userdata}
"""



def get_llm_analyzed(prompt: str, model :str = "deepseek/deepseek-r1-0528"):
    """
    Purpose: communicates with model available on openrouter 
    Args: prompt (str), model (str): deepseek/deepseek-r1-0528
    Returns: llm generated user persona
    """
    print(f"processing user information in llm, it might take some time")

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "RedditPersonaBuilder"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You're an expert in user behavior profiling."},
            {"role": "user", "content": prompt}
        ]
    }

    response = httpx.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def create_file(data: str, username: str):
    """
    Purpose: Creates txt file with by username and adds data to it
    Args: data (str), username (str)
    """
    
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
    parse = argparse.ArgumentParser(description="Reddit username")
    parse.add_argument("--username", required=True, help="Provide reddit username to extract data")

    args = parse.parse_args()
    username = args.username

    prompt = build_prompt(username=username)

    persona = get_llm_analyzed(prompt=prompt)
    
    create_file(data=persona, username=username)


if __name__ == "__main__":
    main()
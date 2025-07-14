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


def extract_user_posts(username: str):
    """
    Purpose: Scrapes user's submitted posts from /submitted/ page
    Args: username (str)
    Returns: scraped posts data (str)
    """
    print(f"extracting posts of {username}")
    url = f"https://www.reddit.com/user/{username}/submitted/"

    try:
        result = requests.get(url, headers=headers)
        soup = BeautifulSoup(result.text, "html.parser")

        posts = soup.find_all("div", class_="subgrid-container")

        post_content = []
        total_chars = 0

        for i, post in enumerate(posts):
            if i >= 10:
                break

            text = post.get_text(strip=True)
            if text and len(text) > 50:
                cleaned_text = ' '.join(text.split())[:400]
                post_content.append(f"POST: {cleaned_text}")
                total_chars += len(cleaned_text)

                if total_chars > 4000:
                    break

        result_text = '\n---\n'.join(post_content)
        print(f"Extracted {len(result_text)} characters from {len(post_content)} posts")
        return result_text

    except Exception as e:
        print(f"Failed to fetch posts: {e}")
        return ""


def extract_user_comments(username: str):
    """
    Purpose: Scrapes user's comments from /comments/ page
    Args: username (str)
    Returns: scraped comments data (str)
    """
    print(f"extracting comments of {username}")
    url = f"https://www.reddit.com/user/{username}/comments/"

    try:
        result = requests.get(url, headers=headers)
        soup = BeautifulSoup(result.text, "html.parser")
        
        comments = soup.find_all("div", class_="subgrid-container")

        comment_content = []
        total_chars = 0

        for i, comment in enumerate(comments):
            if i >= 15:
                break

            text = comment.get_text(strip=True)
            if text and len(text) > 30:
                cleaned_text = ' '.join(text.split())[:300]
                comment_content.append(f"COMMENT: {cleaned_text}")
                total_chars += len(cleaned_text)
   
                if total_chars > 4000:
                    break

        result_text = '\n---\n'.join(comment_content)
        print(f"Extracted {len(result_text)} characters from {len(comment_content)} comments")
        return result_text
   
    except Exception as e:
        print(f"Failed to fetch comments: {e}")
        return ""


def extract_userdata(username: str):
    """
    Purpose: Scrapes combined user data from profile, posts, and comments
    Args: username (str)
    Returns: scraped data (str) - limited to avoid token limits
    """
    print(f"extracting complete profile of {username}")

    profile_url = f"https://www.reddit.com/user/{username}/"
    profile_data = ""

    try:
        result = requests.get(profile_url, headers=headers)
        soup = BeautifulSoup(result.text, "html.parser")

        posts = soup.find_all("div", class_="subgrid-container")
        text_content = []
        total_chars = 0

        for i, post in enumerate(posts):
            if i >= 10:  # Limit profile data
                break

            text = post.get_text(strip=True)
            if text and len(text) > 30:
                cleaned_text = ' '.join(text.split())[:250]
                text_content.append(f"PROFILE: {cleaned_text}")
                total_chars += len(cleaned_text)

                if total_chars > 2500:
                    break

        profile_data = '\n---\n'.join(text_content)
    
    except Exception as e:
        print(f"Failed to fetch profile: {e}")
        profile_data = ""

    posts_data = extract_user_posts(username)
    comments_data = extract_user_comments(username)

    all_data = []
    if profile_data:
        all_data.append(f"=== PROFILE DATA ===\n{profile_data}")
    if posts_data:
        all_data.append(f"=== SUBMITTED POSTS ===\n{posts_data}")
    if comments_data:
        all_data.append(f"=== COMMENTS ===\n{comments_data}")

    combined_data = '\n\n'.join(all_data)

    if len(combined_data) > 12000:
        combined_data = combined_data[:12000] + "\n[Content truncated for token limits]"

    print(f"Total extracted: {len(combined_data)} characters")
  
    return combined_data


def build_prompt(username):
    userdata = extract_userdata(username=username)
    print("prompt building")
    return f"""
Analyze the following Reddit user data for '{username}' and build a comprehensive user persona in plane readable text.
The data includes their profile activity, submitted posts, and comments.

Please provide detailed analysis including:
- Age range (estimate based on language, interests, references)
- Gender (if determinable from content)
- Occupation/Education level
- Interests and hobbies
- Personality traits and behavioral patterns
- Political or philosophical leanings
- Writing style and communication patterns
- Preferred subreddits and communities
- Social behaviors and interaction style
- Values and motivations
- Potential pain points or frustrations
- Goals and aspirations (if evident)

User Data:
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

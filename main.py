from bs4 import BeautifulSoup

import requests

import argparse

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/58.0.3029.110 Safari/537.36"
    )
}


def extract_userdata(username: str):
    """
    Purpuse: Scraps the userdata from https://www.reddit.com/user/{username}/
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




def main():
    parse = argparse.ArgumentParser(description="Reddit username")
    parse.add_argument("--username", required=True, help="Provide reddit username to extract data")

    args = parse.parse_args()
    username = args.username




if __name__ == "__main__":
    main()
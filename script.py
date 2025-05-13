"""
Scrapes a headline from The Daily Pennsylvanian website and saves it to a 
JSON file that tracks headlines over time.
"""

import os
import sys
import json  # Import JSON to handle file creation
import daily_event_monitor

import bs4
from bs4 import BeautifulSoup
import requests
import loguru


def scrape_data_point():
    url = "https://www.thedp.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(url, headers=headers)
    print("Request status code:", response.status_code)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch page. Status: {response.status_code}")

    soup = BeautifulSoup(response.content, "html.parser")

    # Look for the "Most Read" list and grab the top article
    most_read_section = soup.find("div", class_="most-read")
    if not most_read_section:
        raise Exception("Could not find Most Read section")

    top_story = most_read_section.find("a")
    if not top_story:
        raise Exception("Could not find top story link in Most Read section")

    headline = top_story.get_text(strip=True)
    link = "https://www.thedp.com" + top_story['href']
    return {"headline": headline, "url": link}


if __name__ == "__main__":

    # Setup logger to track runtime
    loguru.logger.add("scrape.log", rotation="1 day")

    # Create data dir if needed
    loguru.logger.info("Creating data directory if it does not exist")
    try:
        os.makedirs("data", exist_ok=True)
    except Exception as e:
        loguru.logger.error(f"Failed to create data directory: {e}")
        sys.exit(1)

    # Ensure the JSON file exists
    json_file_path = "data/daily_pennsylvanian_headlines.json"
    if not os.path.isfile(json_file_path):
        loguru.logger.info("File does not exist, creating an empty JSON file")
        try:
            with open(json_file_path, "w") as f:
                json.dump([], f)  # Initialize with an empty list
        except Exception as e:
            loguru.logger.error(f"Failed to create the JSON file: {e}")
            sys.exit(1)

    # Load daily event monitor
    loguru.logger.info("Loading daily event monitor")
    dem = daily_event_monitor.DailyEventMonitor(json_file_path)

    # Run scrape
    loguru.logger.info("Starting scrape")
    try:
        data_point = scrape_data_point()
    except Exception as e:
        loguru.logger.error(f"Failed to scrape data point: {e}")
        data_point = None

    # Save data
    if data_point is not None:
        dem.add_today(data_point)
        dem.save()
        loguru.logger.info("Saved daily event monitor")

    def print_tree(directory, ignore_dirs=[".git", "__pycache__"]):
        loguru.logger.info(f"Printing tree of files/dirs at {directory}")
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            level = root.replace(directory, "").count(os.sep)
            indent = " " * 4 * (level)
            loguru.logger.info(f"{indent}+--{os.path.basename(root)}/")
            sub_indent = " " * 4 * (level + 1)
            for file in files:
                loguru.logger.info(f"{sub_indent}+--{file}")

    print_tree(os.getcwd())

    loguru.logger.info("Printing contents of data file {}".format(dem.file_path))
    with open(dem.file_path, "r") as f:
        loguru.logger.info(f.read())

    # Finish
    loguru.logger.info("Scrape complete")
    loguru.logger.info("Exiting")

from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError
import time
import os
import logging
import json
from datetime import datetime
import shutil
import requests
from urllib.parse import urlparse
import re
import random

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_repost.log'),
        logging.StreamHandler()
    ]
)

# Configuration
CONFIG_FILE = "config.json"
REPOSTED_IDS_FILE = "reposted_ids.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        config = {
            "source_username": "",
            "target_username": "",
            "target_password": "",
            "check_interval": 3000  # Time in seconds between reposts (50 minutes)
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        logging.error(f"Please fill in your credentials in {CONFIG_FILE}")
        exit(1)
    
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

# Directories
DOWNLOAD_DIR = "downloaded_images"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def load_reposted_ids():
    """Load the set of previously reposted media IDs"""
    if os.path.exists(REPOSTED_IDS_FILE):
        with open(REPOSTED_IDS_FILE, "r") as f:
            return set(str(id) for id in json.load(f))  # Convert all IDs to strings
    return set()

def save_reposted_ids(reposted_ids):
    """Save the set of previously reposted media IDs"""
    with open(REPOSTED_IDS_FILE, "w") as f:
        json.dump(list(reposted_ids), f)

def get_random_media(client, source_username):
    """Fetch a single random media from Instagram"""
    try:
        # Get user info
        user_info = client.user_info_by_username(source_username)
        if not user_info:
            logging.error(f"Could not find user: {source_username}")
            return None
            
        # Get a random media
        try:
            # Get total media count
            total_media = user_info.media_count
            if total_media == 0:
                logging.error(f"No media found for user: {source_username}")
                return None
                
            # Calculate a random offset (0 to total_media-1)
            random_offset = random.randint(0, total_media - 1)
            
            # Get media at random offset
            medias = client.user_medias(user_info.pk, 1, random_offset)
            if not medias:
                logging.error(f"Failed to fetch media at offset {random_offset}")
                return None
                
            return medias[0]
            
        except Exception as e:
            if "Please wait a few minutes" in str(e):
                logging.warning("Rate limited by Instagram. Waiting 5 minutes...")
                time.sleep(300)  # Wait 5 minutes
                return None
            raise e
            
    except Exception as e:
        logging.error(f"Error fetching media: {str(e)}")
        return None

def download_image(url, media_id):
    """Download image from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, stream=True, headers=headers)
        if response.status_code == 200:
            file_path = os.path.join(DOWNLOAD_DIR, f"{media_id}.jpg")
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return file_path
        logging.error(f"Failed to download image. Status code: {response.status_code}")
        return None
    except Exception as e:
        logging.error(f"Error downloading image: {str(e)}")
        return None

def login_client(username, password):
    client = Client()
    try:
        client.login(username, password)
        logging.info(f"Successfully logged in as {username}")
        return client
    except LoginRequired as e:
        logging.error(f"Login failed for {username}: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during login for {username}: {str(e)}")
        raise

def cleanup_old_images():
    """Remove images older than 24 hours"""
    current_time = time.time()
    for filename in os.listdir(DOWNLOAD_DIR):
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        if os.path.getmtime(filepath) < current_time - 86400:  # 24 hours
            os.remove(filepath)
            logging.info(f"Cleaned up old image: {filename}")

def repost_random_media(target_cl, source_username, config):
    """Repost a random media from the source account"""
    try:
        logging.info(f"Fetching a random post from {source_username}...")
        media = get_random_media(target_cl, source_username)
        
        if not media:
            logging.info("No post found")
            return

        # Load previously reposted IDs
        reposted_ids = load_reposted_ids()
        
        # Check if this media has been reposted before
        media_id = str(media.pk)
        if media_id in reposted_ids:
            logging.info("This post has already been reposted")
            return
            
        logging.info(f"Selected media with ID: {media_id}")

        # Get the image URL and download it
        image_url = media.thumbnail_url
        logging.info(f"Downloading image from: {image_url}")
        image_path = download_image(image_url, media_id)
        
        if not image_path:
            logging.error("Failed to download image")
            return

        caption = media.caption_text or ""
        logging.info(f"Posting with caption: {caption[:50]}...")

        # Post to target account
        logging.info("Reposting to target account...")
        target_cl.photo_upload(image_path, caption)

        # Add to reposted IDs and save
        reposted_ids.add(media_id)
        save_reposted_ids(reposted_ids)
        logging.info(f"Added media ID {media_id} to reposted list")
        logging.info("Repost complete")

    except ClientError as e:
        logging.error(f"Instagram API error: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error during repost: {str(e)}")
        logging.exception("Full traceback:")

def main():
    config = load_config()
    
    try:
        target_cl = login_client(config["target_username"], config["target_password"])
        
        logging.info("Starting random repost timer...")
        logging.info(f"Will repost every {config['check_interval']} seconds")
        
        while True:
            try:
                repost_random_media(target_cl, config["source_username"], config)
                cleanup_old_images()
                
                # Wait for the configured interval
                logging.info(f"Waiting {config['check_interval']} seconds until next repost...")
                time.sleep(config["check_interval"])
                
            except Exception as e:
                logging.error(f"Error in main loop: {str(e)}")
                logging.exception("Full traceback:")
                time.sleep(300)  # Wait 5 minutes before retrying
                
    except KeyboardInterrupt:
        logging.info("Script stopped by user")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        logging.exception("Full traceback:")
    finally:
        # Cleanup
        if os.path.exists(DOWNLOAD_DIR):
            shutil.rmtree(DOWNLOAD_DIR)
        logging.info("Script terminated")

if __name__ == "__main__":
    main()

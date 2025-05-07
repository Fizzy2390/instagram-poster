# Instagram Random Reposter

A Python script that automatically reposts random content from a source Instagram account to your target account at specified intervals. This tool is useful for creating automated content curation or maintaining an active presence on Instagram.

## Features

- 🔄 Random post selection from source account's entire history
- ⏱️ Configurable posting intervals
- 📝 Preserves original captions
- 🎯 Never reposts the same content twice
- 🧹 Automatic cleanup of downloaded images
- 📊 Detailed logging of all operations
- 🛡️ Rate limit handling and error recovery
- 🔒 Secure credential management

## Requirements

- Python 3.6+
- Instagram account credentials
- Required Python packages:
  - instagrapi
  - requests

## Installation

1. Clone this repository:
```bash
git clone https://github.com/Fizzy2390/instagram-poster.git
cd instagram-random-reposter
```

2. Install required packages:
```bash
pip install instagrapi requests
```

3. Create a `config.json` file with your credentials:
```json
{
    "source_username": "account_to_monitor",
    "target_username": "your_account",
    "target_password": "your_password",
    "check_interval": 3000
}
```

## Configuration

- `source_username`: The Instagram account to repost from
- `target_username`: Your Instagram account username
- `target_password`: Your Instagram account password
- `check_interval`: Time in seconds between reposts (default: 3000 seconds / 50 minutes)

## Usage

Run the script:
```bash
python app.py
```

The script will:
1. Log in to your Instagram account
2. Start the reposting timer
3. At each interval:
   - Select a random post from the source account
   - Check if it's been reposted before
   - If not, download and repost it
   - Save the post ID to prevent future reposts
   - Wait for the next interval

## Logging

The script creates detailed logs in `instagram_repost.log`, including:
- Login status
- Post selection
- Download progress
- Repost status
- Error messages
- Rate limit warnings

## Safety Features

- Handles Instagram rate limits automatically
- Waits 5 minutes when rate limited
- Cleans up downloaded images after 24 hours
- Never reposts the same content twice
- Secure credential storage in config file

## Notes

- The source account must be public
- Instagram may have rate limits on API usage
- Use responsibly and in accordance with Instagram's terms of service
- Recommended to use longer intervals (e.g., 300 seconds) to avoid rate limits

## License

MIT License

## Disclaimer

This tool is for educational purposes only. Use it responsibly and in accordance with Instagram's terms of service. The author is not responsible for any misuse or account restrictions that may result from using this script. 
import requests

# Your personal access token
ACCESS_TOKEN = 'your_token'

# Base URL for Figshare API
BASE_URL = 'https://api.figshare.com/v2'

# Set headers with token
headers = {
    'Authorization': f'token {ACCESS_TOKEN}'
}

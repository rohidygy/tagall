import os

from dotenv import load_dotenv

load_dotenv()


API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
TOKEN = os.getenv("TOKEN")
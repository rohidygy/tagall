import os

from dotenv import load_dotenv

load_dotenv()


API_ID = int(os.getenv("API_ID", "25194940"))
API_HASH = os.getenv("API_HASH", "ed16f15b65c372cc60159afb62963824")
TOKEN = os.getenv("TOKEN", "6450071825:AAFb1qVXPZaJPKa4A9Ekel8CkS8YuBwLc-8")

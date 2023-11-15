import os
from dotenv import load_dotenv
load_dotenv()

SECRET = os.getenv('SECRET')
DATABASE_URL = os.getenv('DATABASE_URL')
REDISCLOUD_URL = os.getenv('REDISCLOUD_URL')
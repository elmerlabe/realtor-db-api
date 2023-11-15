import os
from dotenv import load_dotenv
load_dotenv()

SECRET = os.getenv('SECRET')
DATABASE_URL = os.getenv('DATABASE_URL')
REDISCLOUD_URL = os.getenv('REDISCLOUD_URL')

#heroku database uri fix
#https://help.heroku.com/ZKNTJQSK/why-is-sqlalchemy-1-4-x-not-connecting-to-heroku-postgres
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://" ,"postgresql://", 1)
import pymongo
from dotenv import load_dotenv
from os import getenv

load_dotenv()

db_client = pymongo.MongoClient(getenv("MONGO_URI"))
db = db_client[getenv("environment", "development")]
db.gc_room.create_index(
    [
        ("channels", pymongo.TEXT),
    ],
    unique=True,
)

print("Done.")

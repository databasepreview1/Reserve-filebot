import asyncio
import logging

import pymongo
from pymongo.errors import PyMongoError

from config import DB_URL, DB_NAME

logger = logging.getLogger(__name__)

# NOTE: pymongo is a *blocking* driver. If these calls are made directly
# inside an `async def`, a slow/unreachable MongoDB server (timeouts,
# ReplicaSetNoPrimary, etc.) will freeze the whole asyncio event loop for
# up to serverSelectionTimeoutMS, which in turn blocks Pyrogram from
# processing ANY updates (that's why the bot appeared to "stop responding"
# entirely, not just fail DB calls). Every call below is pushed to a
# worker thread via asyncio.to_thread so a stuck Mongo call can never
# freeze command handling, and every call is wrapped so a Mongo outage
# degrades gracefully instead of crashing the handler.

dbclient = pymongo.MongoClient(
    DB_URL,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000,
    retryWrites=True,
    retryReads=True,
    maxPoolSize=50,
    heartbeatFrequencyMS=10000,
)
database = dbclient[DB_NAME]
user_data = database['users']  # collection name unchanged - no data migration/reset


async def present_user(user_id: int) -> bool:
    """Return True if the user exists. On a DB error, returns False
    instead of raising/hanging - the caller (start handler) will then
    try add_user(), which is itself safe against duplicate-key errors,
    so no data is lost or reset."""
    try:
        found = await asyncio.to_thread(user_data.find_one, {'_id': user_id})
        return bool(found)
    except PyMongoError as e:
        logger.warning(f"[DB] present_user({user_id}) failed: {e}")
        return False


async def add_user(user_id: int) -> bool:
    try:
        await asyncio.to_thread(user_data.insert_one, {'_id': user_id})
        return True
    except pymongo.errors.DuplicateKeyError:
        # user already present - not an error, nothing to do
        return True
    except PyMongoError as e:
        logger.warning(f"[DB] add_user({user_id}) failed: {e}")
        return False


async def full_userbase() -> list:
    """Returns the list of all user ids. On a DB error, returns an empty
    list rather than raising, so /users and /broadcast fail soft instead
    of killing the handler. No documents are read destructively, dropped,
    or modified."""
    try:
        def _fetch():
            return [doc['_id'] for doc in user_data.find({}, {'_id': 1})]
        return await asyncio.to_thread(_fetch)
    except PyMongoError as e:
        logger.warning(f"[DB] full_userbase() failed: {e}")
        return []


async def del_user(user_id: int) -> bool:
    try:
        await asyncio.to_thread(user_data.delete_one, {'_id': user_id})
        return True
    except PyMongoError as e:
        logger.warning(f"[DB] del_user({user_id}) failed: {e}")
        return False





# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Backup Channel @JishuBotz
# Developer @JishuDeveloper

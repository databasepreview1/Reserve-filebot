import base64
import re
import asyncio
import logging
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import FORCE_SUB_CHANNEL, ADMINS
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

logger = logging.getLogger(__name__)




async def is_subscribed(filter, client, update):
    if not FORCE_SUB_CHANNEL:
        return True
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True
    try:
        member = await client.get_chat_member(chat_id = FORCE_SUB_CHANNEL, user_id = user_id)
    except UserNotParticipant:
        return False

    if not member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
        return False
    else:
        return True 


async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string


async def decode(base64_string):
    base64_string = base64_string.strip("=") # links generated before this commit will be having = sign, hence striping them to handle padding errors.
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes) 
    string = string_bytes.decode("ascii")
    return string


async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temb_ids = message_ids[total_messages:total_messages+200]
        msgs = []  # always defined - avoids NameError if the fetch below fails
        for attempt in range(3):
            try:
                msgs = await client.get_messages(
                    chat_id=client.db_channel.id,
                    message_ids=temb_ids
                )
                break
            except FloodWait as e:
                logger.warning(f"[get_messages] FloodWait {e.x}s, retrying...")
                await asyncio.sleep(e.x + 1)
            except Exception as e:
                logger.warning(f"[get_messages] failed to fetch batch: {e}")
                msgs = []
                break
        total_messages += len(temb_ids)
        messages.extend(msgs)
    return messages


def is_copyable(message) -> bool:
    """True if a message actually has content Pyrogram can copy.
    Guards against the 'Empty messages cannot be copied' error, which
    happens for deleted/service messages or gaps in the DB channel."""
    if message is None:
        return False
    if getattr(message, "empty", False):
        return False
    return True


async def safe_copy_message(message, chat_id, **kwargs):
    """Copy a message with a FloodWait retry loop and an empty-message
    guard. Returns the copied Message on success, or None if the
    message was empty/non-copyable or copying failed after retries.
    Never raises FloodWait or 'Empty messages cannot be copied' up to
    the caller. UserIsBlocked/InputUserDeactivated ARE re-raised so
    callers (e.g. broadcast) can still detect and clean up those users."""
    if not is_copyable(message):
        logger.info(f"[safe_copy_message] skipped empty/non-copyable message {getattr(message, 'id', '?')}")
        return None

    for attempt in range(3):
        try:
            return await message.copy(chat_id=chat_id, **kwargs)
        except FloodWait as e:
            logger.warning(f"[safe_copy_message] FloodWait {e.x}s, waiting...")
            await asyncio.sleep(e.x + 1)
        except (UserIsBlocked, InputUserDeactivated):
            # Let the caller handle these (e.g. remove the user from the DB).
            raise
        except ValueError as e:
            # Covers "Empty messages cannot be copied" if it slips past
            # the is_copyable() check for any pyrogram-version reason.
            logger.info(f"[safe_copy_message] skipped: {e}")
            return None
        except Exception as e:
            logger.warning(f"[safe_copy_message] copy failed: {e}")
            return None
    logger.warning("[safe_copy_message] gave up after repeated FloodWait")
    return None


async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = "https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern,message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    else:
        return 0


def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time


subscribed = filters.create(is_subscribed)
       





# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Backup Channel @JishuBotz
# Developer @JishuDeveloper

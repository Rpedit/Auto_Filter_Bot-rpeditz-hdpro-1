from aiohttp import web
from .route import routes
from asyncio import sleep 
from datetime import datetime
from database.users_chats_db import db
from info import URL, PREMIUM_LOGS
from Script import script
from pyrogram.errors import InputUserDeactivated, UserIsBlocked, PeerIdInvalid
import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

async def check_expired_premium(client):
    while True:
        try:
            data = await db.get_expired(datetime.now())
            for u in data:
                user_id = u["id"]
                await db.remove_premium_access(user_id)
                try:
                    tg_user = await client.get_users(user_id)
                    mention = tg_user.mention if tg_user else "User"
                    await client.send_message(
                        chat_id=user_id,
                        text=script.PREMIUM_END_TEXT.format(mention)
                    )
                    await client.send_message(
                        PREMIUM_LOGS, 
                        text=f"<b>#Premium_Expire\n\nUser name: {mention}\nUser id: <code>{user_id}</code></b>"
                    )
                except (InputUserDeactivated, UserIsBlocked, PeerIdInvalid):
                    logger.warning(f"User {user_id} deactivated ya blocked hai. Skipped.")
                except Exception as e:
                    logger.error(f"Premium expire notification error for {user_id}: {e}")
                await sleep(0.5)
        except Exception as e:
            logger.error(f"Error in check_expired_premium background task: {e}")
        
        # Har 1 second me database ko choke karne ki jagah 60 second wait karega
        await sleep(60)

async def keep_alive():
    """Keep bot alive by sending periodic pings."""
    async with aiohttp.ClientSession() as session:
        while True:
            await asyncio.sleep(298)
            try:
                async with session.get(URL) as resp:
                    if resp.status != 200:
                        logger.warning(f"⚠️ Ping Error! Status: {resp.status}")
            except Exception as e:
                logger.error(f"❌ Ping Failed: {e}")

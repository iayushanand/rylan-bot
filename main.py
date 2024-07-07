import os

import aiosqlite
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utilities.discord_utilities import load_extensions, set_preferred_jishaku_flags

load_dotenv()
set_preferred_jishaku_flags()


class MyNewHelp(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            embed = discord.Embed(description=page, color=discord.Color.blurple())
            await destination.send(embed=embed)


class MyBot(commands.Bot):
    db = None

    async def load_db(self):
        self.db = await aiosqlite.connect("database.db")
        await self.db.execute("CREATE TABLE IF NOT EXISTS economy (user_id INT PRIMARY KEY, ice_cream INT)")
        await self.db.execute("CREATE TABLE IF NOT EXISTS inventory (user_id INT, item_name)")
        await self.db.commit()

    async def on_ready(self):
        print("Loaded in as: ", self.user.name)

    async def setup_hook(self) -> None:
        await load_extensions(self, "cogs", func=lambda i: print("Successfully loaded ", i))
        await self.load_extension("jishaku")
        print("Successfully loaded jishaku")
        await self.load_db()
        print("Successfully loaded the database")

bot = MyBot(command_prefix="?", intents=discord.Intents.all(), owner_ids={724275771278884906, 1119002837985267752}, help_command=MyNewHelp())

bot.run(os.getenv("TOKEN"))

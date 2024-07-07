from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from utilities.discord_utilities import MakeModal

if TYPE_CHECKING:
    from main import MyBot

import json

with open("shop.json") as f:
    shop = json.load(f)


class AddItemButton(discord.ui.View):
    async def interaction_check(self, interaction: discord.Interaction["MyBot"]):
        return await interaction.client.is_owner(interaction.user)

    @discord.ui.button(label="Press to add an item!", style=discord.ButtonStyle.blurple)
    async def callback(self, interaction: discord.Interaction, _):
        global shop

        async def callback(interaction: discord.Interaction, values: dict[str, str]):
            name = values["name"].lower()
            price = values["price"]
            description = values["description"]
            emoji = values.get("emoji", "")

            if not price.isdigit():
                return await interaction.response.send_message(content="The price must be an integer", ephemeral=True)
            elif name in shop:
                return await interaction.response.send_message(content="An item with that name already exists", ephemeral=True)
            price = int(price)

            shop[name] = {
                "name": name,
                "emoji": emoji,
                "price": price,
                "description": description
            }

            with open("shop.json", "w") as f:
                json.dump(shop, f, indent=2)

            await interaction.response.send_message(content=f"Successfully added {name} to the shop", ephemeral=True)

        modal = MakeModal(title="Add Item", callback=callback, inputs=[
            discord.ui.TextInput(label="Name", placeholder="The name of the item"),
            discord.ui.TextInput(label="Price", placeholder="The price of the item"),
            discord.ui.TextInput(label="Emoji", placeholder="The emoji of the item"),
            discord.ui.TextInput(label="Description", placeholder="The description of the item", style=discord.TextStyle.long),
        ])
        await interaction.response.send_modal(modal)


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot: "MyBot" = bot

    @commands.command()
    @commands.is_owner()
    async def add_icecream(self, ctx: commands.Context, user: discord.User, amount: int):
        await self.bot.db.execute("INSERT INTO economy (user_id, ice_cream) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET ice_cream = ice_cream + excluded.ice_cream", (user.id, amount))
        await self.bot.db.commit()
        await ctx.send(f"Added {amount} icecream to {user.mention}")

    @commands.command()
    @commands.is_owner()
    async def add_item(self, ctx: commands.Context):
        view = AddItemButton()
        await ctx.send("Press the button!", view=view)

    @commands.command()
    @commands.is_owner()
    async def remove_item(self, ctx: commands.Context, item_name):
        global shop
        if item_name not in shop:
            return await ctx.send("That item doesn't exist")

        del shop[item_name]
        with open("shop.json", "w") as f:
            json.dump(shop, f, indent=2)
        await ctx.send(f"Successfully removed {item_name} from the shop")

    @commands.command()
    async def shop(self, ctx: commands.Context):
        embed = discord.Embed(title="Shop", color=discord.Color.blurple())
        for name, data in shop.items():
            embed.add_field(name=f"{data['emoji']} {name}", value=f"**Price:** {data['price']:,}\n{data['description']}")

        await ctx.send(embed=embed)

    @commands.command(aliases=['lb'])
    async def leaderboard(self, ctx: commands.Context):
        row = await self.bot.db.execute("SELECT user_id, ice_cream FROM economy ORDER BY ice_cream DESC LIMIT 10")
        row = await row.fetchall()

        embed = discord.Embed(title="Leaderboard", description="", color=discord.Color.blurple())

        for i, data in enumerate(row, start=1):
            embed.description += f"**{i}.**<@{data[0]}> | {data[1]}🍦\n"

        await ctx.send(embed=embed)

    @commands.command()
    async def buy(self, ctx: commands.Context, *, item_name: str):
        try:
            item = shop[item_name.lower()]
        except KeyError:
            return await ctx.send("That item doesn't exist")

        cursor = await self.bot.db.execute("SELECT ice_cream FROM economy WHERE user_id = ?", (ctx.author.id,))
        data = await cursor.fetchone()
        if data is None:
            money = 0
        else:
            money = data[0]

        if item['price'] > money:
            return await ctx.send(f"You don't have enough ice cream to buy {item_name}")

        await self.bot.db.execute("UPDATE economy SET ice_cream = ice_cream - ? WHERE user_id = ?", (item['price'], ctx.author.id))
        await self.bot.db.execute("INSERT INTO inventory (user_id, item_name) VALUES (?, ?)", (ctx.author.id, item['name']))
        await ctx.send(f"Successfully bought {item_name}")

    @commands.command(aliases=['bal'])
    async def balance(self, ctx: commands.Context, user: discord.User = commands.Author):
        cursor = await self.bot.db.execute("SELECT ice_cream FROM economy WHERE user_id = ?", (user.id,))
        data = await cursor.fetchone()
        if data is None:
            money = 0
        else:
            money = data[0]

        await ctx.send(f"You have {money} icecream!")

    @commands.command(aliases=['inv'])
    async def inventory(self, ctx: commands.Context, user: discord.User = commands.Author):
        cursor = await self.bot.db.execute("SELECT item_name FROM inventory WHERE user_id = ?", (user.id,))
        data = await cursor.fetchall()
        items = {}

        for item in data:
            name = item[0]
            if name in items:
                items[name] += 1
            else:
                items[name] = 1

        embed = discord.Embed(title="Inventory", description="\n".join(f"{v} {k}" for k, v in items.items()), color=discord.Color.blurple())
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Economy(bot))

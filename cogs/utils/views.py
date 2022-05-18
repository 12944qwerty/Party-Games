import discord
from discord import app_commands
import asyncio

class Confirm(discord.ui.View):
    def __init__(self, bot, interaction, *args, **kwargs):
        super().__init__(*args, **kwargs, timeout=30.0)
        self.bot = bot
        self.interaction = interaction

        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirmed(self, button, interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def canceled(self, button, interaction):
        self.value = False
        self.stop()

    async def interaction_check(self, interaction):
        return interaction.user == self.interaction.author
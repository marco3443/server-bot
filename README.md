# This is a comprehensive Discord bot with various features.
# To use this bot, you must replace 'YOUR_BOT_TOKEN_HERE' with your bot's actual token.
# هذا الكود هو لبوت ديسكورد متكامل بمميزات متنوعة.
# لاستخدام هذا البوت، يجب عليك استبدال 'YOUR_BOT_TOKEN_HERE' بالرمز الخاص بالبوت.

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get
import asyncio
from datetime import timedelta
import random
from typing import Optional

# Set up intents to allow the bot to read events
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.reactions = True

# Define the bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Channel and role names for the bot to use
VERIFY_CHANNEL_NAME = "verify-here"
VERIFY_EMOJI = "✅"
REPORT_CHANNEL_NAME = "reports-channel"
ADMIN_ROLE_NAME = "★--𝗛𝗶𝗴𝗵 𝗠𝗮𝗻𝗮𝗴𝗲𝗺𝗲𝗻𝘁--★"
LOG_CHANNEL_NAME = "log-channel"
MUTED_ROLE_NAME = "Muted"

# List of bad words for automatic filtering
BAD_WORDS = ["كلمة1", "كلمة2", "كلمة3", "كلمة4"] # Fill this list with the words you want to block

# Starboard setup
STARBOARD_CHANNEL_NAME = "starboard"
STARBOARD_EMOJI = "⭐"
STARBOARD_THRESHOLD = 3 # Number of stars required to pin a message

# A list to store message IDs that have already been starboarded
starboarded_messages = []
autorole_id = None
starboard_channel_id = None
log_channel_id = None
report_channel_id = None
verify_channel_id = None

# Blacklist & Whitelist
# To specify users, place their User IDs here
BLACKLISTED_USERS = set()  # Users who cannot use bot commands
WHITELISTED_USERS = set()  # Users who can use certain restricted commands

def is_whitelisted(user_id):
    """
    Check if a user is in the whitelist.
    The whitelist is optional. If it's empty, everyone can use the commands.
    """
    return not WHITELISTED_USERS or user_id in WHITELISTED_USERS

# Custom check to see if a user is not blacklisted
def is_not_blacklisted():
    def predicate(interaction: discord.Interaction):
        return interaction.user.id not in BLACKLISTED_USERS
    return app_commands.check(predicate)

# Custom check to see if a user is on the whitelist (and a specific role)
def is_whitelisted_and_admin():
    def predicate(interaction: discord.Interaction):
        is_admin = get(interaction.user.roles, name=ADMIN_ROLE_NAME)
        return is_admin and (not WHITELISTED_USERS or interaction.user.id in WHITELISTED_USERS)
    return app_commands.check(predicate)

@bot.event
async def on_ready():
    """This function runs when the bot successfully starts."""
    print(f'Logged in as {bot.user}')
    
    global starboard_channel_id, log_channel_id, report_channel_id, verify_channel_id
    
    # Store channel IDs for faster access
    for guild in bot.guilds:
        log_channel = get(guild.text_channels, name=LOG_CHANNEL_NAME)
        if log_channel:
            log_channel_id = log_channel.id
            
        starboard_channel = get(guild.text_channels, name=STARBOARD_CHANNEL_NAME)
        if starboard_channel:
            starboard_channel_id = starboard_channel.id

        report_channel = get(guild.text_channels, name=REPORT_CHANNEL_NAME)
        if report_channel:
            report_channel_id = report_channel.id

        verify_channel = get(guild.text_channels, name=VERIFY_CHANNEL_NAME)
        if verify_channel:
            verify_channel_id = verify_channel.id
        
        break

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.event
async def on_member_join(member):
    """This function runs when a new member joins the server."""
    log_channel = bot.get_channel(log_channel_id)
    verify_channel = bot.get_channel(verify_channel_id)

    if log_channel:
        embed = discord.Embed(
            title="🆕 New Member",
            description=f"**{member.mention}** has joined the server.",
            color=discord.Color.green()
        )
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        await log_channel.send(embed=embed)
    
    if verify_channel:
        embed = discord.Embed(
            title="Welcome!",
            description=f"{member.mention}, welcome to the server! Please press ✅ to open a verification ticket.",
            color=discord.Color.blue()
        )
        msg = await verify_channel.send(embed=embed)
        await msg.add_reaction(VERIFY_EMOJI)

    # Give auto-role if set
    global autorole_id
    if autorole_id:
        role = member.guild.get_role(autorole_id)
        if role:
            await member.add_roles(role)
            print(f"Auto-role '{role.name}' assigned to {member.name}.")

@bot.event
async def on_raw_reaction_add(payload):
    """This function runs when a user adds a reaction to a message."""
    # Ticket system
    if payload.emoji.name == VERIFY_EMOJI and payload.channel_id == verify_channel_id:
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if member.bot: 
            return
            
        ticket_channel_name = f'ticket-{member.name.lower()}'
        existing_channel = get(guild.text_channels, name=ticket_channel_name)
        
        if existing_channel:
            try:
                await existing_channel.send(f"Hey {member.mention}, you already have an open ticket. Please check here.")
            except discord.Forbidden:
                pass # Bot can't send messages, ignore
            return
        
        verification_category = get(guild.categories, name="Verification")
        if not verification_category:
            verification_category = await guild.create_category("Verification")

        ticket_channel = await guild.create_text_channel(
            f'ticket-{member.name}',
            category=verification_category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
        )
        await ticket_channel.send(f"Welcome {member.mention}! Please type anything here to complete the verification.")
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            embed = discord.Embed(
                title="🎟️ New Ticket",
                description=f"**{member.name}** has opened a verification ticket: {ticket_channel.mention}",
                color=discord.Color.purple()
            )
            await log_channel.send(embed=embed)

    # Starboard system
    if payload.emoji.name == STARBOARD_EMOJI and payload.channel_id != starboard_channel_id:
        guild = bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return
        
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        starboard_channel = bot.get_channel(starboard_channel_id)
        
        if message.author.bot or message.id in starboarded_messages or not starboard_channel:
            return

        for reaction in message.reactions:
            if str(reaction.emoji) == STARBOARD_EMOJI:
                if reaction.count >= STARBOARD_THRESHOLD:
                    embed = discord.Embed(
                        title="Pinned Message! ⭐",
                        description=f"{message.content}\n\n[Go to message]({message.jump_url})",
                        color=discord.Color.yellow()
                    )
                    embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url if message.author.avatar else None)
                    
                    if message.attachments:
                        embed.set_image(url=message.attachments[0].url)
                    
                    await starboard_channel.send(embed=embed)
                    starboarded_messages.append(message.id)
                    break

@bot.event
async def on_message(message):
    """This function is used for member verification inside the ticket and also for filtering bad words."""
    if message.author.bot: 
        return
        
    # Bad word filter
    for word in BAD_WORDS:
        if word in message.content.lower():
            await message.delete()
            await message.channel.send(f"{message.author.mention}, please do not use inappropriate language.", delete_after=5)
            log_channel = bot.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="⛔ Forbidden Message",
                    description=(
                        f"**Message:** \n```\n{message.content}\n```\n"
                        f"**User:** {message.author.mention}\n"
                        f"**In channel:** {message.channel.mention}"
                    ),
                    color=discord.Color.red()
                )
                await log_channel.send(embed=embed)
            return

    # Member verification in the ticket
    if message.channel.name.startswith("ticket-"):
        # This logic should be handled by a moderator or a specific command,
        # but for the sake of the original code, we will make it a one-time thing.
        # This prevents the channel from being deleted on every message.
        if "تم التحقق" not in message.channel.topic:
            await message.channel.edit(topic="Member Verified")
            log_channel = bot.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="✅ New Member Verified!",
                    description=(
                        f"**Name:** {message.author.mention}\n"
                        f"**Join Date:** {message.author.joined_at.strftime('%Y-%m-%d %H:%M:%S')}"
                    ),
                    color=discord.Color.green()
                )
                await log_channel.send(embed=embed)
            await message.channel.send("Verification successful! The ticket will be closed soon.")
            await asyncio.sleep(5)
            await message.channel.delete()

    await bot.process_commands(message)

# Administrative event logging
@bot.event
async def on_guild_channel_create(channel):
    log_channel = bot.get_channel(log_channel_id)
    if log_channel:
        embed = discord.Embed(title="➕ New Channel", description=f"A new channel has been created: {channel.mention} of type `{channel.type}`", color=discord.Color.blue())
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_channel_delete(channel):
    log_channel = bot.get_channel(log_channel_id)
    if log_channel:
        embed = discord.Embed(title="➖ Channel Deleted", description=f"The channel `{channel.name}` of type `{channel.type}` has been deleted", color=discord.Color.orange())
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_channel_update(before, after):
    log_channel = bot.get_channel(log_channel_id)
    if log_channel:
        changes = []
        if before.name != after.name: changes.append(f"Name: `{before.name}` -> `{after.name}`")
        if before.topic != after.topic: changes.append(f"Topic: Modified.")
        if changes:
            embed = discord.Embed(title="📝 Channel Updated", description=f"Channel {after.mention} has been updated\n" + "\n".join(changes), color=discord.Color.yellow())
            await log_channel.send(embed=embed)

@bot.event
async def on_member_ban(guild, user):
    log_channel = bot.get_channel(log_channel_id)
    if log_channel:
        embed = discord.Embed(title="🔨 Member Banned", description=f"The member {user.mention} has been banned", color=discord.Color.dark_red())
        await log_channel.send(embed=embed)

@bot.event
async def on_member_unban(guild, user):
    log_channel = bot.get_channel(log_channel_id)
    if log_channel:
        embed = discord.Embed(title="✅ Member Unbanned", description=f"The member {user.mention} has been unbanned", color=discord.Color.green())
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_role_create(role):
    log_channel = bot.get_channel(log_channel_id)
    if log_channel:
        embed = discord.Embed(title="➕ New Role", description=f"A new role has been created: `{role.name}`", color=discord.Color.blue())
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_role_delete(role):
    log_channel = bot.get_channel(log_channel_id)
    if log_channel:
        embed = discord.Embed(title="➖ Role Deleted", description=f"The role `{role.name}` has been deleted", color=discord.Color.orange())
        await log_channel.send(embed=embed)

@bot.event
async def on_member_update(before, after):
    log_channel = bot.get_channel(log_channel_id)
    if log_channel:
        if len(before.roles) < len(after.roles):
            new_role = next((role for role in after.roles if role not in before.roles), None)
            if new_role:
                embed = discord.Embed(title="🛡️ New Role", description=f"**{after.mention}** received the role: `{new_role.name}`", color=discord.Color.green())
                await log_channel.send(embed=embed)
        elif len(before.roles) > len(after.roles):
            removed_role = next((role for role in before.roles if role not in after.roles), None)
            if removed_role:
                embed = discord.Embed(title="❌ Role Removed", description=f"The role `{removed_role.name}` was removed from **{after.mention}**", color=discord.Color.red())
                await log_channel.send(embed=embed)

# General Commands
@bot.tree.command(name="ping", description="Shows the bot's response latency.")
@is_not_blacklisted()
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'Latency: {round(bot.latency * 1000)}ms')

@bot.tree.command(name="userinfo", description="Displays information about a specific member.")
@is_not_blacklisted()
async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    embed = discord.Embed(title="User Information", color=member.color)
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    embed.add_field(name="Name", value=member.display_name, inline=False)
    embed.add_field(name="Username", value=member.name, inline=False)
    embed.add_field(name="Roles", value=", ".join([role.mention for role in member.roles if role.name != "@everyone"]), inline=False)
    embed.add_field(name="Joined At", value=member.joined_at.strftime('%Y-%m-%d %H:%M:%S'), inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverinfo", description="Displays detailed information about the server.")
@is_not_blacklisted()
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"Server Information: {guild.name}", color=discord.Color.blue())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="Member Count", value=guild.member_count, inline=True)
    embed.add_field(name="Channel Count", value=len(guild.channels), inline=True)
    embed.add_field(name="Creation Date", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Role Count", value=len(guild.roles), inline=True)
    embed.add_field(name="Server ID", value=guild.id, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="avatar", description="Displays the profile picture of a specific member.")
@is_not_blacklisted()
async def avatar(interaction: discord.Interaction, member: Optional[discord.Member]):
    member = member or interaction.user
    if member.avatar:
        embed = discord.Embed(title=f"Profile picture for {member.display_name}", color=member.color)
        embed.set_image(url=member.avatar.url)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"No profile picture available for {member.display_name}", ephemeral=True)

@bot.tree.command(name="roll", description="Rolls a die and shows the result.")
@is_not_blacklisted()
async def roll(interaction: discord.Interaction, sides: app_commands.Range[int, 2, 100] = 6):
    roll_result = random.randint(1, sides)
    await interaction.response.send_message(f"I rolled a {sides}-sided die, and the result is: `{roll_result}`!")

@bot.tree.command(name="announce", description="Sends an announcement in a specific channel.")
@is_whitelisted_and_admin()
async def announce(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    embed = discord.Embed(
        title="📢 New Announcement",
        description=message,
        color=discord.Color.gold()
    )
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)
    try:
        await channel.send(embed=embed)
        await interaction.response.send_message(f"Announcement sent to {channel.mention} successfully.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message(f"I don't have permission to send messages in {channel.mention}.", ephemeral=True)

@bot.tree.command(name="giveaway", description="Creates a giveaway in the channel.")
@is_whitelisted_and_admin()
async def giveaway(interaction: discord.Interaction, duration: app_commands.Range[int, 1, 1440], winners: app_commands.Range[int, 1, 10], prize: str):
    await interaction.response.send_message("Creating the giveaway...", ephemeral=True)
    
    embed = discord.Embed(
        title="🎉 New Giveaway!",
        description=f"🎁 **Prize:** {prize}\n"
                    f"⏰ **Duration:** {duration} minutes\n"
                    f"👥 **Winners:** {winners}\n\n"
                    "To enter, react with 🎉",
        color=discord.Color.red()
    )
    giveaway_message = await interaction.channel.send(embed=embed)
    await giveaway_message.add_reaction("🎉")
    
    await asyncio.sleep(duration * 60)
    
    try:
        giveaway_message = await interaction.channel.fetch_message(giveaway_message.id)
        users = [user async for user in giveaway_message.reactions[0].users() if not user.bot]
    except (discord.NotFound, IndexError):
        await interaction.channel.send("Giveaway not found or no one reacted.")
        return

    if len(users) < winners:
        await interaction.channel.send("Not enough participants to select winners.")
        return
    
    selected_winners = random.sample(users, winners)
    
    winner_mentions = ", ".join([winner.mention for winner in selected_winners])
    await interaction.channel.send(f"🎉 Congratulations {winner_mentions}! You won **{prize}**!")

@bot.tree.command(name="report", description="Reports a member for violating the rules.")
@is_not_blacklisted()
async def report(interaction: discord.Interaction, member: discord.Member, reason: str):
    report_channel = bot.get_channel(report_channel_id)
    if report_channel:
        embed = discord.Embed(
            title="⚠️ New Report",
            description=f"**Reported User:** {member.mention}\n"
                        f"**Reported By:** {interaction.user.mention}\n"
                        f"**Reason:** `{reason}`",
            color=discord.Color.red()
        )
        await report_channel.send(embed=embed)
        await interaction.response.send_message("Your report has been sent successfully. Thank you for helping us maintain a safe environment.", ephemeral=True)
    else:
        await interaction.response.send_message(f"The report channel `{REPORT_CHANNEL_NAME}` was not found. Please inform an admin.", ephemeral=True)

class PollView(discord.ui.View):
    def __init__(self, question, options):
        super().__init__()
        self.question = question
        self.votes = {option: 0 for option in options}
        self.voters = set()
        
        for option in options:
            button = discord.ui.Button(label=option, style=discord.ButtonStyle.secondary, custom_id=option)
            button.callback = self.handle_vote
            self.add_item(button)

    async def handle_vote(self, interaction: discord.Interaction):
        if interaction.user.id in self.voters:
            await interaction.response.send_message("You have already voted in this poll.", ephemeral=True)
            return

        self.voters.add(interaction.user.id)
        option_chosen = interaction.data['custom_id']
        self.votes[option_chosen] += 1
        await interaction.response.send_message(f"Thank you, you have voted for `{option_chosen}`", ephemeral=True)
        
    @discord.ui.button(label="Show Results", style=discord.ButtonStyle.primary)
    async def show_results(self, interaction: discord.Interaction, button: discord.ui.Button):
        results_text = "Poll Results:\n"
        for option, count in self.votes.items():
            results_text += f"**{option}**: {count} votes\n"
        await interaction.response.send_message(results_text, ephemeral=True)

@bot.tree.command(name="poll", description="Creates a new poll with interactive buttons.")
@is_whitelisted_and_admin()
async def poll(interaction: discord.Interaction, question: str, option1: str, option2: str, option3: Optional[str] = None, option4: Optional[str] = None, option5: Optional[str] = None):
    options = [opt for opt in [option1, option2, option3, option4, option5] if opt is not None]
    
    embed = discord.Embed(
        title="New Poll",
        description=f"**{question}**\n\nVote by clicking the appropriate button:",
        color=discord.Color.gold()
    )
    
    view = PollView(question, options)
    
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="setup_autorole", description="Sets a role to be automatically given to new members.")
@is_whitelisted_and_admin()
async def setup_autorole(interaction: discord.Interaction, role: discord.Role):
    global autorole_id
    autorole_id = role.id
    await interaction.response.send_message(f"Successfully set `{role.name}` as the 'Auto Role'.", ephemeral=True)

@bot.tree.command(name="setup_starboard", description="Creates a 'starboard' channel to log featured messages.")
@is_whitelisted_and_admin()
async def setup_starboard(interaction: discord.Interaction):
    global starboard_channel_id
    starboard_channel_name = STARBOARD_CHANNEL_NAME
    existing_channel = get(interaction.guild.text_channels, name=starboard_channel_name)
    if not existing_channel:
        new_channel = await interaction.guild.create_text_channel(starboard_channel_name)
        starboard_channel_id = new_channel.id
        await interaction.response.send_message(f"Starboard channel created successfully.", ephemeral=True)
    else:
        starboard_channel_id = existing_channel.id
        await interaction.response.send_message(f"Starboard channel already exists.", ephemeral=True)

# Moderation commands group
mod_group = app_commands.Group(name="mod", description="Moderation and administration commands.")
bot.tree.add_command(mod_group)

@mod_group.command(name="kick", description="Kicks a member from the server.")
@is_whitelisted_and_admin()
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    try:
        await member.kick(reason=reason)
        await interaction.response.send_message(f'Successfully kicked {member.mention}.')
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to kick this member.")

@mod_group.command(name="ban", description="Bans a member from the server.")
@is_whitelisted_and_admin()
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    try:
        await member.ban(reason=reason)
        await interaction.response.send_message(f'Successfully banned {member.mention}.')
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to ban this member.")

@mod_group.command(name="clear", description="Deletes a specified number of messages.")
@is_whitelisted_and_admin()
async def clear(interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100]):
    try:
        await interaction.response.send_message(f'Deleting {amount} messages...', ephemeral=True)
        await interaction.channel.purge(limit=amount)
    except discord.Forbidden:
        await interaction.followup.send("I don't have permission to delete messages in this channel.")
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

@mod_group.command(name="warn", description="Sends a warning to a member and logs it.")
@is_whitelisted_and_admin()
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
    embed = discord.Embed(
        title="⚠️ Warning",
        description=f"**{member.mention}**, you have been warned for: `{reason}`",
        color=discord.Color.yellow()
    )
    try:
        await member.send(embed=embed)
        await interaction.response.send_message(f'Successfully warned {member.mention}.')
    except discord.Forbidden:
        await interaction.response.send_message(f'Could not send a DM to {member.mention}. The user may have DMs disabled.')
    
    log_channel = bot.get_channel(log_channel_id)
    if log_channel:
        embed_log = discord.Embed(
            title="⚠️ Warning",
            description=(
                f"**Warned User:** {member.mention}\n"
                f"**Warned By:** {interaction.user.mention}\n"
                f"**Reason:** `{reason}`"
            ),
            color=discord.Color.yellow()
        )
        await log_channel.send(embed=embed_log)

@mod_group.command(name="pin", description="Pins a specific message in the channel.")
@is_whitelisted_and_admin()
async def pin(interaction: discord.Interaction, message: discord.Message):
    try:
        await message.pin()
        await interaction.response.send_message("Message pinned successfully.")
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to pin messages.")

@mod_group.command(name="mute", description="Mutes a member in the server.")
@is_whitelisted_and_admin()
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
    muted_role = get(interaction.guild.roles, name=MUTED_ROLE_NAME)
    if muted_role:
        try:
            await member.add_roles(muted_role, reason=reason)
            await interaction.response.send_message(f'Successfully muted {member.mention}.')
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to add this role.")
        
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            embed = discord.Embed(
                title="🔇 Member Muted",
                description=(
                    f"**Muted User:** {member.mention}\n"
                    f"**Muted By:** {interaction.user.mention}\n"
                    f"**Reason:** `{reason}`"
                ),
                color=discord.Color.yellow()
            )
            await log_channel.send(embed=embed)
    else:
        await interaction.response.send_message(f"Could not find a role named '{MUTED_ROLE_NAME}'. Please create it first.", ephemeral=True)

@mod_group.command(name="unmute", description="Unmutes a member in the server.")
@is_whitelisted_and_admin()
async def unmute(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
    muted_role = get(interaction.guild.roles, name=MUTED_ROLE_NAME)
    if muted_role and muted_role in member.roles:
        try:
            await member.remove_roles(muted_role, reason=reason)
            await interaction.response.send_message(f'Successfully unmuted {member.mention}.')
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to remove this role.")
        
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            embed = discord.Embed(
                title="🔊 Member Unmuted",
                description=(
                    f"**Unmuted User:** {member.mention}\n"
                    f"**Unmuted By:** {interaction.user.mention}\n"
                    f"**Reason:** `{reason}`"
                ),
                color=discord.Color.green()
            )
            await log_channel.send(embed=embed)
    else:
        await interaction.response.send_message("This member is not muted.", ephemeral=True)

@mod_group.command(name="slowmode", description="Sets the slow mode for a channel.")
@is_whitelisted_and_admin()
async def slowmode(interaction: discord.Interaction, seconds: app_commands.Range[int, 0, 21600]):
    try:
        await interaction.channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(f'Slowmode has been set to `{seconds}` seconds.', ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to manage the channel.", ephemeral=True)

@mod_group.command(name="lock", description="Locks a channel to prevent members from sending messages.")
@is_whitelisted_and_admin()
async def lock(interaction: discord.Interaction, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    try:
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message(f"Channel {channel.mention} has been locked successfully.")
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to manage the channel.", ephemeral=True)

@mod_group.command(name="unlock", description="Unlocks a channel to allow members to send messages.")
@is_whitelisted_and_admin()
async def unlock(interaction: discord.Interaction, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    try:
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message(f"Channel {channel.mention} has been unlocked successfully.")
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to manage the channel.", ephemeral=True)

@mod_group.command(name="timeout", description="Temporarily mutes a member.")
@is_whitelisted_and_admin()
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: app_commands.Range[int, 1, 40320], reason: str = "No reason provided."):
    try:
        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await interaction.response.send_message(f"{member.mention} has been successfully timed out for {minutes} minutes due to: `{reason}`.")
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to timeout this member. Make sure the bot's role is higher than the member's role.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

@mod_group.command(name="add_role", description="Adds a role to a member.")
@is_whitelisted_and_admin()
async def add_role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    try:
        await member.add_roles(role)
        await interaction.response.send_message(f"Successfully added role `{role.name}` to {member.mention}.")
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to add this role.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

@mod_group.command(name="remove_role", description="Removes a role from a member.")
@is_whitelisted_and_admin()
async def remove_role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    try:
        await member.remove_roles(role)
        await interaction.response.send_message(f"Successfully removed role `{role.name}` from {member.mention}.")
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to remove this role.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

# Blacklist and Whitelist commands
@mod_group.command(name="blacklist_add", description="Adds a member to the blacklist.")
@is_whitelisted_and_admin()
async def blacklist_add(interaction: discord.Interaction, member: discord.Member):
    if member.id in BLACKLISTED_USERS:
        await interaction.response.send_message(f"{member.mention} is already in the blacklist.", ephemeral=True)
    else:
        BLACKLISTED_USERS.add(member.id)
        await interaction.response.send_message(f"Successfully added {member.mention} to the blacklist.", ephemeral=True)

@mod_group.command(name="blacklist_remove", description="Removes a member from the blacklist.")
@is_whitelisted_and_admin()
async def blacklist_remove(interaction: discord.Interaction, member: discord.Member):
    if member.id in BLACKLISTED_USERS:
        BLACKLISTED_USERS.remove(member.id)
        await interaction.response.send_message(f"Successfully removed {member.mention} from the blacklist.", ephemeral=True)
    else:
        await interaction.response.send_message(f"{member.mention} is not in the blacklist.", ephemeral=True)

@mod_group.command(name="blacklist_show", description="Displays the list of blacklisted members.")
@is_whitelisted_and_admin()
async def blacklist_show(interaction: discord.Interaction):
    if not BLACKLISTED_USERS:
        await interaction.response.send_message("There are no members in the blacklist currently.", ephemeral=True)
    else:
        members_list = []
        for user_id in BLACKLISTED_USERS:
            user = bot.get_user(user_id)
            if user:
                members_list.append(f"- {user.mention} (`{user.id}`)")
            else:
                members_list.append(f"- `Unknown User` (`{user_id}`)")
        
        embed = discord.Embed(
            title="Blacklist",
            description="\n".join(members_list),
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@mod_group.command(name="whitelist_add", description="Adds a member to the whitelist.")
@is_whitelisted_and_admin()
async def whitelist_add(interaction: discord.Interaction, member: discord.Member):
    if member.id in WHITELISTED_USERS:
        await interaction.response.send_message(f"{member.mention} is already in the whitelist.", ephemeral=True)
    else:
        WHITELISTED_USERS.add(member.id)
        await interaction.response.send_message(f"Successfully added {member.mention} to the whitelist.", ephemeral=True)

@mod_group.command(name="whitelist_remove", description="Removes a member from the whitelist.")
@is_whitelisted_and_admin()
async def whitelist_remove(interaction: discord.Interaction, member: discord.Member):
    if member.id in WHITELISTED_USERS:
        WHITELISTED_USERS.remove(member.id)
        await interaction.response.send_message(f"Successfully removed {member.mention} from the whitelist.", ephemeral=True)
    else:
        await interaction.response.send_message(f"{member.mention} is not in the whitelist.", ephemeral=True)

# Run the bot with your token.
# قم بتشغيل البوت باستخدام الرمز الخاص بك.
try:
    bot.run("YOUR_BOT_TOKEN_HERE")
except discord.LoginFailure:
    print("Error: The token is invalid. Please check it.")
except Exception as e:
    print(f"An error occurred while running the bot: {e}")

import texttable
import discord
import dbutils
import asyncio
import random
import pathlib
import datetime
import time

# create discord client
client = discord.Client()

# Set file that will stop this process
kill_file = pathlib.Path("/home/pi/discord/kill")

last_server_update = {}
ddb = dbutils.ServerDatabase()

# token from https://discordapp.com/developers
token = 'NDk4MTUxNzg3NzgyNDcxNjgy.DppwWA.57Ra07xIQijBpWVwcF3GDX4RsvU'

def find_channel(server, channel_name):
    for channel in server.channels:
        if channel.name == channel_name:
            return channel
    return None

def find_role(server, role_name):
    for role in server.roles:
        if role.name == role_name:
            return role
    return None

def create_table(table_text):
    try:
        table = texttable.Texttable(0)
        for row in table_text.split("|"):
            table.add_row(row.split(","))
        return "```" + table.draw() + "```"
    except Exception as e:
        raise(e)


@client.event
async def on_ready():
    try:
        # print bot information
        print("username --> " + client.user.name)
        print("userid --> " + client.user.id)
        print('Discord.py Version --> {}'.format(discord.__version__))
        print("Servers:")
        for server in client.servers:
            print("    {0} --> {1}".format(server.id, server.name))
            last_server_update[server.id] = int(time.time())
    except Exception as e:
        print(e)

@client.event
async def on_message(message):
    if message.content.startswith("!table "):
        try:
            table_text = message.content[7:]
            await client.send_message(message.channel, create_table(table_text))
        except Exception as e:
            await client.send_message(message.channel, "Error creating table: " + str(e))
    elif message.content == "!members" or message.content = "!posse":
        table_text = "MEMBER_NAME,JOINED_ON,STATUS"
        for member in message.server.members:
            # mlookup = discord.utils.find(lambda m: m.id == member.id, message.server.members)
            table_text += "|{0},{1},{2}".format(member.name, member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), member.status)
        await client.send_message(message.channel, create_table(table_text))
        print(message.server.default_role.mention)
    elif message.content.startswith("!battle "):
        thisplayer = message.author
        adversary = message.content[8:]
        adlookup = discord.utils.find(lambda m: m.mention == adversary, message.server.members)
        if adlookup is None:
            await client.send_message(message.channel, "```Usage: !battle <member>```")
        else:
            await client.send_message(message.channel, thisplayer.mention + " scores " + str(random.randint(1,100)) + ", " + adversary + " scores " + str(random.randint(1,100)))
    elif message.content == '!aliases':
        mems = ddb.get_all_server_member_system_aliases(message.server.id)
        table_text = "MEMBER_ID,NICKNAME,SYSTEM,ALIAS"
        removed_users = 0;
        for mem in mems:
            dmem = discord.utils.find(lambda m: m.id == mem[1], message.server.members)
            if dmem is None:
                # If a user has left (or was booted), then they would still exist
                # in the database, but won't be found on the server. So remove them
                # from the system aliases table altogether.
                ddb.remove_server_member_system_alias(message.server.id, mem[1], 'all')
                removed_users += 1
            else:
                table_text += "|{0},{1},{2},{3}".format(dmem.name, dmem.nick, mem[2], mem[3])
        await client.send_message(message.channel, create_table(table_text))
        if removed_users > 0:
            await client.send_message(message.channel, "WARNING: " + str(removed_users) + " user(s) were removed from the table (left/kicked/booted?)")
    elif message.content.startswith('!setalias'):
        usage = "```USAGE: !setalias <member> <xbox|ps4|pc> <alias>```"
        params = message.content.split()
        if len(params) != 4:
            await client.send_message(message.channel, usage)
        elif discord.utils.find(lambda m: m.mention == params[1], message.server.members) is None:
            await client.send_message(message.channel, "Could not find user " + params[1])
            await client.send_message(message.channel, usage)
        elif params[2] not in ('ps4', 'xbox', 'pc'):
            await client.send_message(message.channel, "Invalid system '" + params[2] + "'. system must be xbox, ps4 or pc")
            await client.send_message(message.channel, usage)
        else:
            dmem = discord.utils.find(lambda m: m.mention == params[1], message.server.members)
            ddb.update_server_member_system_alias(message.server.id, dmem.id, params[2], params[3])
            await client.send_message(message.channel, "Succesfully set user alias :smiley:")
    elif message.content.startswith('!rmalias'):
        usage = "```USAGE: !rmalias <member> <xbox|ps4|pc|all>```"
        params = message.content.split()
        if len(params) != 3:
            await client.send_message(message.channel, usage)
        elif discord.utils.find(lambda m: m.mention == params[1], message.server.members) is None:
            await client.send_message(message.channel, "Could not find user '" + params[1] + "'")
        elif params[2] not in ('ps4', 'xbox', 'pc','all'):
            await client.send_message(message.channel, "Invalid system '" + params[2] + "'. system must be xbox, ps4, pc, or all")
            await client.send_message(message.channel, usage)
        else:
            dmem = discord.utils.find(lambda m: m.mention == params[1], message.server.members)
            ddb.remove_server_member_system_alias(message.server.id, dmem.id, params[2])
            await client.send_message(message.channel, "Succesfully removed user :)")

@client.event
async def on_member_join(member):
    # await client.send_message(general_chat_channel, "Marshal Mobot welcomes you " + member.mention + ". Now play nice y'hear?")
    # await client.add_roles(member, (stranger_role))
    pass

async def maintenance_loop():
    await client.wait_until_ready()
    keep_running = True

    while keep_running:
        await asyncio.sleep(30)

        if kill_file.is_file():
            print("Kill file activated. Quitting.")
            await client.logout()
            kill_file.unlink() # unlink = delete file
            keep_running = False

# start bot
client.loop.create_task(maintenance_loop())
client.run(token)

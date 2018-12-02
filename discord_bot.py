import texttable
import urllib.request
import discord
import discord_config
import dbutils
import asyncio
import random
import pathlib
import datetime
import time
import game_four

# create discord client
client = discord.Client()

# Set file that will stop this process
kill_file = pathlib.Path(discord_config.KILL_FILE)

last_server_update = {}
ddb = dbutils.ServerDatabase()
g4 = game_four.GameFour(ddb)

# token from https://discordapp.com/developers
token = discord_config.DISCORD_OATH_TOKEN

# Uses the table module to split a string into columns seperated by commas, with
# rows seperated by the | symbol.
def create_table(table_text):
    try:
        table = texttable.Texttable(0)
        for row in table_text.split("|"):
            table.add_row(row.split(","))

        # Not massively happy about this, but Discord has a 2,000 character
        # limit per message. So I will split up the table into a list, then 
        # rejoin it into lists of 20 rows at a time. That way, separate smaller
        # messages can be sent in quick succession.
        split_table = table.draw().splitlines()
        n = 20 # split into 20 rows at a time.
        split_table_groups = [ split_table[i:i+n] for i in range(0, len(split_table), n) ]

        # They're now in groups of n rows, but we need to re-add the \n that
        # splitlines removed earlier.
        table_strings = []
        for table_group in split_table_groups:
            table_strings.append("\n".join(table_group))

        return table_strings
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
            # last_server_update[server.id] = int(time.time())
    except Exception as e:
        print(e)


# Displays a random number for two players.
async def battle(message):
    thisplayer = message.author
    adversary = message.content[8:]
    adlookup = discord.utils.find(lambda m: m.mention == adversary, message.server.members)
    if adlookup is None:
        await client.send_message(message.channel, "```Usage: !battle <member>```")
    else:
        await client.send_message(message.channel, thisplayer.mention + " scores " + str(random.randint(1,100)) + ", " + adversary + " scores " + str(random.randint(1,100)))


def get_member_name(server, memid):
    try:
        mem = discord.utils.find(lambda m: m.id == memid, server.members)
        return mem.name
    except Exception as ex:
        return ''


def get_member_nickname(server, memid):
    try:
        mem = discord.utils.find(lambda m: m.id == memid, server.members)
        return mem.nick if mem.nick is not None else ''
    except Exception as ex:
        return ''


# Shows the PS4/Xbox/PC alias for a given user as set using the !setalias command.
async def show_aliases(message):
    params = message.content.split()
    systype = params[1] if len(params) == 2 else 'all'
    mems = ddb.get_all_server_member_system_aliases(message.server.id, system_type=systype)
    mems.sort(key=lambda mem: get_member_nickname(message.server,mem[1]).lower())
    table_text = "MEMBER_ID,NICKNAME,SYSTEM,ALIAS" if systype == 'all' else "MEMBER_ID,NICKNAME,ALIAS"
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
            if systype == 'all':
                table_text += "|{0},{1},{2},{3}".format(dmem.name, dmem.nick, mem[2], mem[3])
            else:
                table_text += "|{0},{1},{2}".format(dmem.name, dmem.nick, mem[3])

    # create_table returns a list of seperate strings to avoid the 2,000 character limit.
    table_strings = create_table(table_text)

    await client.send_message(message.channel, "```System aliases (" + systype + ")```")

    for table_string in table_strings:
        await client.send_message(message.channel, "```" + table_string + "```")

    if removed_users > 0:
        await client.send_message(message.channel, "WARNING: " + str(removed_users) + " user(s) were removed from the table (left/kicked/booted?)")


# For the given user and system, set their id in the database.
async def set_alias(message):
    usage = "```USAGE: !setalias <member> <xbox|ps4|pc> <alias>```"
    params = message.content.split()
    if not message.author.server_permissions.administrator:
        await client.send_message(message.channel, "Sorry " + message.author.mention + ", only administrators can do this :frowning:")
    elif len(params) != 4:
        await client.send_message(message.channel, usage)
    # elif discord.utils.find(lambda m: m.mention == params[1], message.server.members) is None:
    elif params[2] not in ('ps4', 'xbox', 'pc'):
        await client.send_message(message.channel, "Invalid system '" + params[2] + "'. system must be xbox, ps4 or pc")
        await client.send_message(message.channel, usage)
    elif len(message.mentions) != 1:
        await client.send_message(message.channel, "You must state the user in the first parameter.")
        await client.send_message(message.channel, usage)
    else:
        # dmem = discord.utils.find(lambda m: m.mention == params[1], message.server.members)
        dmem = message.mentions[0]
        ddb.update_server_member_system_alias(message.server.id, dmem.id, params[2], params[3])
        await client.send_message(message.channel, "Succesfully set user alias :smiley:")


# Remove the user alias from the database from the given system (or 'all' for all systems).
async def remove_alias(message):
    usage = "```USAGE: !rmalias <member> <xbox|ps4|pc|all>```"
    params = message.content.split()
    if not message.author.server_permissions.administrator:
        await client.send_message(message.channel, "Sorry " + message.author.mention + ", only administrators can do this :frowning:")
    elif len(params) != 3:
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


async def new_game_four(message):
    if len(message.mentions) != 1:
        await client.send_message(message.channel, "You need to add 1 person to play with " + message.author.mention)
    elif message.mentions[0].bot:
        await client.send_message(message.channel, "You can't play against a bot " + message.author.mention + ". They'd never respond!")
    else:
        try:
            g4game = g4.new_game(message.server.id, message.channel.id, message.mentions[0].id, message.author.id)
            await client.send_message(message.channel, "Game " + str(g4game['game_id']) + " created")
            await show_game_four_board(g4game['game_id'], message)
        except Exception as ex:
            await client.send_message(message.channel, str(ex))


async def maybe_play(message):
    g4game = g4.find_active_player_game(message.server.id, message.author.id)
    if g4game is not None:
        try:
            # Note that I'm casting the message.content to an int, so I'm assuming that's all been done!
            g4.drop_chip(message.server.id, g4game['game_id'], int(message.content)-1)
            await show_game_four_board(g4game['game_id'], message)
        except Exception as ex:
            await client.send_message(message.channel, "EXCEPTION: " + str(ex)) 


async def show_game_four_board(game_id, message):
    g4game = g4.get_game(message.server.id, game_id)
    new_board = g4.display_board(message.server.id, g4game['game_id'])
    # I do NOT know why I have to wrap the player1_id and player2_id in strings. They're stored as strings in the database.
    player1 = discord.utils.find(lambda m: m.id == str(g4game['player1_id']), message.server.members)
    player2 = discord.utils.find(lambda m: m.id == str(g4game['player2_id']), message.server.members)
    status_text = game_four.GameFour.STATUSES[g4game['status']]
    # await client.send_message(message.channel, "```{0}\nPlayer 1 (X): {1}\nPlayer 2 (O): {2}\n{3}```".format(new_board, player1.name, player2.name, status_text))
    image_file = g4.draw_board_image(g4game['board'], player1.name, player2.name, status_text)
    await client.send_file(message.channel, image_file)

@client.event
async def on_message(message):
    if message.content.startswith("!battle "):
        await battle(message)
    elif message.content.startswith('!aliases') or message.content.startswith('!posse'):
        await show_aliases(message)
    elif message.content.startswith('!setalias'):
        await set_alias(message)
    elif message.content.startswith('!rmalias'):
        await remove_alias(message)
    elif message.content.startswith('!gamefour '):
        await new_game_four(message)
    elif len(message.content) == 1 and message.content.isdigit():
        await maybe_play(message)


@client.event
async def on_member_join(member):
    general_channel = discord.utils.find(lambda c: c.name == 'general', member.server.channels)
    if general_channel is not None:
        await client.send_message(general_channel, "Marshal Mobot welcomes you " + member.mention + ". Now play nice y'hear?")
        stranger_role = discord.utils.find(lambda r: r.name == 'Stranger', member.server.roles)
        await client.add_roles(member, (stranger_role))


async def end_inactive_games():
    terminated_games = g4.end_inactive_games(180)
    for terminated_game in terminated_games:
        game_server = discord.utils.find(lambda s: s.id == str(terminated_game[0]), client.servers)
        game_channel = discord.utils.find(lambda c: c.id == str(terminated_game[2]), game_server.channels)
        await client.send_message(game_channel, terminated_game[3])


async def maintenance_loop():
    await client.wait_until_ready()
    keep_running = True

    while keep_running:
        await asyncio.sleep(60)
        print("Maintenance run " + str(datetime.datetime.now()), flush=True)

        await end_inactive_games()

        if kill_file.is_file():
            print("Kill file activated. Quitting.")
            await client.logout()
            kill_file.unlink() # unlink = delete file
            keep_running = False


try:
    urllib.request.urlopen('https://www.google.com')
    print("Internet Connection confirmed. Starting Client...")
except Exception as ex:
    print("Unable to connect to the internet. Possibly too soon after server restart? Sleeping for 30 seconds")
    time.sleep(30)
    print("OK, trying again. If it fails now... Who knows!")

# start bot
client.loop.create_task(maintenance_loop())
client.run(token)

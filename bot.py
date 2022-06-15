# To-Do Bot for Discord
# Version 1.0 [6/15/22]
# Created by Nate MacLeod (natemacleod.github.io)

import discord
from discord.ext import pages
import asyncio
import motor
import motor.motor_asyncio
import os
from dotenv import load_dotenv

# -------- SETUP --------

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
MONGO_CONN_STR = os.getenv('MONGO_CONN_STR')

# MongoDB setup
conn_str = MONGO_CONN_STR
client = motor.motor_asyncio.AsyncIOMotorClient(
    conn_str, serverSelectionTimeoutMS=5000)
async def get_server_info():
    try:
        print(await client.server_info())
    except Exception:
        print("Unable to connect to the server.")
loop = asyncio.get_event_loop()
loop.run_until_complete(get_server_info())

# Handles guild ID errors (needed for all commands)
async def getGID(ctx):
    g = ctx.guild
    if g is None:
        await ctx.respond("This channel is not in a guild.")
        return False
    else:
        return g.id

# comparison function for the leaderboard
def comparePts(a): return a['pts']

# initialize bot and DB
bot = discord.Bot()
db = client.to_do_bot

# Print message when bot account logs in
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


# -------- COMMANDS --------

@bot.slash_command(name="new", description="Create a new list for this server", guild_ids=[790243425567768638])
async def new(ctx):
    gid = await getGID(ctx)
    if gid:
        doc = await db.lists.find_one({'id': gid})
        if doc is None:
            newdoc = {'id': gid, 'tasks': [], 'users': []}
            result = await db.lists.insert_one(newdoc)
            await ctx.respond("List created.")
        else:
            await ctx.respond("A list for this server already exists.")

@bot.slash_command(name="add", description="Add a task to this server's list", guild_ids=[790243425567768638])
async def add(ctx, task, date=False):
    gid = await getGID(ctx)
    if gid:
        doc = await db.lists.find_one({'id': gid})
        if doc is None:
            await ctx.respond("No list exists for this server. Try running /new.")
        else:
            tasks = doc['tasks']
            t = {'name': task, 'date': date, 'subs': []}
            tasks.append(t)
            await db.lists.update_one({'id': gid}, {'$set': {'tasks': tasks}})
            await ctx.respond("Task " + str(task) + " added to list as task #" + str(len(tasks)) + ".")

@bot.slash_command(name="addsubtask", description="Add a subtask to task #[task] on this server's list", guild_ids=[790243425567768638])
async def addsubtask(ctx, task, subtask, date=False):
    id = int(id)
    gid = await getGID(ctx)
    if gid:
        doc = await db.lists.find_one({'id': gid})
        if doc is None:
            await ctx.respond("No list exists for this server. Try running /new.")
        else:
            tasks = doc['tasks']
            if len(tasks) < id:
                await ctx.respond("Task " + str(id) + " does not exist.")
            else:
                t = {'name': subtask, 'date': date}
                tasks[id - 1]['subs'].append(t)
                await db.lists.update_one({'id': gid}, {'$set': {'tasks': tasks}})
                await ctx.respond("Task " + str(subtask) + " added to list as task #" + str(id) + "." + str(len(tasks[id - 1]['subs'])) + ".")

@bot.slash_command(name="list", description="Display this server's list", guild_ids=[790243425567768638])
async def list(ctx):
    gid = await getGID(ctx)
    if gid:
        doc = await db.lists.find_one({'id': gid})
        if doc is None:
            await ctx.respond("No list exists for this server. Try running /new.")
        else:
            tasks = doc['tasks']
            pagelist = ["**Task List** *(" + str(len(tasks)) + " tasks)*\n"]
            onPage = 0
            pageNum = 0

        for i in range(0, len(tasks)):
            pagelist[pageNum] += "**" + str(i + 1) + "**. " + tasks[i]['name']
            if tasks[i]['date'] is not False:
                pagelist[pageNum] += " - " + tasks[i]['date']
            pagelist[pageNum] += "\n"
            onPage += 1
            for j in range(0, len(tasks[i]['subs'])):
                pagelist[pageNum] += "    **" + \
                    str(i + 1) + "." + str(j + 1) + \
                    "**. " + tasks[i]['subs'][j]['name']
                if tasks[i]['subs'][j]['date'] is not False:
                    pagelist[pageNum] += " - " + tasks[i]['subs'][j]['date']
                pagelist[pageNum] += "\n"
                onPage += 1
            if onPage >= 10 and i < len(tasks) - 1:
                pagelist.append(
                    "**Task List** *(" + str(len(tasks)) + " tasks)*\n")
                pageNum += 1
                onPage = 0
        paginator = pages.Paginator(pages=pagelist, loop_pages=True)
        await paginator.respond(ctx.interaction, ephemeral=False)

# Removes a task from the list (needed for both /remove and /complete). 
# Returns False if there is an error
async def removetask(ctx, id):
    id = float(id)
    gid = await getGID(ctx)
    if gid:
        doc = await db.lists.find_one({'id': gid})
        if doc is None:
            await ctx.respond("No list exists for this server. Try running /new.")
            return False
        else:
            tasks = doc['tasks']
            removed = ""
            if len(tasks) > id - 1:
                if id % 1 == 0:
                    id = int(id)
                    removed = tasks.pop(id - 1)
                    await db.lists.update_one({'id': gid}, {'$set': {'tasks': tasks}})
                    return "Task " + removed['name'] + " removed from list."
                else:
                    sub = str(id)
                    for i in range(0, len(sub)):
                        if sub[i] == '.':
                            sub = int(sub[(i + 1):len(sub)])
                            break
                    id = int(id)
                    removed = tasks[id - 1]['subs'].pop(sub - 1)
                    await db.lists.update_one({'id': gid}, {'$set': {'tasks': tasks}})
                return "Subtask " + removed['name'] + " removed from list."
            else:
                await ctx.respond("Task " + (str(id) if id % 1!= 0 else str(int(id))) + " does not exist.")
                return False
    else: return False

@bot.slash_command(name="remove", description="Removes a task from this server's list", guild_ids=[790243425567768638])
async def remove(ctx, id):
    res = await removetask(ctx, id)
    if res:
        ctx.respond(res)

@bot.slash_command(name="complete", description="Removes a task from this server's list and awards a point", guild_ids=[790243425567768638])
async def complete(ctx, id):
    res = await removetask(ctx, id)
    if res:
        gid = await getGID(ctx)
        if gid:
            doc = await db.lists.find_one({'id': gid})
            userIndex = -1
            users = doc['users']
            for i in range(0, len(doc['users'])):
                if users[i]['id'] == ctx.author.id:
                    userIndex = i
                    break

            if userIndex >= 0:
                users[userIndex]['pts'] += 1
            else:
                users.append(
                    {'id': ctx.author.id, 'name': ctx.author.name, 'pts': 1})

            await db.lists.update_one({'id': gid}, {'$set': {'users': users}})
            await ctx.respond(res + "\nPoint awarded to <@" + str(ctx.author.id) + ">. Your current score is " + str(users[userIndex]['pts']) + ".")

@bot.slash_command(name="deletelist", description="Completely deletes this server's list", guild_ids=[790243425567768638])
async def deletelist(ctx):
    gid = await getGID(ctx)
    if gid:
        doc = await db.lists.find_one({'id': gid})
        if doc is None:
            await ctx.respond("No list exists for this server. Try running /new.")
        else:
            await db.lists.delete_one({'id': gid})
            await ctx.respond("List deleted.")

@bot.slash_command(name="lb", description="Shows the leaderboard for the server", guild_ids=[790243425567768638])
async def lb(ctx, top="10"):
    gid = await getGID(ctx)
    if gid:
        doc = await db.lists.find_one({'id': gid})
        if doc is None:
            await ctx.respond("No list exists for this server. Try running /new.")
        else:
            doc['users'].sort(reverse=True, key=comparePts)
            pagelist = ["**Leaderboard** *(top " + top + ")*\n"]
            onPage = 0
            pageNum = 0
            top = int(top)
            for i in range(0, min(top, len(doc['users']))):
                pagelist[pageNum] += "**" + str(i + 1) + "**. " + doc['users'][i]['name'] + \
                    " *(" + str(doc['users'][i]['pts']) + " points)*\n"
                onPage += 1
                if onPage >= 10 and i < min(top, len(doc['users'])) - 1:
                    onPage = 0
                    pageNum += 1
                    pagelist.append("**Leaderboard** *(top " + top + ")*\n")
            paginator = pages.Paginator(pages=pagelist, loop_pages=True)
            await paginator.respond(ctx.interaction, ephemeral=False)

# Run bot
bot.run(DISCORD_TOKEN)
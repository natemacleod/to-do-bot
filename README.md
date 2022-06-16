# To-Do Bot
A to-do list bot for Discord

(Note: This bot is currently not active. To use it, follow the instructions below.)

This bot allows server members to collaborate and compete to finish tasks on a shared to-do list.

## Commands
- /new: Creates a new list for the server.
- /add: Adds a task to your list.
- /addsubtask: Adds a subtask to a task on your list.
- /list: Displays your list.
- /complete: Removes a task from your list, awarding a point to the user who completed it.
- /remove: Removes a task from your list.
- /lb: Displays a leaderboard of server members, ranked by their total points.
- /deletelist: Completely deletes your list from the database.

## Setup
To use this bot:
1. Set up a new application in Discord's developer portal
2. Invite the bot to a server
3. Clone this repo
4. Run `pip install py-cord --pre motor asyncio python-dotenv` (this will install all needed libraries)
5. Create a .env file following the example. You will need a MongoDB server (can be local, Atlas, etc.)
6. Run bot.py

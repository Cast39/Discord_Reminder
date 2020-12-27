import discord
import pickle

from guild import Guild_Manager
from reminder import Reminder

# add by going to https://discord.com/oauth2/authorize?scope=bot&permissions=0&client_id=792429161301671996

## settings

settings = {
    "permissioninteger": 68672,
    "commandprefix": "$"
}

# constants
helpmessage = """***How to use me:***

all users can follow reminders. These reminders will remind you to send specific messages.
Those reminders need to be created by Admins.

 
***[User]***
***$reminderlist*** -> shows you all timers present on this server
***$follow [timer_name]*** -> 
***$unfollow [timer]*** ->


***[Admin]***
***$createreminder [name] [time] [massage]***
will remind all players which followed this reminder to send [message] if it hasn't been sent in [time] in the channel where this command was sent. 

The time can for example be: 1m (minimum) | 1.6h | 2d | 1w
As an example: $createreminder 2h !d bump

***$deletereminder [name]***
will delete a reminder
you can add ***publish*** at the end to inform all users who followed this reminder that the reminder is no longer active.
"""

client = discord.Client()


class ReminderBot:
    def __init__(self, token):
        self.token = token
        self.savefile = "reminderbot.save"
        self.guilds = Guild_Manager()

    def load_save(self):
        with open(self.savefile, "rb") as f:
            self.guilds = pickle.load(f)

    def save_guilds(self):
        with open(self.savefile, "wb") as f:
            pickle.dump(self.guilds, f)

    def start(self, savefile=None):
        if savefile is not None:
            self.savefile = savefile
        try:
            self.load_save()

        except:
            print("Couldn't find a previous save. Creating a new instead")

            self.guilds = Guild_Manager()
            try:
                self.save_guilds()
            except:
                print("Error! Could not create a savefile")
                return

        client.run(self.token)

    async def on_ready(self):
        print('We have logged in as {0.user}\n'.format(client))

    async def on_message(self, message):
        if message.author == client.user:
            return

        textmessage = message.content

        guild = self.guilds.get_guild(message.guild.id)
        if guild is None:
            self.guilds.add_guild(message.guild.id)

            guild = self.guilds.get_guild(message.guild.id)
            print(f'added Guild {message.guild.id}')

        # filter for commands
        if textmessage.startswith(settings['commandprefix']):
            command = textmessage[len(settings['commandprefix']):].split(" ")
            if command[0] == "help":
                await message.channel.send(helpmessage)

            # createreminder
            elif command[0] == "createreminder" and len(command) >= 4:
                if guild.add_reminder(Reminder(command[1], command[2], command[3], message.channel.id)):
                    self.save_guilds()
                    await message.add_reaction('✅')
                else:
                    await message.add_reaction('❌')

            # deletereminder
            elif command[0] == "deletereminder" and (len(command) == 2 or len(command) == 3):
                publish_deletion = len(command) == 3 and command[2] == "publish"
                if publish_deletion:
                    subscribers = guild.get_remindner(command[1]).subscribers

                if guild.remove_reminder(command[1]):
                    await message.add_reaction('✅')
                    self.save_guilds()
                    if publish_deletion:
                        pass  # TODO message subscribers
                else:
                    await message.add_reaction('❌')

            # reminderlist
            elif command[0] == "reminderlist" and len(command) == 1:
                response = "***Reminders of this Server:***\n"
                for reminder_name in guild.reminders:
                    response += f'\n{reminder_name}'
                await message.channel.send(response)

            # follow
            elif command[0] == "follow" and len(command) == 2:
                reminder = guild.get_reminder(command[1])
                if reminder is None or reminder.is_subscriber(message.author.id):
                    await message.add_reaction('❌')
                else:
                    reminder.add_subscriber(message.author.id)
                    self.save_guilds()
                    await message.add_reaction('✅')

            # unfollow
            elif command[0] == "unfollow" and len(command) == 2:
                reminder = guild.get_reminder(command[1])
                if reminder is None or not reminder.is_subscriber(message.author.id):
                    await message.add_reaction('❌')
                else:
                    reminder.remove_subscriber(message.author.id)
                    self.save_guilds()
                    await message.add_reaction('✅')

            else:
                await message.add_reaction('❌')

    async def on_guild_join(self, guild):
        print("Oh yummy a new Server")
        self.guilds.add_guild(guild.id)
        self.save_guilds()

    async def on_guild_remove(self, guild):
        print("Oh no...")
        self.guilds.remove_guild(guild.id)
        self.save_guilds()
        print("Anyway")


reminderbot = ReminderBot('NzkyNDI5MTYxMzAxNjcxOTk2.X-dlKg.xBbtOcCbacL5GM9kYJ5UV_4Q_fA')


@client.event
async def on_ready():
    await reminderbot.on_ready()


@client.event
async def on_message(message):
    await reminderbot.on_message(message)


@client.event
async def on_guild_join(guild):
    await reminderbot.on_guild_join(guild)


@client.event
async def on_guild_remove(guild):
    await reminderbot.on_guild_remove(guild)


reminderbot.start()

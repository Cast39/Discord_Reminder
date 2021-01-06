import discord
import pickle
import asyncio
import re

from guild import Guild_Manager
from reminder import Reminder

# you need to create a file called "discordtoken.py" with one line:
# token = [Discord Bot Token]
from discordtoken import token

# add by going to https://discord.com/oauth2/authorize?scope=bot&permissions=0&client_id=792429161301671996

# settings

settings = {
    "permissioninteger": 68672,
    "commandprefix": "*",
    "reminder_check_interval": 15
}


# constants
helpmessage = f'**How to use me:**\n\
\n\
all users can follow reminders. These reminders will remind you to send specific messages.\n\
Those reminders need to be created by Admins.\n\
\n\
\n\
__[User]__\n\
**\\{settings["commandprefix"]}listreminders** -> shows you all timers present on this server\n\
**\\{settings["commandprefix"]}follow [reminder_name]** -> \n\
**\\{settings["commandprefix"]}unfollow [reminder]** ->\n\
**\\{settings["commandprefix"]}listsubscribers [reminder]** ->\n\
\n\
\n\
__[Admin]__\n\
**\\{settings["commandprefix"]}createreminder [name] [time] [massage]**\n\
will remind all players which followed this reminder to send [message] if it hasn\'t been sent in [time] in the channel where this command was sent. \n\
\n\
The time can for example be: 1m (minimum) | 1h | 2d | 1w\n\
As an example: {settings["commandprefix"]}createreminder 2h !d bump\n\
\n\
**\\{settings["commandprefix"]}deletereminder [name]**\n\
will delete a reminder\n\
you can add *publish* at the end to inform all users who followed this reminder that the reminder is no longer active.\n\
'


class ReminderBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.savefile = "reminderbot.save"

        self.timepattern = re.compile("\\d+[mMhHsSdDtT]")
        self.guild_manager = Guild_Manager()

        self.bg_task = self.loop.create_task(self.checkreminders())

    def load_save(self):
        with open(self.savefile, "rb") as f:
            self.guild_manager = pickle.load(f)

    def save_guilds(self):
        with open(self.savefile, "wb") as f:
            pickle.dump(self.guild_manager, f)

    def setup(self, savefile=None):
        if savefile is not None:
            self.savefile = savefile
        try:
            self.load_save()

        except:
            print("Couldn't find a previous save. Creating a new instead")

            self.guild_manager = Guild_Manager()
            try:
                self.save_guilds()
            except:
                print("Error! Could not create a savefile")
                return

    async def checkreminders(self):
        await self.wait_until_ready()
        guild = None
        reminder = None
        while not self.is_closed():
            reminder = None
            for guild_id in self.guild_manager.guilds:
                guild = self.guild_manager.guilds[guild_id]
                print(f'Checking Reminder for Guild [{self.get_guild(guild.guildid).name}]')
                for reminder_name in guild.reminders:
                    reminder = guild.get_reminder(reminder_name)
                    print(f'status of [{reminder_name}]: ', end="")
                    if reminder.is_it_time_to_remind():
                        if reminder.get_reminded():
                            print(f'already reminded, waiting for \'{reminder.message}\'')
                        else:
                            print(f'reminding right now')

                            message = f'**{reminder_name}** IT\'S TIME'
                            if len(reminder.subscribers) != 0:
                                message += " ("
                                for userid in reminder.subscribers:
                                    user = self.get_user(userid)
                                    #print(f'{user}\n{dir(user)}\n{type(user)}')
                                    if user is None:
                                        print(f'THE ANOMALY: USER {userid} IS NOT IN THE DATABASE')
                                    else:
                                        message += f'{user.mention} '
                                message += ")"
                            await self.get_channel(reminder.channelid).send(message)
                            reminder.set_reminded()
                            print()

                    else:
                        print('fine :)')
                print()

            if reminder is not None:
                self.save_guilds()
                print()

            await asyncio.sleep(settings['reminder_check_interval'])

    async def on_ready(self):
        print('We have logged in as {0.user}\n'.format(self))

    async def on_message(self, message):
        if message.author == self.user:
            return

        textmessage = message.content

        guild = self.guild_manager.get_guild(message.guild.id)
        if guild is None:
            self.guild_manager.add_guild(message.guild.id)

            guild = self.guild_manager.get_guild(message.guild.id)
            print(f'added Guild {message.guild.id}')

        # filter for commands
        if textmessage.startswith(settings['commandprefix']):
            command = textmessage[len(settings['commandprefix']):].split(" ")
            if command[0] == "help":
                await message.channel.send(helpmessage)

            # createreminder
            elif command[0] == "createreminder" and len(command) >= 4:
                searchresult = self.timepattern.search(command[2])

                if searchresult is None:
                    await message.channel.send(f'Invalid time pattern!')
                else:
                    timestring = command[2][searchresult.start():searchresult.end()]
                    listencommand = " ".join(command[3:])

                    reminder = Reminder(command[1], timestring, listencommand, message.channel.id)

                    if guild.add_reminder(reminder):
                        guild.get_reminder(command[1]).add_subscriber(message.author.id)
                        self.save_guilds()
                        await message.channel.send(
                            f'Created reminder called **{command[1]}** for **{listencommand}** in channel **{message.channel.name}** every **{command[2]}**!')
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

            # listreminders
            elif command[0] == "listreminders" and len(command) == 1:
                response = ""
                if len(guild.reminders) == 0:
                    response = "**Reminders of this Server:**\n\n no reminders yet"
                else:
                    response = "**Reminders of this Server:**\n\n" + "\n".join(guild.reminders)
                await message.channel.send(response)

            # listsubscribers
            elif command[0] == "listsubscribers" and len(command) == 2:
                reminder = guild.get_reminder(command[1])
                if reminder is None:
                    await message.channel.send(f'invalid name {command[1]}')
                else:
                    response = f'**Subscribers of {command[1]}**\n'

                    for subscriber_id in reminder.subscribers:
                        user = self.get_user(subscriber_id)
                        if user is None:
                            print(f'THE ANOMALY: USER {subscriber_id} IS NOT IN THE DATABASE')
                        else:
                            response += f'\n{user.name}'

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
            if guild.check_for_reminder_updates(message):
                await message.add_reaction('✅')

    async def on_guild_join(self, guild):
        print("Oh yummy a new Server")
        self.guild_manager.add_guild(guild.id)
        self.save_guilds()

    async def on_guild_remove(self, guild):
        print("Oh no...")
        self.guild_manager.remove_guild(guild.id)
        self.save_guilds()
        print("Anyway")


reminderbot = ReminderBot()

reminderbot.setup()
reminderbot.run(token)

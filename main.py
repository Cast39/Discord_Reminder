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
    "reminder_check_interval": 60,
    "botadmins": [391218106166542337]
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
    def __init__(self, savefile=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if savefile is None:
            self.savefile = "reminderbot.save"
        else:
            self.savefile = savefile

        print(f'using savefile \'{self.savefile}\'')
        try:
            print('loading Save')
            self.load_save()
            print('Done!')

        except:
            print("Couldn't find a previous save. Creating a new instead")

            self.guild_manager = Guild_Manager()
            try:
                self.save_guilds()
            except:
                print("Error! Could not create a savefile")
                self.logout()
                return

        self.timepattern = re.compile("\\d+[mMhHsSdDtT]")

        self.bg_task = self.loop.create_task(self.checkreminders())

    def load_save(self):
        with open(self.savefile, "rb") as f:
            self.guild_manager = pickle.load(f)

    def save_guilds(self):
        print('[INFO] saving guilds')
        with open(self.savefile, "wb") as f:
            pickle.dump(self.guild_manager, f)

        print('[INFO] Done!')

    async def checkreminders(self):
        await self.wait_until_ready()
        guild = None
        reminder = None
        while not self.is_closed():
            reminder = None
            for guild_id in self.guild_manager.guilds:
                guild = self.guild_manager.guilds[guild_id]
                try:
                    print(f'Checking Reminders for Guild [{self.get_guild(guild.guildid).name}]')
                except:
                    print(f'Guild was not found, skipping Guild {guild_id}\n')
                    continue

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
                                    # if user is None:
                                    #    print(f'THE ANOMALY: USER {reminder.subscribers[userid]} IS NOT IN THE DATABASE')
                                    message += f'{reminder.subscribers[userid][1]} '
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
                        guild.get_reminder(command[1]).add_subscriber(message.author.id, message.author.display_name,
                                                                      message.author.mention)
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
                    if len(reminder.subscribers) == 0:
                        response += "\nno subscribers yet"
                    else:
                        for subscriber_id in reminder.subscribers:
                            # if user is None:
                            #    print(f'THE ANOMALY: USER {reminder.subscribers[subscriber_id]} IS NOT IN THE DATABASE')
                            response += f'\n{reminder.subscribers[subscriber_id][0]}'

                    await message.channel.send(response)


            # follow
            elif command[0] == "follow" and len(command) == 2:
                reminder = guild.get_reminder(command[1])
                if reminder is None or reminder.is_subscriber(message.author.id):
                    await message.add_reaction('❌')
                else:
                    reminder.add_subscriber(message.author.id, message.author.display_name, message.author.mention)
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

            # SECRET COMMANDS
            elif message.author.id in settings['botadmins']:
                # check
                if command[0] == "check" and len(command) == 2:
                    user = self.get_user(int(command[1]))
                    if user is None:
                        await message.channel.send("User not Found")
                    else:
                        await message.channel.send(f'User Found: {user.name}')

                # save
                elif command[0] == "save" and len(command) == 1:
                    self.save_guilds()
                    await message.add_reaction('✅')

                # stop bot
                elif command[0] == 'stop' and len(command) == 1:
                    await message.add_reaction('✅')
                    self.bg_task.cancel()
                    self.save_guilds()
                    await self.close()

        else:
            if guild.check_for_reminder_updates(message):
                await message.add_reaction('✅')

    async def on_guild_join(self, guild):
        print("Oh yummy a new Server")
        self.guild_manager.add_guild(guild.id)
        self.save_guilds()

    async def on_guild_unavailable(self, guild):
        print("Oh no...")
        self.guild_manager.remove_guild(guild.id)
        self.save_guilds()
        print("Anyway")


reminderbot = ReminderBot()

reminderbot.run(token)

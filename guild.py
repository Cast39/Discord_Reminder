import time


class Guild_Manager:
    def __init__(self):
        self.guilds = {}

    def add_guild(self, guildid):
        if guildid in self.guilds:
            return False
        else:
            self.guilds[guildid] = Guild(guildid)

    def get_guild(self, guild_id):
        for guild in self.guilds.values():
            if guild.guildid == guild_id:
                return guild
        return None

    def remove_guild(self, guild_id):
        guild = self.get_guild(guild_id)

        if guild is not None:
            return True

        return False


class Guild:
    def __init__(self, guildid):
        self.guildid = guildid
        self.reminders = {}
        self.jointime = time.time()
        self.leavetime = 0

    def get_reminder(self, reminder_name):
        if reminder_name in self.reminders:
            return self.reminders[reminder_name]
        return None

    def add_reminder(self, reminder):
        if self.get_reminder(reminder.name) is None:
            self.reminders[reminder.name] = reminder
            return True
        return False

    def remove_reminder(self, reminder_name):
        if reminder_name in self.reminders:
            self.reminders.pop(reminder_name)
            return True
        return False

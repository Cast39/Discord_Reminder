import time


class Reminder:
    def __init__(self, name, message, interval, channel, starttime=0):
        self.name = name
        self.message = message
        self.interval = interval
        self.channel = channel
        self.lasttime = starttime
        self.subscribers = []

    def add_subscriber(self, user_id):
        if not user_id in self.subscribers:
            self.subscribers.append(user_id)

    def remove_subscriber(self, user_id):
        if user_id in self.subscribers:
            self.subscribers.pop(self.subscribers.index(user_id))

    def is_subscriber(self, user_id):
        return user_id in self.subscribers

    def update_last_time(self):
        self.lasttime = time.time()

    def is_it_time_to_remind(self):
        return self.lasttime + self.interval >= time.time()

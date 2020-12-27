import time


class Reminder:
    def __init__(self, name, interval, message, channelid):
        self.name = name
        self.message = message
        self.interval = 10  # TODO interval
        self.channelid = channelid

        self.nexttime = time.time() + self.interval
        self.subscribers = []
        self.is_reminded = False

    def add_subscriber(self, user_id):
        if not user_id in self.subscribers:
            self.subscribers.append(user_id)

    def remove_subscriber(self, user_id):
        if user_id in self.subscribers:
            self.subscribers.pop(self.subscribers.index(user_id))

    def is_subscriber(self, user_id):
        return user_id in self.subscribers

    def update_next_time(self):
        self.nexttime = time.time() + self.interval
        self.is_reminded = False

    def set_reminded(self):
        self.is_reminded = True

    def get_reminded(self):
        return self.is_reminded

    def is_it_time_to_remind(self):
        return self.nexttime <= time.time()

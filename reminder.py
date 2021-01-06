import time


def stringtime_to_seconds(stringtime):
    unknownunittime = int(stringtime[:-1])
    unit = stringtime[-1].lower()

    if unit == 'm':
        unknownunittime *= 60
    elif unit == 'h':
        unknownunittime *= 3600
    elif unit == 's':
        unknownunittime *= 3600
    elif unit == 'd':
        unknownunittime *= 86400
    elif unit == 't':
        unknownunittime *= 86400
    else:
        unknownunittime = -1

    return unknownunittime


class Reminder:
    def __init__(self, name, interval, message, channelid):
        self.name = name
        self.message = message
        self.interval = stringtime_to_seconds(interval)
        self.channelid = channelid

        self.nexttime = time.time() + self.interval
        self.subscribers = {}
        self.is_reminded = False

    def add_subscriber(self, user_id, display_name, mention_tag):
        if user_id not in self.subscribers:
            self.subscribers[user_id] = [display_name, mention_tag]

    def remove_subscriber(self, user_id):
        if user_id in self.subscribers:
            self.subscribers.pop(user_id)

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

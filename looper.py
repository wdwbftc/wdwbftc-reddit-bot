import time

import praw

from worker import Worker


class Looper:

    def __init__(self, config: dict, reddit: praw.Reddit):
        self.config = config
        self.reddit = reddit

    def run(self):
        worker = Worker(self.config, self.reddit)
        loop_seconds = self.config['settings']['loop_minutes'] * 60
        if loop_seconds == 0:
            worker.process()
            return

        while True:
            last_time = time.time()
            worker.process()
            seconds_passed = time.time() - last_time
            if seconds_passed < loop_seconds:
                time.sleep(loop_seconds - seconds_passed)


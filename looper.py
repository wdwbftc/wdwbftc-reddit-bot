import logging
import time

import praw
import prawcore.exceptions

from worker import Worker


class Looper:

    def __init__(self, config: dict, reddit: praw.Reddit):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.reddit = reddit

    def run(self):
        worker = Worker(self.config, self.reddit)
        loop_seconds = self.config['settings']['loop_minutes'] * 60
        if loop_seconds == 0:
            self.try_process(worker)
            return

        while True:
            last_time = time.time()
            self.try_process(worker)
            seconds_passed = time.time() - last_time
            if seconds_passed < loop_seconds:
                time.sleep(loop_seconds - seconds_passed)

    def try_process(self, worker):
        try:
            worker.process()
        except prawcore.PrawcoreException as e:
            self.logger.error(f'PRAW exception occurred: {e}')

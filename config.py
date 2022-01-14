import json
import logging
import os
import shutil

from easygui import msgbox, passwordbox


class Config:

    def __init__(self, path='config.json', sample_path='config.sample.json'):
        self.logger = logging.getLogger(__name__)
        self.path = path
        self.sample_path = sample_path

    def get(self):
        self.init_file()

        with open(file=self.path, mode='r', encoding='utf-8') as file:
            config = json.load(file)

        if not config['authentication']['user_agent'].strip():
            self.logger.error(
                f'User agent is missing. Please provide it in the following format: '
                f'<platform>:<app ID>:<version string> (by /u/<reddit username>)')
            raise Exception()
        if not config['authentication']['client_id'].strip():
            config['authentication']['client_id'] = msgbox('Client ID').strip()
        if not config['authentication']['client_secret'].strip():
            config['authentication']['client_secret'] = msgbox('Client secret').strip()
        if not config['authentication']['username'].strip():
            config['authentication']['username'] = msgbox('Username').strip()
        if not config['authentication']['password'].strip():
            config['authentication']['password'] = passwordbox('Password')
        return config

    def init_file(self):
        if os.path.isfile(self.path):
            return

        if os.path.isfile(self.sample_path):
            shutil.copyfile(self.sample_path, self.path)
            self.logger.info(
                f'Created {self.path}. Please fill it according to README.md and start the application again.')
            exit(-1)
        else:
            self.logger.error(
                f'{self.sample_path} is missing. Please restore it or create {self.path} manually.')
            raise Exception()

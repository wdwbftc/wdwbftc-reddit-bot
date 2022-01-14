import praw as praw


class Api:

    def __init__(self, config: dict):
        self.config = config

    def get(self) -> praw.Reddit:
        authentication = self.config['authentication']
        return praw.Reddit(
            client_id=authentication['client_id'],
            client_secret=authentication['client_secret'],
            username=authentication['username'],
            password=authentication['password'],
            user_agent=authentication['user_agent']
        )

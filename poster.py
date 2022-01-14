import logging

from praw.models import Submission


class Poster:

    def __init__(self, config: dict):
        self.logger = logging.getLogger(__name__)
        self.config = config

    def post_comment(self, condition: dict, submission: Submission):
        if self.has_comment(condition, submission):
            self.logger.info(f'Post already has comment')
            return

        if self.config['settings']['test_run']:
            self.logger.info(f'Posting comment (skipping - test run)')
        else:
            self.logger.info(f'Posting comment')
            submission.reply(condition['message'])

    @staticmethod
    def has_comment(condition: dict, submission: Submission) -> bool:
        for comment in submission.comments:
            body = comment.body
            if body == condition['message']:
                return True
            for check_message in condition['check_messages']:
                if body.startswith(check_message):
                    return True
        return False

import logging
from datetime import datetime, timedelta, timezone

import praw
import prawcore
from praw.models import Redditor

from poster import Poster


class Worker:

    def __init__(self, config: dict, reddit: praw.Reddit):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.reddit = reddit
        self.poster = Poster(config)

    def process(self):
        self.logger.debug(f'Processing started')
        for condition in self.config['conditions']:
            self.logger.debug(f'Processing condition')
            if not condition['check_subreddits']:
                self.logger.debug(f'No subreddits to check')
                continue
            if 'subreddits_recent' not in condition:
                condition['subreddits_recent'] = {}
            for subreddit in condition['subreddits']:
                self.logger.debug(f'Checking subreddit: {subreddit}')
                self.process_subreddit(condition, subreddit)
        self.logger.debug(f'Processing ended')

    def process_subreddit(self, condition: dict, subreddit: str):
        subreddits_recent = condition['subreddits_recent']
        if subreddit not in subreddits_recent:
            subreddits_recent[subreddit] = None

        submission_recent = None
        for submission in self.reddit.subreddit(subreddit).new(limit=None):
            if not submission_recent:
                submission_recent = submission.created_utc
            if subreddits_recent[subreddit] and submission.created_utc <= subreddits_recent[subreddit]:
                self.logger.debug(f'Reached already checked posts in subreddit')
                break
            if submission.created_utc < self.get_utc(timedelta(minutes=condition['new_posts_minutes'])):
                self.logger.debug(f'Reached date limit in subreddit')
                break

            self.logger.info(f'Checking post: {submission.permalink}')

            author = submission.author
            if not author:
                continue

            if self.has_posts(condition, author):
                self.logger.warning(f'Found post for user {author.name}: {submission.permalink}')
                self.poster.post_comment(condition, submission)
        subreddits_recent[subreddit] = submission_recent

    def has_posts(self, condition: dict, author: Redditor) -> bool:
        subreddits = list(map(lambda x: x.lower(), condition['check_subreddits']))
        self.logger.debug(f'Checking posts for user: {author.name}')
        try:
            return self.has_submissions(condition, author, subreddits) or \
                   self.has_comments(condition, author, subreddits)
        except prawcore.NotFound as e:
            self.logger.error(f'PRAW Not Found exception occurred while checking user {author.name}: {e}')
            return False

    def has_submissions(self, condition: dict, author: Redditor, subreddits: list) -> bool:
        self.logger.debug(f'Checking submissions for user: {author.name}')
        for submission in author.submissions.new(limit=None):
            if submission.created_utc < self.get_utc(timedelta(days=condition['expiration_days'])):
                self.logger.debug('Reached date limit in author submissions')
                return False
            if submission.subreddit.display_name.lower() in subreddits:
                self.logger.debug(f'Found submission: {submission.permalink}')
                return True
        return False

    def has_comments(self, condition: dict, author: Redditor, subreddits: list) -> bool:
        self.logger.debug(f'Checking comments for user: {author.name}')
        for comment in author.comments.new(limit=None):
            if comment.created_utc < self.get_utc(timedelta(days=condition['expiration_days'])):
                self.logger.debug('Reached date limit in author comments')
                return False
            if comment.subreddit.display_name.lower() in subreddits:
                self.logger.debug(f'Found comment: {comment.permalink}')
                return True
        return False

    @staticmethod
    def get_utc(delta: timedelta):
        return (datetime.now(timezone.utc) - delta).timestamp()

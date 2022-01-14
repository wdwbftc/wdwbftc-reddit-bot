import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import praw
from praw.models import Submission, Redditor

from poster import Poster


class Worker:

    @dataclass
    class Temporary:
        subreddits_recent = {}
        users = {}

    @dataclass
    class User:
        comment_recent = None
        submission_recent = None
        checked_recent = None

    def __init__(self, config: dict, reddit: praw.Reddit):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.reddit = reddit
        self.poster = Poster(config)

    def process(self):
        self.logger.info(f'Beginning processing')
        for condition in self.config['conditions']:
            self.logger.info(f'Processing condition')
            if not condition['check_subreddits']:
                self.logger.info(f'No subreddits to check')
                continue
            if 'temp' not in condition:
                condition['temp'] = self.Temporary()
            for subreddit in condition['subreddits']:
                self.logger.info(f'Checking subreddit: {subreddit}')
                self.process_subreddit(condition, subreddit)
        self.logger.info(f'Processing ended')

    def process_subreddit(self, condition: dict, subreddit: str):
        subreddits_recent = condition['temp'].subreddits_recent
        if subreddit not in subreddits_recent:
            subreddits_recent[subreddit] = None

        users = condition['temp'].users
        submission_recent = None
        for submission in self.reddit.subreddit(subreddit).new(limit=None):
            if not submission_recent:
                submission_recent = submission.created_utc
            if subreddits_recent[subreddit] and submission.created_utc <= subreddits_recent[subreddit]:
                self.logger.info(f'Reached already checked posts in subreddit')
                break
            if submission.created_utc < self.get_utc(timedelta(minutes=condition['new_posts_minutes'])):
                self.logger.info(f'Reached date limit in subreddit')
                break

            self.logger.info(f'Checking post: {submission.permalink}')

            author = submission.author
            if not author:
                continue
            if author.name not in users:
                users[author.name] = self.User()
            user = users[author.name]

            if not self.has_posts(condition, user):
                self.check_posts(condition, author, user)
            if self.has_posts(condition, user):
                self.logger.warning(f'User {author.name} found on {submission.permalink}')
                self.poster.post_comment(condition, submission)
        subreddits_recent[subreddit] = submission_recent

    def has_posts(self, condition: dict, user: User) -> bool:
        return user.checked_recent and user.checked_recent > self.get_utc(timedelta(days=condition['expiration_days']))

    def check_posts(self, condition: dict, author: Redditor, user: User):
        subreddits = list(map(lambda x: x.lower(), condition['check_subreddits']))
        self.check_comments(condition, author, user, subreddits)
        self.check_submissions(condition, author, user, subreddits)

    def check_comments(self, condition: dict, author: Redditor, user: User, subreddits: list):
        comment_recent = None
        for comment in author.comments.new(limit=None):
            if not comment_recent:
                comment_recent = comment.created_utc
            if user.comment_recent and comment.created_utc <= user.comment_recent:
                self.logger.debug('Reached already checked posts in author comments')
                break
            if comment.created_utc < self.get_utc(timedelta(days=condition['expiration_days'])):
                self.logger.debug('Reached date limit in author comments')
                break
            self.logger.debug(f'Checking comment for user {author.name}: {comment.permalink}')
            if comment.subreddit.display_name.lower() in subreddits:
                self.logger.debug('Found post in author comments')
                user.checked_recent = comment.created_utc
                break
        user.comment_recent = comment_recent

    def check_submissions(self, condition: dict, author: Redditor, user: User, subreddits: list):
        submission_recent = None
        for submission in author.submissions.new(limit=None):
            if not submission_recent:
                submission_recent = submission.created_utc
            if user.submission_recent and submission.created_utc <= user.submission_recent:
                self.logger.debug('Reached already checked posts in author submissions')
                break
            if submission.created_utc < self.get_utc(timedelta(days=condition['expiration_days'])):
                self.logger.debug('Reached date limit in author submissions')
                break
            self.logger.debug(f'Checking submission for user {author.name}: {submission.permalink}')
            if submission.subreddit.display_name.lower() in subreddits and submission.created_utc > user.checked_recent:
                self.logger.debug('Found post in author submissions')
                user.checked_recent = submission.created_utc
                break
        user.submission_recent = submission_recent

    @staticmethod
    def get_utc(delta: timedelta):
        return (datetime.now(timezone.utc) - delta).timestamp()

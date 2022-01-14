import logging.config
import os

from api import Api
from config import Config
from looper import Looper


def main():
    os.makedirs('logs', exist_ok=True)
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger(__name__)

    logger.info('Starting application')

    config = Config().get()
    reddit = Api(config).get()
    assert reddit.user.me() == config['authentication']['username']

    Looper(config, reddit).run()

    logger.info('Stopping application')


if __name__ == '__main__':
    main()

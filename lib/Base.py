import logging

class Base(object):

    def __init__(self):

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)

        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(ch)

        self.logger = logger
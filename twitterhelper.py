# -*- coding: utf-8 -*-

import yaml
from python_twitter import twitter

def _get_api_key():
    return yaml.safe_load(open('api.yaml').read().decode('utf-8'))

def _get_twitter():
    keys = _get_api_key()
    return twitter.Api(
        keys['consumer_key'],
        keys['consumer_secret'],
        keys['access_token_key'],
        keys['access_token_secret'],
        cache=None
        )


class TwitterHelper(object):
    def __init__(self):
        self._twitter = _get_twitter()

    def tweet(self, status):
        self._twitter.PostUpdate(status)
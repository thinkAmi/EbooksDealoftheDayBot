# -*- coding: utf-8 -*-

from google.appengine.ext import ndb

class TweetHistory(ndb.Model):
    last_message = ndb.StringProperty()


class ErrorMailHistory(ndb.Model):
    last_send_date = ndb.DateProperty()

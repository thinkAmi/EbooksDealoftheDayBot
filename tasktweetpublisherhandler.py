# -*- coding: utf-8 -*-

import webapp2
import os
import logging
from lxml import html
from google.appengine.api import urlfetch

from tasktweetbasehandler import TaskTweetBaseHandler


# Deal of the Dayを取得する具象クラス
# 作成例
class ExampleHandler(TaskTweetBaseHandler):
    def __init__(self, request, response):
        # __init__をオーバーライドするなら、必ず呼ぶメソッド(self.initialize(request, response))
        # http://webapp-improved.appspot.com/guide/handlers.html#overriding-init
        self.initialize(request, response)

        # 必須設定
        self._tweetId = ''
        self._dealUrl = ''
        self._errorWeb = ''
        self._errorContents = ''

        # 片方のみアンコメント： _feedUrlはフィードから、_scrapeUrlはWebから、データを取得するときに指定するURL
        #self._feedUrl = ''
        #self._scrapeUrl = ''


    # 以下は必要に応じてオーバーライドするメソッド
    # FeedやWebから取得したタイトルを編集するときに、オーバーライドして使用するメソッド
    #def edit_title(self, title):

    # Webをスクレイピングする時に使用するメソッド
    #def _get_DOTD_from_web(self):



# 実際に使用するクラス群
# Apress
class TaskTweetApressHandler(TaskTweetBaseHandler):
    def __init__(self, request, response):
        self.initialize(request, response)

        self._tweetId = 'Apress'
        self._feedUrl = 'http://www.apress.com/index.php/dailydeals/index/rss'
        self._dealUrl = 'http://www.apress.com/'
        self._errorWeb = 'Error:ApressWeb'
        self._errorContents = 'Error:ApressFeed'


# PEARSON (SAMS等)
class TaskTweetPearsonHandler(TaskTweetBaseHandler):
    def __init__(self, request, response):
        self.initialize(request, response)

        self._tweetId = 'PEARSON'
        self._feedUrl = 'http://www.informit.com/deals/deal_rss.aspx'
        self._dealUrl = 'http://www.informit.com/deals/'
        self._errorWeb = 'Error:PEARSONWeb'
        self._errorContents = 'Error:PEARSONFeed'


    def edit_title(self, title):
        # PEARSONの場合、タイトルが長すぎてツイートできないことがある
        # [ :: ]の後ろにタイトルが入ってくるので、そこで区切る
        splited = title.split(' :: ')
        return splited[1]


# O'Reilly
class TaskTweetOreillyHandler(TaskTweetBaseHandler):
    def __init__(self, request, response):
        self.initialize(request, response)

        self._tweetId = 'OReilly'
        self._feedUrl = 'http://feeds.feedburner.com/oreilly/ebookdealoftheday'
        self._dealUrl = 'http://oreilly.com/'
        self._errorWeb = 'Error:OReillyWeb'
        self._errorContents = 'Error:OReillyFeed'


    def edit_title(self, title):
        # [:]がない場合(セット販売とか) -> そのまま表示
        # [:]がある場合(単品) -> [:]で区切り、２つ目以降の要素がタイトルとなる
        if ':' in title:
            splited = title.split(':')

            results = []
            for i, title in enumerate(splited):
                if i > 0:
                    results.append(title)

            return ':'.join(results)
        else:
            return title


# Microsoft Press(O'Reilly)
class TaskTweetMicrosoftPressHandler(TaskTweetBaseHandler):
    def __init__(self, request, response):
        self.initialize(request, response)

        self._tweetId = 'MicrosoftPress'
        self._feedUrl = 'http://feeds.feedburner.com/oreilly/mspebookdeal'
        self._dealUrl = 'http://oreilly.com/'
        self._errorWeb = 'Error:OReillyMSPressWeb'
        self._errorContents = 'Error:OReillyMSPressFeed'


    def edit_title(self, title):
        splited = title.split(':')

        results = []
        for i, title in enumerate(splited):
            if i > 0:
                results.append(title)

        return ':'.join(results)


# Manning
class TaskTweetManningHandler(TaskTweetBaseHandler):
    def __init__(self, request, response):
        self.initialize(request, response)

        self._tweetId = 'Manning'
        self._scrapeUrl = 'http://incsrc.manningpublications.com/dotd.js'
        self._dealUrl = 'http://www.manning.com/'
        self._errorWeb = 'Error:ManningWeb'
        self._errorContents = 'Error:ManningWeb'


    def scrape(self):
        response = urlfetch.fetch(self._scrapeUrl)
        root = html.fromstring(response.content)

        # 著者名は取れないので、書名のみを戻す
        return root.xpath('//a')[0].text



debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')


# Handler用のURLリスト
# 対象のDeal of the Dayが増えたら、ここにも追加すること (Cronの方でもこのdictを利用している)
handlerUrls = dict(
    Apress='/task/tweet/apress',
    Pearson = '/task/tweet/pearson',
    Oreilly = '/task/tweet/oreilly',
    OreillyMS = '/task/tweet/oreillymspress',
    Manning = '/task/tweet/manning',
    )



app = webapp2.WSGIApplication([
                               (handlerUrls['Apress'], TaskTweetApressHandler),
                               (handlerUrls['Pearson'], TaskTweetPearsonHandler),
                               (handlerUrls['Oreilly'], TaskTweetOreillyHandler),
                               (handlerUrls['OreillyMS'], TaskTweetMicrosoftPressHandler),
                               (handlerUrls['Manning'], TaskTweetManningHandler),
                               ], debug=debug)



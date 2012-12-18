# -*- coding: utf-8 -*-

import webapp2
import os
import logging
import datetime
import json

from google.appengine.api import urlfetch
from google.appengine.api import mail
from google.appengine.api.labs import taskqueue

from lxml import html
import yaml

from python_twitter.twitter import TwitterError
from twitterhelper import TwitterHelper
from models import TweetHistory, ErrorMailHistory


# ツイートする抽象クラス：実際は、このクラスを継承して利用する
class TaskTweetHandler(webapp2.RequestHandler):
    def post(self):

        # 例外が出た場合、エラーログを残し、タスクを終了する。
        try:
            self._tweet()

        except TwitterError, e:
            if e.message == u'Status is a duplicate.':
                # 重複Tweetはよくあることなので、infoレベルにする
                logging.info(u'Duplicate posted')
            else:
                logging.error(e)

        except Exception, e:
            logging.error(e)



    def _tweet(self):
        # 今のところはDeal of the DayはFeedで配信されているため、Feedのみの検索で十分そう
        message = self._get_DOTD_from_feed()

        if message is None:
            # エラーを出力
            logging.error(u'Cannot Get DOTD')
            self._send_error_mail(self._errorFeed)
            return


        # すでにツイート済の場合、ログに残して、ツイートせずに終了
        if self._has_tweeted(message):
            logging.info(u'Already posted')
            return


        # tweetする
        twitter = TwitterHelper()
        twitter.tweet(message)


        # 重複ツイートを避けるため、datastoreにツイート内容を保存
        self._save_tweet_message(message)



    def _get_DOTD_from_web(self):
        # 【今のところ使っていない】
        # サイトをスクレイピングして、Deal of the Day のデータを取得する
        # 取得できない場合、Noneを返す
        response = urlfetch.fetch(self._dealUrl)

        # Deal of Today を取得する
        root = html.fromstring(response.content)
        # 全DOM中から、<p>タグがクラス名が「centred」のものをさがす
        entries = root.xpath('//p[@class="centred"]/a/text()')

        # 現時点では、該当するものは3個
        if len(entries) != 3:
            # スクレイピングエラーの場合、スクレイピング方法を変更する必要があるため、管理者アカウントへメールを飛ばす
            self._send_error_mail(self._errorWeb)
            return None

        # [0]に書名あり
        result = self._create_message(entries[0])
        return result



    def _get_DOTD_from_feed(self):
        # 子クラスで指定したFeedのURLを元に、、Deal of the Day のデータを取得する
        # 取得できない場合、Noneを返す

        # 必須パラメータなので、呼び出し元のサーバーIPアドレスを取得する
        ip = os.environ['REMOTE_ADDR']

        # Google Feed API での1件フェッチ
        url = (
            u'https://ajax.googleapis.com/ajax/services/feed/load?v=1.0&q='
            + self._feedUrl
            + u'&num=1'
            + u'&userip=' + ip
            )
        feed = urlfetch.fetch(url)

        j = json.loads(feed.content)
        entries = j['responseData']['feed']['entries']
        for entry in entries:
            # entriesは1件だけのため、forの中で処理をしてしまう
            result = self._create_message(entry['title'])
            return result

        # ここまで来た場合、該当するデータがないということで、Noneを返す
        return None



    def _create_message(self, title):
        # 複数回使う可能性があるものは、最初に編集しておく
        # また、先頭に空白・タブ・改行が入ってくる可能性があるため、それらも削除する
        publisher = u'[' + self._tweetId + u']　'
        ebookTitle = self.edit_title(title).lstrip()

        msg = publisher + ebookTitle + u'　' + self._dealUrl
        if len(msg) <= 140:
            return msg

        msg = publisher + ebookTitle
        if len(msg) <= 140:
            return msg

        msg = ebookTitle
        if len(msg) <= 140:
            return msg

        return ebookTitle[0:140]



    def _has_tweeted(self, message):
        # データストアを検索し、値が一致すれば、すでにツイート済
        history = TweetHistory.get_by_id(self._tweetId)

        if history is None:
            # エンティティがない場合は、まだツイートしていない
            return False
        elif message == history.last_message:
            return True
        else:
            return False



    def _save_tweet_message(self, message):
        # ツイートした内容をデータストアに保存する
        history = TweetHistory(id=self._tweetId, last_message=message)
        history.put()



    def _send_error_mail(self, errorType):
        # エラーの場合、管理者メール送信タスクを作成する
        # 送信履歴がないこと・本日はまだ送信していないことが条件
        # ndbの場合キャッシュをするので、キャッシュはオフにしておく
        history = ErrorMailHistory.get_by_id(
                        errorType,
                        use_cache=False,
                        use_memcache=False
                        )

        if history is None:
            self._add_send_error_mail_task(history, errorType)
            return

        now = datetime.datetime.utcnow()
        if history.last_send_date < now.date():
            self._add_send_error_mail_task(history, errorType)
            return



    def _add_send_error_mail_task(self, history, errorType):
        # メールの送信、送信履歴の更新
        taskqueue.add(
            url='/task/errormail',
            params={'subject': errorType}
            )

        if history is None:
            history = ErrorMailHistory(id=errorType)

        now = datetime.datetime.utcnow()
        history.last_send_date = now.date()
        history.put()


    '''
    以下、具象クラスでオーバーライドが任意のメソッド
    '''
    def edit_title(self, title):
        # feedのタイトルが長いなどの場合、編集して返すためのメソッド
        return title



# Deal of the Dayを取得する具象クラス
# Apress
class TaskTweetApressHandler(TaskTweetHandler):
    def __init__(self, request, response):
        # __init__をオーバーライドするなら、必ず呼ぶメソッド(self.initialize(request, response))
        # http://webapp-improved.appspot.com/guide/handlers.html#overriding-init
        self.initialize(request, response)

        self._tweetId = 'Apress'
        self._feedUrl = 'http://www.apress.com/index.php/dailydeals/index/rss'
        self._dealUrl = 'http://www.apress.com/'
        self._errorWeb = 'Error:ApressWeb'
        self._errorFeed = 'Error:ApressFeed'




# PEARSON (SAMS等)
class TaskTweetPearsonHandler(TaskTweetHandler):
    def __init__(self, request, response):
        self.initialize(request, response)

        self._tweetId = 'PEARSON'
        self._feedUrl = 'http://www.informit.com/deals/deal_rss.aspx'
        self._dealUrl = 'http://www.informit.com/deals/'
        self._errorWeb = 'Error:PEARSONWeb'
        self._errorFeed = 'Error:PEARSONFeed'


    def edit_title(self, title):
        # PEARSONの場合、タイトルが長すぎてツイートできないことがある
        # [ :: ]の後ろにタイトルが入ってくるので、そこで区切る
        splited = title.split(' :: ')
        return splited[1]


# O'Reilly
class TaskTweetOreillyHandler(TaskTweetHandler):
    def __init__(self, request, response):
        self.initialize(request, response)

        self._tweetId = 'OReilly'
        self._feedUrl = 'http://feeds.feedburner.com/oreilly/ebookdealoftheday'
        self._dealUrl = 'http://oreilly.com/'
        self._errorWeb = 'Error:OReillyWeb'
        self._errorFeed = 'Error:OReillyFeed'


    def edit_title(self, title):
        # O'Reillyの場合、タイトルが長い上、セットになることもある
        # [:]で区切り、２つ目以降の要素がタイトルとなる
        splited = title.split(':')

        # また、シリーズ品の場合、[:]なしの場合がある
        # その時は、タイトルそのままを返す
        if len(splited) == 1:
            return title

        results = []
        for i, title in enumerate(splited):
            if i > 0:
                results.append(title)

        return ':'.join(results)


# Microsoft Press(O'Reilly)
class TaskTweetMicrosoftPressHandler(TaskTweetHandler):
    def __init__(self, request, response):
        self.initialize(request, response)

        self._tweetId = 'MicrosoftPress'
        self._feedUrl = 'http://feeds.feedburner.com/oreilly/mspebookdeal'
        self._dealUrl = 'http://oreilly.com/'
        self._errorWeb = 'Error:OReillyMSPressWeb'
        self._errorFeed = 'Error:OReillyMSPressFeed'


    def edit_title(self, title):
        splited = title.split(':')

        if len(splited) == 1:
            return title

        results = []
        for i, title in enumerate(splited):
            if i > 0:
                results.append(title)

        return ':'.join(results)



debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

app = webapp2.WSGIApplication([
                               ('/task/tweet/apress', TaskTweetApressHandler),
                               ('/task/tweet/pearson', TaskTweetPearsonHandler),
                               ('/task/tweet/oreilly', TaskTweetOreillyHandler),
                               ('/task/tweet/oreillymspress', TaskTweetMicrosoftPressHandler),
                               ], debug=debug)
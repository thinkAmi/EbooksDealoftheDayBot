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


APRESS_URL = u'http://www.apress.com/'
ERROR_TYPE_FAIL_WEB = u'web'
ERROR_TYPE_FAIL_FEED = u'feed'

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

        # Deal of Today を取得する
        message = self._get_DOTD_from_web()

        if message is None:
            # RSSよりデータを取得
            message = self._get_DOTD_from_feed()

        if message is None:
            # エラーを出力
            logging.error(u'Cannot Get DOTD')
            self._send_error_mail(ERROR_TYPE_FAIL_FEED)
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
        # Apressのサイトをスクレイピングして、Deal of the Day のデータを取得する
        # 取得できない場合、Noneを返す
        response = urlfetch.fetch(APRESS_URL)

        # Deal of Today を取得する
        root = html.fromstring(response.content)
        # 全DOM中から、<p>タグがクラス名が「centred」のものをさがす
        entries = root.xpath('//p[@class="centred"]/a/text()')
        
        # 現時点では、該当するものは3個
        if len(entries) != 3:
            # スクレイピングエラーの場合、スクレイピング方法を変更する必要があるため、管理者アカウントへメールを飛ばす
            self._send_error_mail(ERROR_TYPE_FAIL_WEB)
            return None

        # [0]に書名あり
        result = self._create_message(entries[0])
        return result



    def _get_DOTD_from_feed(self):
        # Apressのフィードを取得して、Deal of the Day のデータを取得する
        # 取得できない場合、Noneを返す

        # 必須パラメータなので、呼び出し元のサーバーIPアドレスを取得する
        ip = os.environ['REMOTE_ADDR']

        # Google Feed API での1件フェッチ
        url = (
            u'https://ajax.googleapis.com/ajax/services/feed/load?v=1.0&q='
            + u'http://www.apress.com/index.php/dailydeals/index/rss'
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
        return title + u' ' + APRESS_URL



    def _has_tweeted(self, message):
        # データストアを検索し、値が一致すれば、すでにツイート済
        history = TweetHistory.get_by_id(u'tweet')

        if history is None:
            # エンティティがない場合は、まだツイートしていない
            return False
        elif message == history.last_message:
            return True
        else:
            return False



    def _save_tweet_message(self, message):
        # ツイートした内容をデータストアに保存する
        history = TweetHistory(id=u'tweet', last_message=message)
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

        subject = None
        if errorType == ERROR_TYPE_FAIL_WEB:
            subject = 'Error:web'
        elif errorType == ERROR_TYPE_FAIL_FEED:
            subject = 'Error:feed'

        taskqueue.add(
            url='/task/errormail', 
            params={'subject': subject}
            )

        if history is None:
            history = ErrorMailHistory(id=errorType)

        now = datetime.datetime.utcnow()
        history.last_send_date = now.date()
        history.put()




debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')
            
app = webapp2.WSGIApplication([
                               ('/task/tweet', TaskTweetHandler),
                               ], debug=debug)
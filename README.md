EbooksDealoftheDayBot
========

複数の出版社のDeal of the DayをツイートするBotをGAEで動かすためのプログラムです。



開発環境
----------

* OS: Windows7 x64
* SDK: Google App Engine SDK for Python  1.7.4 - 2012-12-13
* Python: Python2.7


セットアップ
----------

1. app.yamlに自分のApplicationIDを入力します。
2. api.yamlに自分のTwitterBotの各種APIキーを入力します。
3. あとはGoogle App Engineへとデプロイすれば、Botが動作します。


動作
----------

* Deal of the Dayのあるサイトのフィードを、一時間に一度、Google Feed APIにてフィードのチェックを行います (現時点では、Apress・PEARSON・O'Reilly・O'Reilly Microsoft Press・Manning)。
* 変更があれば、TwitterBotがツイートします。
* /feedにアクセスすることで、フィードを出力します。


ライセンス
----------
MITライセンス

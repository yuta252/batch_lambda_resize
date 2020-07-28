===============================================
Lambda関数によるS3アップロード画像のExif削除とリサイズ
===============================================

目的
=====
アップロードされた画像をDeepLearningで学習するためには画像のサイズとExif情報を削除する必要がある。
特にモバイル端末で撮影した画像をStartlens（Web画面）から直接アップロードしてしまうとExif情報が付与されたままアップロードされてしまう。
このExif情報を付与したまま学習してしまうと画像の回転が考慮されず学習の精度が下がってしまうためバッチ処理が必要である。

ツールのバージョン
==============
:Python:    3.6.10
:pip:       20.1.1


インストールと起動方法
==================
リポジトリーからコードを取得し、venv環境に依存ライブラリをインストールする

    #. $ git clone https://github.com/
    #. $ cd startlens
    #. $ python3.6 -m venv venv
    #. $ source venv/bin/activate
    #. (venv) $ pip install -r requirements/test.txt
    #. (venv) $ python3.6 manage.py runserver --settings=config.settings.test


AWSでの環境設定と起動方法
======================
:Ubuntu:    18.04
:インスタンスタイプ:    t2.micro

EC2インスタンス内での実行手順

    #. sudo apt -y update
    #. sudo apt -y upgrade
    #. sudo apt -y install build-essential python3-dev libsqlite3-dev libreadline6-dev libgdbm-dev zlib1g-dev libbz2-dev sqlite3 tk-dev zip libssl-dev
    #. wget https://www.python.org/ftp/python/3.6.10/Python-3.6.10.tgz
    #. tar xf Python-3.6.10.tgz
    #. cd Python-3.6.10
    #. ./configure —prefix=/opt/python3.6.10
    #. make
    #. sudo make install
    #. sudo ln -s /opt/python3.6.10/bin/python3.6 /usr/local/bin/python3.6
    #. sudo ln -s /opt/python3.6.10/bin/pip3.6 /usr/local/bin/pip


RDSの構築
========
:DB:    8.0.19

RDSを作成しEC2インスタンスでの実行手順

    * sudo apt -y install mysql-client default-libmysqlclient-dev

データベースの接続確認

    * mysql -h { database endpoint } -u rootname --password="password"

データベーステーブルの作成

    * sql> CREATE DATABASE startlens


ソースコードのデプロイ
===================
EC2のvenv仮想環境で下記を実行

    * pip install -r requirements/test.txt
    * pip install wheel mysqlclient django-environ django-storages boto3
    * mkdir /var/log/startlens_django
    * BASE_DIRディレクトリに .envファイルを作成し config.setting.test で読み込む環境変数を定義する
    * S3の作成とS3fullaccessユーザーをIAMで作成して .envにEC2からS3へアクセスするためのアクセスキーとシークレットキーを設定する


Djangoの設定
===========
管理者アカウトを作成する

    * python manage.py create superuser

静的ファイルの配置

    * sudo mkdir /var/www
    * sudo mkdir /var/www/startlens_django
    * sudo chown ubuntu:www-data /var/www/startlens_django
    * python manage.py collectstatic --noinput


アプリケーションサーバーとリバースプロキシの設定
=========================================
:nginx:    1.14.0
:gunicorn:    20.0.4

アプリケーションサーバーとしてgunicornをセットアップする

    * pip install gunicorn
    * gunicorn --daemon --bind=0.0.0.0:8000 config.wsgi

デーモンで起動しているgunicornを停止する場合

    * sudo lsof -i:8000
    * sudo kill -9 PID

リバースプロキシとしてnginxのインストールと設定

    * sudo apt install -y nginx
    * sudo systemctl enable nginx
    * mv config/startlens /etc/nginx/site-available/startlens
    * sudo ln -s /etc/nginx/sites-available/startlens /etc/nginx/sites-enabled/
    * sudo unlink /etc/nginx/site-enabled/default
    * sudo nginx -t
    * sudo systemctl relaod nginx


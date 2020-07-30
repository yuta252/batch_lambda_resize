===============================================
Lambda関数によるS3アップロード画像のExif削除とリサイズ
===============================================

目的
=====
アップロードされた画像をDeepLearningで学習するためには画像のサイズとExif情報を削除する必要がある。
特にモバイル端末で撮影した画像をStartlens（Web画面）から直接アップロードしてしまうとExif情報が付与されたままアップロードされてしまう。
このExif情報を付与したまま学習してしまうと画像の回転が考慮されず学習の精度が下がってしまうためバッチ処理が必要である。

機能
====
S3の特定のバケットにアップロードされたjpg画像をprefixをもとにLambdaで自動検知し、画像のExif情報の削除と正しい方向への回転及び画像を(600px, 600px)でリサイズする

Lambdaの実行環境
==============
:ランタイム:    python3.6
:メモリ:       512MB


Lambdaパッケージの作成
===================
:EC2 OS:      Ubuntu18.04


Lambda関数を作成するためには①AWS Lambdaコンソールから設計図を利用して直接作成する方法②Lambda関数をパッケージ化したzipファイルをアップロードする方法、の2種類がある。
今回は外部ライブラリPillowを利用するため②の方法で進める。ただし、ローカルで作業する場合にPillowをインストールするとLambda（Amazon Linux）で動作しないため、Dockerを利用するかEC2上でパッケージ化の作業を行う。
以下はEC2でパッケージ化する場合の手順


    #. sudo apt -y update
    #. sudo apt -y install build-essential python3-dev libsqlite3-dev libreadline6-dev libgdbm-dev zlib1g-dev libbz2-dev sqlite3 tk-dev zip libssl-dev
    #. wget https://www.python.org/ftp/python/3.6.10/Python-3.6.10.tgz
    #. tar xf Python-3.6.10.tgz
    #. cd Python-3.6.10
    #. ./configure —prefix=/opt/python3.6.10
    #. make
    #. sudo make install
    #. sudo ln -s /opt/python3.6.10/bin/python3.6 /usr/local/bin/python3.6
    #. sudo ln -s /opt/python3.6.10/bin/pip3.6 /usr/local/bin/pip
    #. python3.6 -m venv venv
    #. source venv/bin/activate
    #. mkdir ~/work & cd work
    #. git clone https://github.com/yuta252/batch_lambda_resize.git
    #. pip install -r requirements.txt
    #. cd $VIRTUAL_ENV/lib/python3.6/site-packages
    #. zip -r9 $(OLDPWD)/lambda_function.zip .
    #. cd ${OLDPWD}
    #. zip -g lambda_function.zip lambda_function.py
    #. scp -i secretkey.pem -r ubuntu@[IP Address]:/home/ubuntu/work/batch_lambda_resize/lambda_function.zip [local directory path]



Lambda関数の作成
===============
AWSコンソール上でLambda関数を作成する手順を下記に記載する。

    #. LambdaからS3にアクセスするための実行権限をIAMロールを付与する。IAMからロールを作成し「AWSLambdaBasicExcutionRole」「AmazonS3FullAccess」のポリシーをアタッチする。S3へのポリシーはセキュリティー上の問題があるため本番環境では適切なポリシーに変更する。
    #. Lambdaコンソールから「関数の作成」→「一から作成」を押下し、「Python3.6」ランタイムと上記で作成したIAMロールを指定し、「関数の作成」を押下
    #. トリガーの追加からS3にファイルアップロード時にLambda関数を実行するための設定を行う。S3バケット（ダウンロード先）、イベントタイプを「すべてのオブジェクト作成イベント」、プレフィックスを「postpic/」、サフィックスを「.jpg」に設定する。この時にダウンロード先のS3バケットとアップロード先のS3バケットがLambda_function.pyのコード上同じ場合、無限ループでLambda関数が実行される可能性があるので注意する。
    #. EC2で作成したパッケージlambda_function.zipをアップロードする
    #. テストイベントの設定から新しいテストイベントを作成し、Amazon S3 PutのRecords.s3.bucket.name, Records.s3.arn, Records.s3.object.keyにバケット名とkeyを設定する
    #. 設定したバケットとKeyにファイルをアップロードし、Lambdaコンソールからテストを押下
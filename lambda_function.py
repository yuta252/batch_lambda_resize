import boto3
import os
import json
import sys
import uuid
from urllib.parse import unquote_plus
from traceback import print_exc
from PIL import Image
import PIL.Image
from PIL.ExifTags import TAGS


# s3クライアントの取得
s3_client = boto3.client('s3')


def resize_image(image):
    """
        Pillowによる画像のリサイズ処理
    """
    width, height = image.size
    square_size = min(width, height)

    if width > height:
        # 横方向に切り取る
        top = 0
        bottom = square_size
        left = (width - square_size) / 2
        right = left + square_size
        box = (left, top, right, bottom)
    else:
        # 縦方向に切り取る
        left = 0
        right = square_size
        top = (height - square_size) / 2
        bottom = top + square_size
        box = (left, top, right, bottom)

    image = image.crop(box)
    # 600pxの正方形に調整
    thumbnail_size = (600, 600)
    image.thumbnail(thumbnail_size)
    return image


def _exif(file_path):
    try:
        # JSON生成
        def _format_bytes(obj_):
            res = {}
            for key_, value_ in obj_.items():
                if isinstance(value_, bytes):
                    res[key_] = "{}".format(value_)
                elif isinstance(value_, dict):
                    res[key_] = _format_bytes(value_)
                else:
                    res[key_] = value_
            return res

        # Exifの読み取り
        with Image.open(file_path) as f:
            exif_ = f._getexif()
        info_ = {}
        for key_ in exif_.keys():
            tag_ = TAGS.get(key_, key_)
            if tag_ in ["MakerNote", "UserComment"]:
                continue
            info_[tag_] = exif_[key_]

        return _format_bytes(info_)

    except AttributeError:
        # exif_が存在しない場合の例外処理
        return {}
    except BaseException:
        raise


def list_exif(file_path):
    # jpeg以外のファイルの確認と処理
    path_ = os.path.normpath(file_path)
    buf_ = {"path": path_,
            "file": os.path.basename(path_)}
    # Exifデータの追加
    buf_["exif"] = _exif(path_)
    return buf_


def remove_exif(file_path, resized_path):
    """
        PillowによるExif削除及び回転処理
    """
    # ファイルパス、ファイル名、Exif情報の取得
    item = list_exif(file_path)
    # Exif情報が存在するとき
    if item["exif"] != {}:
        orientation_ = item["exif"]["Orientation"]
        # Exifにより画像が回転しているとき
        if orientation_ > 1:
            print("save file: {} (orientation:{})...".format(item["path"], orientation_))
            trans_ = [0, 3, 1, 5, 4, 6, 2][orientation_ - 2]
            with Image.open(item["path"]) as image_:
                # 正しい方向へ画像を回転処理
                image_ = image_.transpose(trans_)
                # 600px - 600pxにリサイズ
                image_ = resize_image(image_)
                # アップロード用に一時保存
                image_.save(resized_path)


def lambda_handler(event, context):
    """
        Lambdaから最初に呼ばれるハンドラ関数
    """
    for record in event['Records']:
        print("record: {}".format(record))
        bucket = record['s3']['bucket']['name']
        upload_bucket = "startlens-media-resized"
        # 引数からS3のKey(フォルダ名/ファイル名)を抽出
        key = unquote_plus(record['s3']['object']['key'])
        # thumbnails/ファイル名のパスを作成
        tmpkey = key.replace('/', '')
        # S3からダウンロードしたファイルの保存先を設定
        download_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
        # 加工したファイルの一時保存先を設定
        upload_path = '/tmp/resized-{}'.format(tmpkey)
        # S3からファイルをダウンロード
        s3_client.download_file(bucket, key, download_path)
        # Exif削除と回転処理
        remove_exif(download_path, upload_path)
        # 処理後のファイルをS3にアップロード（ダウンロード元とバケットを変更する）
        s3_client.upload_file(upload_path, upload_bucket, key)


if __name__ == "__main__":
    # exif削除処理テスト
    remove_exif('./image/d5f4e21c-a10c-4c0d-9f79_78QE6YA.jpg')

    # 画像のリサイズテスト
    with Image.open('./image/d5f4e21c-a10c-4c0d-9f79_78QE6YA.jpg') as image:
        image = resize_image(image)
        image.save('./image/d5f4e21c-a10c-4c0d-9f79_78QE6YA.jpg')

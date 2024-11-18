import logging
import requests_toolbelt.multipart as multipart
import base64
import boto3
import os
import random

def get_boto_s3():
    return boto3.client(
        's3',
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        region_name='ru-central1',
        endpoint_url='https://storage.yandexcloud.net',
        config=boto3.session.Config(signature_version='s3v4')
    )

def generate_filename():
    adjective = random.choice(open("english-adjectives.txt").readlines()).strip()
    noun = random.choice(open("english-nouns.txt").readlines()).strip()
    return adjective+noun

def file_exists(s3, filename):
    try:
        s3.head_object(Bucket=os.environ['BUCKET_NAME'], Key=f'files/{filename}')
        return True
    except:
        return False

def handler(event, context):
    logger = logging.getLogger('simple_logger')
    logger.setLevel(logging.DEBUG)
    if event['httpMethod'] != 'POST':
        return {
            "statusCode": 400,
            "body": "Invalid request"
        }
    content_type = event['headers']['Content-Type']
    if content_type.split(';')[0] != 'multipart/form-data':
        logger.info(f'Content-Type: {content_type}')
        return {
            "statusCode": 400,
            "body": "Invalid Content-Type"
        }
    data = event['body']
    if event['isBase64Encoded']:
        data = base64.b64decode(data)
    logger.info(f'Data: {data}')

    for part in multipart.MultipartDecoder(data, content_type).parts:
        decoded_header = part.headers[b'Content-Disposition'].decode('utf-8')
        if decoded_header.startswith('form-data; name="file"'):
            filename = generate_filename()
            s3 = get_boto_s3()
            while file_exists(s3, filename):
                filename = generate_filename()
            response = s3.put_object(
                Key=f'files/{filename}',
                Bucket=os.environ['BUCKET_NAME'],
                Body=part.content,
                ACL='public-read'
            )
            logger.info(response)
            return {
                "statusCode": 200,
                "body": f'https://storage.yandexcloud.net/{os.environ["BUCKET_NAME"]}/files/{filename}'
            }

    return {
        "statusCode": 400,
        "body": "No file in request"
    }
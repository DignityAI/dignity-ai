import os
from google.cloud import storage
import boto3

THRESHOLD = 50 * 1024 * 1024  # 50MB
upload_to_gcs = os.getenv('GCS_BUCKET') is not None
upload_to_s3 = os.getenv('S3_BUCKET') is not None

def upload_gcs(local_path, bucket_name):
    client = storage.Client.from_service_account_json(os.getenv('GCS_CREDENTIALS'))
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(os.path.basename(local_path))
    blob.upload_from_filename(local_path)
    print(f'Uploaded {local_path} to GCS bucket {bucket_name}')

def upload_s3(local_path, bucket_name):
    s3 = boto3.client('s3')
    s3.upload_file(local_path, bucket_name, os.path.basename(local_path))
    print(f'Uploaded {local_path} to S3 bucket {bucket_name}')

for root, dirs, files in os.walk('output/IL'):
    for f in files:
        path = os.path.join(root, f)
        size = os.path.getsize(path)
        if size > THRESHOLD:
            if upload_to_gcs:
                upload_gcs(path, os.getenv('GCS_BUCKET'))
            elif upload_to_s3:
                upload_s3(path, os.getenv('S3_BUCKET'))
            else:
                print(f'Large file found but no cloud bucket configured: {path}')

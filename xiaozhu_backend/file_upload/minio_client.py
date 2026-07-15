from minio import Minio
from minio.error import S3Error
from django.conf import settings


def get_minio_client():
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )


def ensure_bucket_exists(client, bucket_name):
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)


def upload_file_to_minio(file_obj, object_name):
    client = get_minio_client()
    ensure_bucket_exists(client, settings.MINIO_BUCKET_NAME)
    
    file_obj.seek(0)
    
    try:
        client.put_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            data=file_obj,
            length=-1,
            part_size=10 * 1024 * 1024
        )
        base_url = f"http://{settings.MINIO_ENDPOINT}" if not settings.MINIO_SECURE else f"https://{settings.MINIO_ENDPOINT}"
        file_url = f"{base_url}/{settings.MINIO_BUCKET_NAME}/{object_name}"
        return {"success": True, "url": file_url}
    except S3Error as e:
        return {"success": False, "error": str(e)}
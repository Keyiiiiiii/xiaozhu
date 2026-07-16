from urllib.parse import urlparse

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
        protocol = "http" if not settings.MINIO_SECURE else "https"
        base_url = f"{protocol}://{settings.MINIO_ENDPOINT}"
        file_url = f"{base_url}/{settings.MINIO_BUCKET_NAME}/{object_name}"
        return {"success": True, "url": file_url}
    except S3Error as e:
        return {"success": False, "error": str(e)}


def get_file_from_minio(file_url):
    parsed_url = urlparse(file_url)
    path_parts = parsed_url.path.lstrip("/").split("/")

    if len(path_parts) < 2:
        return {"success": False, "error": "无效的文件URL"}

    bucket_name = path_parts[0]
    object_name = "/".join(path_parts[1:])

    client = get_minio_client()

    try:
        response = client.get_object(bucket_name, object_name)
        file_content = response.read()
        response.close()
        response.release_conn()
        return {"success": True, "content": file_content, "object_name": object_name}
    except S3Error as e:
        return {"success": False, "error": str(e)}

import os
import boto3
from botocore.config import Config
from config import R2_CONFIG

def is_r2_configured():
    return bool(R2_CONFIG.get("access_key_id") and R2_CONFIG.get("secret_access_key") and R2_CONFIG.get("endpoint_url"))

def get_r2_client():
    if not is_r2_configured():
        return None
    return boto3.client(
        "s3",
        endpoint_url=R2_CONFIG["endpoint_url"],
        aws_access_key_id=R2_CONFIG["access_key_id"],
        aws_secret_access_key=R2_CONFIG["secret_access_key"],
        config=Config(signature_version="s3v4"),
        region_name="auto"
    )

def upload_string_to_r2(content_str, r2_key, content_type="text/plain; charset=utf-8"):
    # Always save to local dist folder as well
    dist_dir = os.path.join(os.path.dirname(__file__), "dist")
    os.makedirs(dist_dir, exist_ok=True)
    local_path = os.path.join(dist_dir, r2_key)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(content_str)

    if not is_r2_configured():
        print(f"📁 [Local Dist] R2 未配置，已保存在本地静态目录: {local_path}")
        return local_path

    try:
        client = get_r2_client()
        client.put_object(
            Bucket=R2_CONFIG["bucket_name"],
            Key=r2_key,
            Body=content_str.encode("utf-8"),
            ContentType=content_type,
            CacheControl="no-cache, no-store, must-revalidate"
        )
        public_url = f"{R2_CONFIG['public_domain'].rstrip('/')}/{r2_key}"
        print(f"✅ [R2] Uploaded: {r2_key} -> {public_url}")
        return public_url
    except Exception as e:
        print(f"⚠️ [R2 Upload Notice] 上传跳过或失败 ({e})，已保存在本地: {local_path}")
        return local_path

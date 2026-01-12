from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3, os, time
from dotenv import load_dotenv
from botocore.config import Config

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
BUCKET = os.getenv("S3_BUCKET")

#  CONFIG WAJIB 
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(
        signature_version="s3v4",
        s3={
            "addressing_style": "virtual"  # ⬅WAJIB UNTUK ap-southeast-3
        }
    )
)

print("S3 REGION :", s3.meta.region_name)
print("S3 ENDPOINT:", s3.meta.endpoint_url)

app = FastAPI()

KTP_FOLDER = "KTP"


# create presigned upload url
class UploadBody(BaseModel):
    filename: str
    type: str


@app.post("/upload")
def upload_url(body: UploadBody):
    if not body.filename or not body.type:
        raise HTTPException(400, "filename & type required")

    key = f"{KTP_FOLDER}/{int(time.time() * 1000)}-{body.filename}"

    try:
        url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": BUCKET,
                "Key": key,
                # "ContentType": body.type
            },
            ExpiresIn=3600
        )

        return {
            "key": key,
            "url": url
        }

    except Exception as e:
        print("UPLOAD ERROR:", e)
        raise HTTPException(500, "Failed to generate upload URL")


# download file
@app.get("/download")
def download_url(key: str):
    if not key:
        raise HTTPException(400, "key required")

    try:
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": BUCKET,
                "Key": key
            },
            ExpiresIn=3600
        )

        return {
            "url": url
        }

    except Exception as e:
        print("DOWNLOAD ERROR:", e)
        raise HTTPException(500, "Failed to generate download URL")

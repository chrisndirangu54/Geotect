from __future__ import annotations
import os
from dataclasses import dataclass
@dataclass
class ObjectStoreConfig:
    endpoint_url:str|None
    bucket:str
    region:str|None
    access_key:str|None
    secret_key:str|None

def config()->ObjectStoreConfig:
    return ObjectStoreConfig(os.getenv("S3_ENDPOINT_URL"),os.getenv("GEOTECT_OBJECT_BUCKET","geotect"),os.getenv("AWS_REGION"),os.getenv("AWS_ACCESS_KEY_ID"),os.getenv("AWS_SECRET_ACCESS_KEY"))

def client():
    try:import boto3
    except Exception as exc:raise RuntimeError("boto3 is required for object storage") from exc
    c=config()
    return boto3.client("s3",endpoint_url=c.endpoint_url,region_name=c.region,aws_access_key_id=c.access_key,aws_secret_access_key=c.secret_key)

def presigned_get(key:str,expires:int=900)->dict:
    c=config();s3=client();url=s3.generate_presigned_url("get_object",Params={"Bucket":c.bucket,"Key":key},ExpiresIn=expires)
    return {"bucket":c.bucket,"key":key,"url":url,"expires_seconds":expires}

def presigned_put(key:str,content_type:str="application/octet-stream",expires:int=900)->dict:
    c=config();s3=client();url=s3.generate_presigned_url("put_object",Params={"Bucket":c.bucket,"Key":key,"ContentType":content_type},ExpiresIn=expires)
    return {"bucket":c.bucket,"key":key,"url":url,"headers":{"Content-Type":content_type},"expires_seconds":expires}

def range_get(key:str,start:int,end:int)->bytes:
    c=config();resp=client().get_object(Bucket=c.bucket,Key=key,Range=f"bytes={start}-{end}")
    return resp["Body"].read()

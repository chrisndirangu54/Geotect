from __future__ import annotations
from sqlalchemy import select
from db import SessionLocal
from admin_models import ModelConfig,ApiSecret
from secret_crypto import decrypt_secret

DEFAULT_MODELS={
 "assistant":{"provider":"openai","model":"gpt-5.6","parameters":{"temperature":0.2}},
 "geology_interpretation":{"provider":"openai","model":"gpt-5.6","parameters":{"temperature":0.1}},
 "vision":{"provider":"openai","model":"gpt-5.6","parameters":{}},
 "embeddings":{"provider":"openai","model":"text-embedding-3-large","parameters":{}}
}

async def get_model_config(task:str)->dict:
    async with SessionLocal() as s:
        row=await s.get(ModelConfig,task)
        if row and row.enabled:return {"provider":row.provider,"model":row.model,"parameters":row.parameters}
    return DEFAULT_MODELS.get(task,DEFAULT_MODELS["assistant"])

async def get_provider_secret(provider:str,name:str="api_key")->str|None:
    async with SessionLocal() as s:
        q=await s.execute(select(ApiSecret).where(ApiSecret.provider==provider,ApiSecret.name==name,ApiSecret.enabled.is_(True)))
        row=q.scalar_one_or_none()
        return decrypt_secret(row.encrypted_value) if row else None

from __future__ import annotations
import base64,hashlib,json
from datetime import datetime,timezone

def digest_payload(payload:dict)->str:
    raw=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

def verify_x509_signature(payload:dict,signature_b64:str,certificate_pem:str,algorithm:str="sha256")->dict:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding,ec,rsa
    cert=x509.load_pem_x509_certificate(certificate_pem.encode())
    raw=json.dumps(payload,sort_keys=True,separators=(",",":")).encode();sig=base64.b64decode(signature_b64)
    pub=cert.public_key();h=hashes.SHA256()
    try:
        if isinstance(pub,rsa.RSAPublicKey):pub.verify(sig,raw,padding.PKCS1v15(),h)
        elif isinstance(pub,ec.EllipticCurvePublicKey):pub.verify(sig,raw,ec.ECDSA(h))
        else:raise ValueError("Unsupported public key type")
        ok=True;err=None
    except Exception as exc:ok=False;err=str(exc)
    return {"valid":ok,"error":err,"subject":cert.subject.rfc4514_string(),"issuer":cert.issuer.rfc4514_string(),
      "serial_number":str(cert.serial_number),"not_valid_before":cert.not_valid_before_utc.isoformat(),"not_valid_after":cert.not_valid_after_utc.isoformat(),
      "payload_sha256":hashlib.sha256(raw).hexdigest(),"verified_at":datetime.now(timezone.utc).isoformat()}

async def external_sign_request(url:str,token:str,payload_digest:str,metadata:dict|None=None)->dict:
    import httpx
    if not url.startswith("https://"):raise ValueError("PKI provider URL must use HTTPS")
    body={"digest_sha256":payload_digest,"metadata":metadata or {}}
    async with httpx.AsyncClient(timeout=60) as c:
        r=await c.post(url,headers={"Authorization":f"Bearer {token}","Accept":"application/json"},json=body);r.raise_for_status();return r.json()

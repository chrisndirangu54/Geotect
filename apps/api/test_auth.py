import auth
from secret_crypto import encrypt_secret,decrypt_secret

def test_secret_round_trip(monkeypatch):
    monkeypatch.setenv("GEOTECT_MASTER_KEY","unit-test-master-key-with-sufficient-entropy")
    secret="sk-test-1234567890"
    assert decrypt_secret(encrypt_secret(secret))==secret

def test_dev_super_admin_claim(monkeypatch):
    monkeypatch.setattr(auth,"DEV_AUTH",True)
    claims=auth.verify_token("dev-super-admin")
    assert claims["email"].lower()==auth.BOOTSTRAP_SUPER_ADMIN

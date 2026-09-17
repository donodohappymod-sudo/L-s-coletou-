import hashlib, hmac, secrets

ALGO='pbkdf2_sha256'; ITERATIONS=600_000

def hash_password(password: str) -> str:
    salt=secrets.token_bytes(16)
    digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,ITERATIONS)
    return f'{ALGO}${ITERATIONS}${salt.hex()}${digest.hex()}'

def verify_password(password: str, encoded: str) -> bool:
    try:
        algo,iters,salt_hex,digest_hex=encoded.split('$',3)
        if algo!=ALGO: return False
        digest=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt_hex),int(iters))
        return hmac.compare_digest(digest.hex(),digest_hex)
    except (ValueError,TypeError): return False

#app/security.py
import os, secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

def require_basic_auth(creds: HTTPBasicCredentials = Depends(security)) -> None:
    # Valores por defecto si no hay variables de entorno
    expected_user = os.environ.get("DASH_USER", "admin")
    expected_pass = os.environ.get("DASH_PASS", "admin")
    
    user_ok = secrets.compare_digest(creds.username, expected_user)
    pass_ok = secrets.compare_digest(creds.password, expected_pass)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )

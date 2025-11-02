"""
Credentials API endpoints - Manage .env credential entries
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any
from pathlib import Path
from dotenv import set_key, load_dotenv
import os


router = APIRouter(prefix="/credentials", tags=["credentials"])


class CredentialPayload(BaseModel):
    key: str = Field(..., min_length=1, description="Environment variable key")
    value: str = Field(..., description="Environment variable value")


@router.post("/set", response_model=Dict[str, Any])
async def set_credential(payload: CredentialPayload):
    """
    Create or update a key-value in the backend .env file and reload environment variables.
    """
    try:
        env_path = Path(".") / ".env"
        env_path.touch(exist_ok=True)
        load_dotenv(env_path)  # ensure loaded/created

        set_key(str(env_path), payload.key, payload.value)
        
        # Reload environment variables to make them available immediately
        load_dotenv(env_path, override=True)
        
        # Update the current process environment
        os.environ[payload.key] = payload.value

        return {
            "success": True,
            "data": {
                "key": payload.key,
                "message": "Credential saved to .env and environment reloaded"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set credential: {str(e)}")


class DeletePayload(BaseModel):
    key: str = Field(..., min_length=1, description="Environment variable key to remove")


@router.post("/delete", response_model=Dict[str, Any])
async def delete_credential(payload: DeletePayload):
    """
    Remove a key from the backend .env file by rewriting it without the key.
    """
    try:
        env_path = Path(".") / ".env"
        env_path.touch(exist_ok=True)

        # Read all lines and filter out the key
        lines = env_path.read_text(encoding="utf-8").splitlines()
        key_prefix = f"{payload.key}="
        new_lines = [line for line in lines if not line.strip().startswith(key_prefix)]
        env_path.write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")
        
        # Remove from current process environment
        if payload.key in os.environ:
            del os.environ[payload.key]

        return {
            "success": True,
            "data": {
                "key": payload.key,
                "message": "Credential removed from .env and environment"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete credential: {str(e)}")


@router.get("/", response_model=Dict[str, Any])
async def list_credentials():
    """
    List all credentials (keys) from the .env file without exposing their values.
    
    Returns:
        Dict containing list of credential keys
    """
    try:
        env_path = Path(".") / ".env"
        credentials = []
        
        if env_path.exists():
            # Read the .env file and parse all key-value pairs
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                
                # Parse KEY=VALUE format
                if "=" in line:
                    key = line.split("=", 1)[0].strip()
                    if key:
                        credentials.append(key)
        
        return {
            "success": True,
            "data": {
                "credentials": credentials,
                "count": len(credentials)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list credentials: {str(e)}")


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_environment():
    """
    Reload all environment variables from the .env file without restarting the server.
    """
    try:
        env_path = Path(".") / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)
            return {
                "success": True,
                "data": {
                    "message": "Environment variables refreshed from .env file"
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "message": "No .env file found, no refresh needed"
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh environment: {str(e)}")



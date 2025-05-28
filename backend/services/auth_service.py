# backend/services/auth_service.py
from functools import wraps
from flask import request, jsonify
import jwt
import os

def require_api_key(f):
    """Simple API key decorator (placeholder for future auth)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For now, just pass through - implement proper auth later
        return f(*args, **kwargs)
    return decorated_function

def validate_api_key(api_key):
    """Validate API key (placeholder)"""
    return True  # Always valid for now

def generate_api_key():
    """Generate API key for users"""
    import secrets
    return secrets.token_urlsafe(32)
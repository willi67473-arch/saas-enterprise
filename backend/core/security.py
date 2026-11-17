"""Jetons : générés aléatoirement, jamais stockés en clair (SHA-256 en base)."""
import hashlib
import secrets
import string


def generate_token(nbytes=32):
    return secrets.token_urlsafe(nbytes)


def hash_token(raw):
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

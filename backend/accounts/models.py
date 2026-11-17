from datetime import timedelta

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone

from core.security import generate_token, hash_token


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse courriel est obligatoire.")
        user = self.model(email=self.normalize_email(email).lower(), **extra_fields)
        user.set_password(password)  # haché (PBKDF2 par défaut), jamais en clair
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    # Le tenant n'est JAMAIS modifiable via l'API ; null uniquement pour un compte technique.
    tenant = models.ForeignKey("tenants.Tenant", null=True, blank=True, on_delete=models.CASCADE, related_name="users")
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    role = models.CharField(max_length=20, default="USER")  # SUPER_ADMIN | ADMIN | MANAGER | USER
    plan = models.CharField(max_length=50, default="FREE")
    status = models.CharField(max_length=20, default="ACTIVE")  # ACTIVE | SUSPENDED
    avatar = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nom", "prenom"]

    def __str__(self):
        return self.email


class AuthToken(models.Model):
    """Jeton d'API : expirant, révocable (suppression au /logout), stocké sous forme hachée."""

    key = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="auth_tokens")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_used_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def issue(cls, user):
        """Crée un jeton et renvoie sa valeur en clair (affichée UNE seule fois)."""
        cls.objects.filter(expires_at__lt=timezone.now()).delete()  # ménage des jetons expirés
        raw = generate_token()
        cls.objects.create(
            key=hash_token(raw),
            user=user,
            expires_at=timezone.now() + timedelta(days=settings.TOKEN_LIFETIME_DAYS),
        )
        return raw

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # Supabase auth.users.id (JWT의 sub). 로그인은 Supabase가 담당하므로 Django 비밀번호는 사용하지 않는다.
    supabase_id = models.UUIDField(unique=True, null=True, blank=True)
    avatar_url = models.URLField(blank=True)

    def __str__(self):
        return self.email or self.username

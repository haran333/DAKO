import time
import uuid
from unittest import mock

import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import User

SUPABASE_URL = "https://test.supabase.co"
JWT_SECRET = "test-secret-that-is-long-enough-for-hs256"


def make_payload(**overrides):
    payload = {
        "sub": str(uuid.uuid4()),
        "aud": "authenticated",
        "iss": f"{SUPABASE_URL}/auth/v1",
        "exp": int(time.time()) + 3600,
        "email": "user@example.com",
        "user_metadata": {"full_name": "홍길동", "avatar_url": "https://example.com/a.png"},
    }
    payload.update(overrides)
    return payload


@override_settings(SUPABASE_URL=SUPABASE_URL, SUPABASE_JWT_SECRET=JWT_SECRET)
class SupabaseAuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def get_me(self, token):
        return self.client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_no_token_is_rejected(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

    def test_hs256_token_creates_user(self):
        payload = make_payload()
        res = self.get_me(jwt.encode(payload, JWT_SECRET, algorithm="HS256"))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["email"], "user@example.com")
        self.assertEqual(res.data["name"], "홍길동")
        user = User.objects.get(supabase_id=payload["sub"])
        self.assertFalse(user.has_usable_password())

    def test_same_sub_reuses_user(self):
        token = jwt.encode(make_payload(), JWT_SECRET, algorithm="HS256")
        self.get_me(token)
        self.get_me(token)
        self.assertEqual(User.objects.count(), 1)

    def test_es256_token_verified_with_jwks(self):
        private_key = ec.generate_private_key(ec.SECP256R1())
        token = jwt.encode(make_payload(), private_key, algorithm="ES256", headers={"kid": "k1"})
        signing_key = mock.Mock(key=private_key.public_key())

        with mock.patch("accounts.authentication._get_jwks_client") as get_client:
            get_client.return_value.get_signing_key_from_jwt.return_value = signing_key
            res = self.get_me(token)

        self.assertEqual(res.status_code, 200)

    def test_expired_token_is_rejected(self):
        token = jwt.encode(make_payload(exp=int(time.time()) - 10), JWT_SECRET, algorithm="HS256")
        self.assertEqual(self.get_me(token).status_code, 401)

    def test_wrong_secret_is_rejected(self):
        token = jwt.encode(make_payload(), "wrong-secret-that-is-long-enough-xx", algorithm="HS256")
        self.assertEqual(self.get_me(token).status_code, 401)

    def test_wrong_audience_is_rejected(self):
        token = jwt.encode(make_payload(aud="anon"), JWT_SECRET, algorithm="HS256")
        self.assertEqual(self.get_me(token).status_code, 401)

    def test_wrong_issuer_is_rejected(self):
        token = jwt.encode(make_payload(iss="https://other.supabase.co/auth/v1"), JWT_SECRET, algorithm="HS256")
        self.assertEqual(self.get_me(token).status_code, 401)


@override_settings(SUPABASE_URL=SUPABASE_URL, SUPABASE_ANON_KEY="anon-key")
class PageTests(TestCase):
    def test_index_renders_with_supabase_config(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'window.SUPABASE_URL = "https://test.supabase.co"')
        self.assertContains(res, 'window.SUPABASE_ANON_KEY = "anon-key"')

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

_jwks_client = None


def _get_jwks_client():
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = jwt.PyJWKClient(
            f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json",
            cache_keys=True,
        )
    return _jwks_client


def verify_supabase_token(token):
    """Supabase access token을 검증하고 payload를 반환한다.

    - HS256: 레거시 JWT secret(SUPABASE_JWT_SECRET)으로 검증
    - ES256/RS256: Supabase JWKS 공개키로 검증 (신규 프로젝트 기본값)
    """
    try:
        alg = jwt.get_unverified_header(token).get("alg")
    except jwt.PyJWTError:
        raise exceptions.AuthenticationFailed("잘못된 토큰 형식입니다.")

    if alg == "HS256":
        if not settings.SUPABASE_JWT_SECRET:
            raise exceptions.AuthenticationFailed("HS256 토큰을 검증할 secret이 설정되지 않았습니다.")
        key = settings.SUPABASE_JWT_SECRET
    elif alg in ("ES256", "RS256"):
        try:
            key = _get_jwks_client().get_signing_key_from_jwt(token).key
        except jwt.PyJWTError:
            raise exceptions.AuthenticationFailed("토큰 서명 키를 찾을 수 없습니다.")
    else:
        raise exceptions.AuthenticationFailed("지원하지 않는 토큰 알고리즘입니다.")

    try:
        return jwt.decode(
            token,
            key,
            algorithms=[alg],
            audience="authenticated",
            issuer=f"{settings.SUPABASE_URL}/auth/v1",
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise exceptions.AuthenticationFailed("토큰이 만료되었습니다.")
    except jwt.PyJWTError:
        raise exceptions.AuthenticationFailed("유효하지 않은 토큰입니다.")


def get_or_create_user(payload):
    User = get_user_model()
    metadata = payload.get("user_metadata") or {}
    email = payload.get("email", "")

    user, created = User.objects.get_or_create(
        supabase_id=payload["sub"],
        defaults={"username": payload["sub"], "email": email},
    )
    if created:
        user.set_unusable_password()

    # Google 프로필 정보 동기화
    user.email = email
    user.first_name = (metadata.get("full_name") or metadata.get("name") or "")[:150]
    user.avatar_url = metadata.get("avatar_url") or metadata.get("picture") or ""
    user.save()
    return user


class SupabaseAuthentication(authentication.BaseAuthentication):
    """`Authorization: Bearer <supabase access token>` 헤더로 사용자를 인증한다."""

    keyword = "Bearer"

    def authenticate(self, request):
        auth = authentication.get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None
        if len(auth) != 2:
            raise exceptions.AuthenticationFailed("Authorization 헤더 형식이 잘못되었습니다.")

        payload = verify_supabase_token(auth[1].decode())
        user = get_or_create_user(payload)
        if not user.is_active:
            raise exceptions.AuthenticationFailed("비활성화된 사용자입니다.")
        return user, payload

    def authenticate_header(self, request):
        return self.keyword

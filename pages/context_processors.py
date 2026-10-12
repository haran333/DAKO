from django.conf import settings


def supabase(request):
    """프론트 HTML에서 {{ SUPABASE_URL }}, {{ SUPABASE_ANON_KEY }}로 사용할 수 있게 한다."""
    return {
        "SUPABASE_URL": settings.SUPABASE_URL,
        "SUPABASE_ANON_KEY": settings.SUPABASE_ANON_KEY,
    }

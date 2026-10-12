from django.urls import path
from django.views.generic import TemplateView

# 프론트 HTML은 templates/pages/ 에 넣고 여기에 한 줄씩 추가한다.
# 로그인 여부 확인은 프론트(Supabase JS)가 담당하고, 데이터는 /api/ 에서 토큰으로 검증한다.
urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/index.html"), name="index"),
]

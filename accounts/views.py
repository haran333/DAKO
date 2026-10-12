from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSerializer


class MeView(APIView):
    """토큰 검증 결과로 현재 로그인한 사용자 정보를 반환한다."""

    def get(self, request):
        return Response(UserSerializer(request.user).data)

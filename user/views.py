from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from user.models import User, UserTokenService
from user.serializers import SignInSerializer, UserCreateSerializer
from rest_framework.response import Response


class PartialPutMixin:

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


@extend_schema(tags=['User'])
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


@extend_schema(tags=['Login'])
class SignInAPIView(APIView):
    serializer_class = SignInSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        return Response({
            'success': True,
            'status_code': 200,
            'message': 'User logged in successfully',
            'data': UserTokenService.get_tokens_for_user(user),
        }, status=status.HTTP_200_OK)

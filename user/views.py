from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from user.models import User, UserTokenService
from user.serializers import SignInSerializer, UserCreateSerializer, LogoutSerializer, MeSerializer
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

        tokens = UserTokenService.get_tokens_for_user(user)
        response = Response({
            'success': True,
            'status_code': 200,
            'message': 'User logged in successfully',
            'data': {
                'access': tokens['access'],
            },
        }, status=status.HTTP_200_OK)

        response.set_cookie(
            key='refresh_token',
            value=tokens['refresh'],
            httponly=True,
            secure=True,
            samesite='Strict',
            max_age=60 * 60 * 24 * 7
        )

        return response


@extend_schema(tags=['Login'])
class LogOutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "Invalid request."}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Profile'])
class MeAPIView(RetrieveAPIView):
    serializer_class = MeSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

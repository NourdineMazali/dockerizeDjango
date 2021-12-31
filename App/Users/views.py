import datetime
import logging

from django.http.response import JsonResponse
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status, viewsets

from Users.models import User
from Users.serializers import UserSerializer, UserLoginSerializer,\
    UserSignUpSerializer
from Users.utils import get_user_or_error


logger = logging.getLogger(__name__)

SUCCESS = status.HTTP_200_OK
CREATED = status.HTTP_201_CREATED
UPDATED = status.HTTP_202_ACCEPTED
DELETED = status.HTTP_204_NO_CONTENT
FORBIDDEN = status.HTTP_403_FORBIDDEN
NOT_FOUND = status.HTTP_404_NOT_FOUND

class UserViewSet(viewsets.GenericViewSet):
    """
    API endpoint that allows to interact with User model
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def list(self, request):
        """
        API endpoint that allows to list all users
        """
        request_user = request.user
        if not request_user.is_admin:
            return Response("You don't have permission", status=FORBIDDEN)
        users = User.objects.all().order_by('-created_at')
        serializer = UserSerializer(users, many=True)
        data = serializer.data
        return Response(data, status=SUCCESS)

    def retrieve(self, request, pk=None):
        """
        API endpoint that allow to get information of one user
        """
        request_user = request.user
        instance, error = get_user_or_error(request_user, pk)
        if error:
            return error
        data = UserLoginSerializer(instance).data
        return Response(data, status=SUCCESS)

    def update(self, request, pk=None):
        """
        API endpoint that allow to edit an user
        """
        request_user = request.user
        instance, error = get_user_or_error(request_user, pk)
        if error:
            return error
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(request.data, request_user)
        user = serializer.update(instance, request.data)
        data = UserSerializer(user).data
        logger.warning(f'Users App | User "{user.id}" updated at {datetime.datetime.now()}')
        return Response(data, status=UPDATED)

    def destroy(self, request, pk=None):
        """
        API endpoint that allow to delete an user
        """
        request_user = request.user
        instance, error = get_user_or_error(request_user, pk)
        if error:
            return error
        logger.warning(f'Users App | User "{instance.id}" deleted at {datetime.datetime.now()}')
        instance.delete()
        return Response(status=DELETED)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def signup(self, request):
        """
        API endpoint that allows to signup
        """
        serializer = UserSignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = UserSignUpSerializer(user).data
        return Response(data, status=CREATED)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        API endpoint that allows to login
        """
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, token = serializer.save()
        data = {"user": UserLoginSerializer(user).data,
                "token": token}
        return JsonResponse(data, status=SUCCESS)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def verify(self, request, pk=None):
        """
        API endpoint that allows to verify user
        """
        query_token = request.query_params.get('token')
        user = User.objects.all().get(id=pk)
        token = user.generate_verification_token()
        if token != query_token:
            return Response("You don't have permission", status=FORBIDDEN)
        user.is_verified = True
        user.save()
        data = {"user": UserLoginSerializer(user).data}
        return JsonResponse(data, status=UPDATED)

'''
views.py
'''
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer, LoginSerializer, GuardianSerializer, ProfileSerializer
from .models import User, Guardian
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": token.key,
        }, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})


class GuardianViewSet(viewsets.ModelViewSet):
    serializer_class = GuardianSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Guardian.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['DELETE'], detail=False, url_path='delete')
    def delete_guardian(self, request):
        name = request.query_params.get('name')
        phone_number = request.query_params.get('phone_number')

        if not name or not phone_number:
            return Response({"detail": "Both name and phone_number are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            guardian = Guardian.objects.get(user=request.user, name=name, phone_number=phone_number)
        except Guardian.DoesNotExist:
            return Response({"detail": "Guardian not found."}, status=status.HTTP_404_NOT_FOUND)

        guardian.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['PATCH'], detail=False, url_path='update')
    def update_guardian(self, request):
        name = request.data.get('old_name')
        phone_number = request.data.get('old_phone_number')

        if not name or not phone_number:
            return Response({"detail": "Both old_name and old_phone_number are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            guardian = Guardian.objects.get(user=request.user, name=name, phone_number=phone_number)
        except Guardian.DoesNotExist:
            return Response({"detail": "Guardian not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(guardian, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        profile_data = request.data.get('profile', {})
        serializer = ProfileSerializer(user.profile, data=profile_data, partial=False)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        user = request.user
        profile_data = request.data.get('profile', {})
        serializer = ProfileSerializer(user.profile, data=profile_data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.delete()
        return Response({"detail": "User account has been successfully deleted."}, status=status.HTTP_204_NO_CONTENT)

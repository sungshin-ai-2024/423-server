'''
views.py
'''

from rest_framework import generics, status, viewsets
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
        # Only return guardians for the logged-in user
        return Guardian.objects.filter(user=self.request.user)

    def get_object(self):
        # Get the guardian object and ensure it belongs to the logged-in user
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied("You do not have permission to access this guardian.")
        return obj

    def perform_create(self, serializer):
        # Save the user who created the guardian information
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # Ensure that the user can only update their own guardian information
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You do not have permission to edit this guardian.")
        serializer.save()

class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

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
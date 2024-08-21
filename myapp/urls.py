from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, LoginView, GuardianViewSet, DeleteAccountView, UserProfileView

router = DefaultRouter()
router.register(r'guardians', GuardianViewSet, basename='guardian')

api_patterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('delete_account/', DeleteAccountView.as_view(), name='delete_account'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),  # Updated route for user profile
    path('', include(router.urls)),
]

urlpatterns = [
    path('', include(api_patterns))
]
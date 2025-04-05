from rest_framework.routers import DefaultRouter

from .views import SSHCredentialViewSet, WinRMCredentialViewSet, HostViewSet, UserViewSet


router = DefaultRouter()

router.register(r'users', UserViewSet, basename='user')
router.register('ssh-credential', SSHCredentialViewSet,
                basename='ssh-credential')
router.register('winrm-credential', WinRMCredentialViewSet,
                basename='winrm-credential')
router.register('host', HostViewSet, basename='host')

urlpatterns = router.urls

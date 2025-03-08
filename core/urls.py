from rest_framework.routers import DefaultRouter

from .views import SSHCredentialViewSet, WinRMCredentialViewSet, HostViewSet


router = DefaultRouter()
router.register('ssh-credential', SSHCredentialViewSet,
                basename='ssh-credential')
router.register('winrm-credential', WinRMCredentialViewSet,
                basename='winrm-credential')
router.register('host', HostViewSet, basename='host')

urlpatterns = router.urls

from rest_framework.routers import DefaultRouter

from .views import ExecuteCommandViewSet, SendFileViewSet


router = DefaultRouter()
router.register('execute-command', ExecuteCommandViewSet,
                basename='execute-command')
router.register('send-file', SendFileViewSet,
                basename='send-file')

urlpatterns = router.urls

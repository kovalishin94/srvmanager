from rest_framework.routers import DefaultRouter

from .views import ExecuteCommandViewSet


router = DefaultRouter()
router.register('execute-command', ExecuteCommandViewSet,
                basename='execute-command')

urlpatterns = router.urls

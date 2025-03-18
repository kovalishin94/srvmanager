from rest_framework.routers import DefaultRouter

from .views import EtalonInstanceViewSet, UpdateFileViewSet


router = DefaultRouter()
router.register('etalon-instance', EtalonInstanceViewSet,
                basename='etalon-instance')
router.register('update-file', UpdateFileViewSet,
                basename='update-file')

urlpatterns = router.urls

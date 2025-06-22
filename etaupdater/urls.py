from rest_framework.routers import DefaultRouter

from .views import EtalonInstanceViewSet, UpdateFileViewSet, EtalonUpdateViewSet


router = DefaultRouter()
router.register('etalon-instance', EtalonInstanceViewSet, basename='etalon-instance')
router.register('update-file', UpdateFileViewSet, basename='update-file')
router.register('etalon-update', EtalonUpdateViewSet, basename='etalon-update')

urlpatterns = router.urls

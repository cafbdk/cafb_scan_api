"""cafb_scan_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from rest_framework import routers
from cafb_scan_api import views

router = routers.DefaultRouter(schema_title='CAFB Food Scanner API')
router.register(r'api/v1/scan', views.ScanViewSet)
router.register(r'api/v1/foodcat', views.FoodCatViewSet)
router.register(r'api/v1/wellscore', views.WellScoreViewSet)
router.register(r'api/v1/nutrule', views.NutRuleViewSet)
router.register(r'api/v1/upc', views.UPCViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
	# url(r'^admin/', admin.site.urls),
    url(r'^', include(router.urls)),
    url(r'^api/v1/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^scan/(?P<upc>[0-9]+)/$', views.scan_view),
    url(r'^scan_tracker/$', scan_tracker, name="scan_tracker"),
]
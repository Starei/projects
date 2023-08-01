from django.urls import include, path

api_patterns = [path("", include("test_app.urls"))]

urlpatterns = [path("api/", include(api_patterns))]

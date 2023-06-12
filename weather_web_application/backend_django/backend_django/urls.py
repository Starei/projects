from django.urls import path, include


api_patterns = [
    path('', include('test_app.urls'))
]

urlpatterns = [
    path('api/', include(api_patterns))
]


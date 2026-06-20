"""
URL configuration for brainforge project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def handler500(request, *args, **kwargs):
    """Custom 500 error handler - returns JSON for AJAX requests."""
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {"status": "error", "message": "An internal server error occurred. Please check your GEMINI_API_KEY is set in the Render environment variables."},
            status=500,
        )
    from django.views.defaults import server_error
    return server_error(request, *args, **kwargs)


def handler400(request, exception, *args, **kwargs):
    """Custom 400 error handler - returns JSON for AJAX requests."""
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {"status": "error", "message": str(exception)},
            status=400,
        )
    from django.views.defaults import bad_request
    return bad_request(request, exception, *args, **kwargs)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("planner.urls")),
]

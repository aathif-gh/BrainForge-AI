from django.urls import path
from . import views

app_name = "planner"

urlpatterns = [
    path("", views.index_view, name="index"),
    path("project/<int:pk>/", views.project_detail_view, name="project_detail"),
    path("project/create/", views.create_project_view, name="create_project"),
    path("project/<int:pk>/delete/", views.delete_project_view, name="delete_project"),
    path("team/", views.team_details_view, name="team_details"),
    path(
        "project/<int:pk>/simulate/",
        views.what_if_simulate_view,
        name="what_if_simulate",
    ),
    path("project/<int:pk>/pdf/", views.download_pdf_view, name="download_pdf"),
    path("project/demo/", views.load_hackathon_demo_view, name="load_demo"),
    path("api/chat/", views.chat_api_view, name="chat_api"),
]

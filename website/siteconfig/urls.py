from django.urls import path
from knowledge import views
urlpatterns = [path("", views.home, name="home"), path("build/<slug:slug>/", views.workflow, name="workflow"), path("guides/", views.guides, name="guides"), path("guides/<slug:slug>/", views.detail, name="detail"), path("downloads/", views.downloads, name="downloads"), path("files/<path:name>", views.file, name="file"), path("healthz", views.health), path("robots.txt", views.robots), path("sitemap.xml", views.sitemap)]

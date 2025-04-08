from django.urls import path

from news_monitoring.story import views

app_name = "story"
urlpatterns = [
    path("", views.list_stories, name="list"),
    path("<int:story_id>/", views.list_duplicates, name="duplicates"),
    path("add/", views.add_or_edit, name="add"),
    path("edit/<int:story_id>/", views.add_or_edit, name="edit"),
    path("delete/<int:story_id>/", views.delete, name="delete"),
    path("fetch-story/", views.fetch_stories, name="fetch"),
    path("fetch-story/<int:story_id>/", views.fetch_stories, name="fetch_with_id"),
]

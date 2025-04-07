from django.contrib import admin

from .models import Story


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ("title", "source_id", "published_date", "root", "added_by", "added_on")
    search_fields = ("title", "root")
    list_filter = ("published_date", "source")
    ordering = ("-published_date",)
    date_hierarchy = "published_date"

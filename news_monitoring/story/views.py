from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django import shortcuts
from django.http import JsonResponse

from news_monitoring.story.models import Story
from news_monitoring.company.models import Company
from news_monitoring.story import services


@login_required
def add_or_edit(request, story_id=None):
    story = None
    companies = None
    tagged_companies = []

    if request.method == "POST":
        is_validated = services.validate_form_data(request.user, request.POST, story_id)
        print(is_validated)

        if not is_validated:
            return shortcuts.render(
                request,
                "story/add_story.html",
                {
                    "error": "Title and URL are required!",
                    "story": story,  # Pass css data if editing
                    "tagged_companies": tagged_companies
                },
            )
        return shortcuts.redirect("story:list")

    if story_id:
        story, tagged_companies = services.get_story(request.user, story_id)
        companies = Company.objects.filter(id__in=[company for company in tagged_companies])

    return shortcuts.render(
        request,
        "story/add_story.html",
        {
            "story": story,
            "companies": companies,
            "tagged_companies": tagged_companies
        }
    )


@login_required
def list_stories(request):
    return shortcuts.render(request, 'story/list_stories.html')


@login_required
def fetch_stories(request, story_id=None):
    search_query = request.GET.get('q', '').strip()
    filter_date = request.GET.get('date', '').strip()
    page_number = request.GET.get('page')

    stories_qs = services.get_stories(request.user, search_query, filter_date, story_id)
    return JsonResponse(services.get_stories_json(stories_qs, page_number))


@login_required
def delete(request, story_id):
    story = services.get_object_or_404(Story, id=story_id, added_by=request.user)
    story.delete()
    messages.success(request, "Story deleted successfully.")
    return shortcuts.redirect("story:list")


@login_required
def list_duplicates(request, story_id):
    return shortcuts.render(request, 'story/list_duplicates.html')

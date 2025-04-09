from django.core.paginator import Paginator
from django.db import transaction, IntegrityError
from django.db.models import Prefetch
from django.db.models import Q
from django.shortcuts import get_object_or_404

from news_monitoring.company.models import Company
from news_monitoring.story.models import Story


def get_story(user, story_id):
    story_qs = Story.objects.prefetch_related("tagged_companies")

    if not user.is_staff:
        story_qs = story_qs.select_related("company")

    story_obj = get_object_or_404(story_qs, id=story_id)
    tagged_companies = list(story_obj.tagged_companies.values_list("id", flat=True))

    return story_obj, tagged_companies


def get_stories(user, search_query, filter_date, story_id):
    """Fetch and filter stories based on search query and date."""

    stories_qs = Story.objects.select_related("company").prefetch_related(
        Prefetch("tagged_companies", queryset=Company.objects.only("id", "name"))
    )

    if not user.is_staff:
        stories_qs = stories_qs.filter(company=user.company)

    if search_query:
        stories_qs = stories_qs.filter(title__icontains=search_query)

    if filter_date:
        stories_qs = stories_qs.filter(published_date=filter_date)
        
    if story_id:
        return stories_qs.filter(Q(id=story_id) | Q(root_id=story_id))

    return stories_qs.filter(root_id=None)


def get_stories_json(stories_qs, page_number):
    """Paginate and return JSON response for AJAX requests."""
    paginator = Paginator(stories_qs, 10)
    page_obj = paginator.get_page(page_number)

    return {
        "stories": [
            {
                "id": story.id,
                "title": story.title,
                "article_url": story.article_url,
                "published_date": story.published_date.strftime('%Y-%m-%d'),
                "body_text": story.body_text[:100] + "..." if len(story.body_text) > 100 else story.body_text,
                "tagged_companies": [company.name for company in story.tagged_companies.all()],
                "persons": story.persons,
                "organizations": story.organizations,
                "locations": story.locations,
                "has_duplicates": story.child_stories.exists(),
            }
            for story in page_obj
        ],
        "has_next": page_obj.has_next(),
        "has_previous": page_obj.has_previous(),
        "current_page": page_obj.number,
        "total_pages": paginator.num_pages,
    }


def update_or_create_story(story, user, title, body_text, published_date, article_url, tagged_companies):
    try:
        with transaction.atomic():

            if story:
                story.title = title
                story.body_text = body_text
                story.published_date = published_date
                story.article_url = article_url
                story.updated_by = user
                story.save(update_fields=["title", "body_text", "published_date", "article_url", "updated_by"])
            else:
                story = Story.objects.create(
                    title=title,
                    body_text=body_text,
                    article_url=article_url,
                    published_date=published_date,
                    added_by=user,
                    company=user.company,
                )

            if tagged_companies:
                story.tagged_companies.set(tagged_companies)

        return True

    except IntegrityError as e:
        print(f"Database error while updating/creating source: {e}")
        return False

    except Exception as e:
        print(f"Unexpected error updating/creating source: {e}")
        return False


def validate_form_data(user, payload, story_id):
    try:
        title = payload.get("title")
        body_text = payload.get("body_text")
        published_date = payload.get("published_date")
        article_url = payload.get("article_url")
        tagged_companies = payload.getlist("tagged_companies")

        if title and article_url:
            story, _ = get_story(user, story_id) if story_id else (None, [])
            success = update_or_create_story(story, user, title, body_text, published_date, article_url,
                                             tagged_companies)
            return success

        return False

    except Exception as e:
        print("Exception Occured -", e)
        return False

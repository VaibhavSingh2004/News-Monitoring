import feedparser
import time
from bs4 import BeautifulSoup
from datetime import datetime

from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from news_monitoring.source.models import Source
from news_monitoring.story.models import Story


def get_source(user, source_id):
    """Fetch a single source with tagged companies."""
    try:
        queryset = Source.objects.prefetch_related("tagged_companies")

        if user.is_staff:
            source_obj = get_object_or_404(queryset, id=source_id)
        else:
            source_obj = get_object_or_404(queryset, id=source_id, company=user.company)

        return source_obj, list(source_obj.tagged_companies.values_list("id", flat=True))

    except Exception as e:
        print(f"Error fetching source object: {e}")
        return None, []


def get_sources(user, search_query):
    """Fetch sources filtered by user and search query."""
    try:
        queryset = Source.objects.select_related("company").prefetch_related("tagged_companies")
        if not user.is_staff:
            queryset = queryset.filter(company=user.company)

        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        return queryset

    except Exception as e:
        print(f"Error fetching sources: {e}")
        return Source.objects.none()


def get_sources_json(sources_qs, page_number):
    """Return paginated sources as JSON."""
    paginator = Paginator(sources_qs, 10)  # Paginate results
    page_obj = paginator.get_page(page_number)

    sources_data = [
        {
            "id": source.id,
            "name": source.name,
            "url": source.url,
            "tagged_companies": [company.name for company in source.tagged_companies.all()],
        }
        for source in page_obj
    ]

    return JsonResponse({
        "sources": sources_data,
        "has_next": page_obj.has_next(),
        "has_previous": page_obj.has_previous(),
        "current_page": page_obj.number,
        "total_pages": paginator.num_pages,
    })


def update_or_create_source(source, user, name, url, company, tagged_companies):
    """Create or update a source with optimized database transactions."""
    try:
        with transaction.atomic():

            if source:
                source.name = name
                source.url = url
                source.company = company
                source.updated_by = user
                source.save(update_fields=["name", "url", "company", "updated_by"])
            else:
                source = Source.objects.create(name=name, url=url, company=company, added_by=user)

            if tagged_companies:
                source.tagged_companies.set(tagged_companies)

        return True
    except IntegrityError as e:
        print(f"Database error while updating/creating source: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error updating/creating source: {e}")
        return False


def validate_form_data(user, payload, source_id):
    """Validate form data and create/update the source."""
    try:
        name = payload.get("name")
        url = payload.get("url")
        company = user.company
        tagged_companies = payload.getlist("tagged_companies")

        if name and url:
            source, _ = get_source(user, source_id) if source_id else (None, [])
            success = update_or_create_source(source, user, name, url, company, tagged_companies)

            return success, "Success" if success else "Error updating source"

        return False, "Name and URL are required fields."

    except Exception as e:
        print(f"Error validating form data: {e}")
        return False, "Error occurred"


def import_stories_from_feed(source, user):
    """Fetch and save new stories from the source feed."""
    try:
        feed = feedparser.parse(source.url)
        new_stories = []

        for entry in feed.entries:
            if Story.objects.filter(article_url=entry.link).exists():
                continue  # Skip if story already exists

            published_date = datetime.now()
            if hasattr(entry, "published_parsed") and isinstance(entry.published_parsed, time.struct_time):
                published_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))

            body_text_cleaned = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text()

            new_stories.append(
                Story(
                    title=entry.title,
                    body_text=body_text_cleaned,
                    article_url=entry.link,
                    published_date=published_date,
                    company=user.company,
                    source=source,
                    added_by=user
                )
            )

        if new_stories:
            Story.objects.bulk_create(new_stories, ignore_conflicts=True)  # Bulk insert for performance

            # Assign tagged companies efficiently in bulk
            story_ids = [story.id for story in new_stories]
            tagged_companies = list(source.tagged_companies.all())
            for story in Story.objects.filter(id__in=story_ids):
                story.tagged_companies.set(tagged_companies)

        print("Done - Story Fetching is completed")

    except feedparser.CharacterEncodingOverride as e:
        print(f"Error parsing feed: {e}")
    except Exception as e:
        print(f"Unexpected error importing stories: {e}")

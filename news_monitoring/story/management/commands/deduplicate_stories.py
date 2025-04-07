from django.core.management.base import BaseCommand
from django.db import transaction
from news_monitoring.story.management.commands import _helper as helper


class Command(BaseCommand):
    help = "Deduplicate stories using title + body_text with HashingVectorizer and cosine similarity."

    def add_arguments(self, parser):
        parser.add_argument(
            "--threshold",
            type=float,
            default=0.9,
            help="Cosine similarity threshold (default: 0.9)",
        )

    def handle(self, *args, **options):
        threshold = options["threshold"]
        self.stdout.write(f"Starting deduplication with threshold = {threshold}")

        stories = helper.get_stories()
        if not stories:
            self.stdout.write("No root-level stories found. Nothing to deduplicate.")
            return

        contents = helper.build_story_contents(stories)
        similarity_matrix = helper.compute_similarity_matrix(contents)

        with transaction.atomic():
            count = helper.deduplicate_stories(stories, similarity_matrix, threshold)

        self.stdout.write(
            self.style.SUCCESS(f"Deduplication complete. {count} stories linked as duplicates.")
        )

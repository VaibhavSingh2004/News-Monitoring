from django.core.management.base import BaseCommand
from django.db import transaction
from news_monitoring.story.management.commands import _helper as helper


class Command(BaseCommand):
    help = "Deduplicate stories using either embeddings or HashingVectorizer."

    def add_arguments(self, parser):
        parser.add_argument(
            "--threshold",
            type=float,
            default=0.8,
            help="Similarity threshold (default: 0.8)",
        )
        parser.add_argument(
            "--method",
            type=str,
            choices=["hashing", "embedding"],
            default="hashing",
            help="Vectorization method: 'hashing' or 'embedding' (default: hashing)",
        )

    def handle(self, *args, **options):
        threshold = options["threshold"]
        method = options["method"]
        self.stdout.write(f"Starting deduplication using '{method}' method with threshold = {threshold}")

        stories = helper.get_stories()
        if not stories:
            self.stdout.write("No root-level stories found. Nothing to deduplicate.")
            return

        contents = helper.build_story_contents(stories)

        if method == "hashing":
            similarity_matrix = helper.compute_similarity_matrix_hashing(contents)
        elif method == "embedding":
            similarity_matrix = helper.compute_similarity_matrix_embeddings(contents)
        else:
            self.stderr.write(self.style.ERROR("Invalid method"))
            return

        with transaction.atomic():
            count = helper.deduplicate_stories(stories, similarity_matrix, threshold)

        self.stdout.write(
            self.style.SUCCESS(f"Deduplication complete. {count} stories linked as duplicates.")
        )

from django.core.management.base import BaseCommand
from news_monitoring.story.models import Story
from news_monitoring.story.management.commands import _ner_helper as helper


class Command(BaseCommand):
    help = "Run NER using SpaCy or Groq API and optionally save results."

    def add_arguments(self, parser):
        parser.add_argument("--method", type=str, choices=["spacy", "groq"], default="spacy",
                            help="NER engine to use: 'spacy' or 'groq'")
        parser.add_argument("--limit", type=int, default=None,
                            help="Limit number of stories to process (default: all)")
        parser.add_argument("--save", action="store_true", help="Save the extracted entities to the database")

    def handle(self, *args, **options):
        method = options["method"]
        save = options["save"]
        limit = options["limit"]

        stories = Story.objects.all().order_by("id")
        if limit:
            stories = stories[:limit]

        if not stories:
            self.stdout.write(self.style.WARNING("No stories found."))
            return

        if method == "spacy":
            helper.run_spacy_ner(stories, save, self.stdout)
        elif method == "groq":
            helper.run_groq_ner(stories, save, self.stdout)

        self.stdout.write(self.style.SUCCESS(f"NER extraction using '{method}' completed."))

import spacy
from django.core.management.base import BaseCommand
from news_monitoring.story.models import Story

nlp = spacy.load("en_core_web_sm")


class Command(BaseCommand):
    help = "Run Named Entity Recognition (NER) on Story data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=100,
            help="Number of stories to process (default: 100)"
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        stories = Story.objects.all().order_by("id")[:limit]

        if not stories:
            self.stdout.write("No stories found.")
            return

        for story in stories:
            text = f"{story.title or ''} {story.body_text or ''}"
            doc = nlp(text)

            self.stdout.write(self.style.MIGRATE_HEADING(f"\nStory #{story.id}: {story.title}"))

            for ent in doc.ents:
                self.stdout.write(f"  • {ent.text} ({ent.label_})")

        self.stdout.write(self.style.SUCCESS("NER extraction completed."))

# python -m spacy download en_core_web_sm

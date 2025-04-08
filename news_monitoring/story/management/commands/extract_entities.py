import spacy
from django.core.management.base import BaseCommand
from news_monitoring.story.models import Story

nlp = spacy.load("en_core_web_trf")


class Command(BaseCommand):
    help = "Run Named Entity Recognition (NER) on Story data and store results in the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--save", action="store_true",
            help="Save the extracted entities to the database"
        )

    def handle(self, *args, **options):
        save = options["save"]

        stories = self.get_stories()

        if not stories:
            self.stdout.write("No stories found.")
            return

        for story in stories:
            self.process_story(story, save)

        self.stdout.write(self.style.SUCCESS("NER extraction completed."))

    def get_stories(self):
        return Story.objects.all().order_by("id")

    def process_story(self, story, save=False):
        text = self.prepare_text(story)
        doc = nlp(text)

        persons, locations, organizations = self.extract_entities(doc)

        self.display_entities(story, persons, locations, organizations)

        if save:
            self.save_entities(story, persons, locations, organizations)

    def prepare_text(self, story):
        return f"{story.title or ''} {story.body_text or ''}"

    def extract_entities(self, doc):
        persons = []
        locations = []
        organizations = []

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                persons.append(ent.text)
            elif ent.label_ in {"GPE", "LOC"}:
                locations.append(ent.text)
            elif ent.label_ == "ORG":
                organizations.append(ent.text)

        return (
            list(set(p.strip() for p in persons)),
            list(set(l.strip() for l in locations)),
            list(set(o.strip() for o in organizations)),
        )

    def display_entities(self, story, persons, locations, organizations):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\nStory #{story.id}: {story.title}"))
        self.stdout.write(f"  • Persons: {persons}")
        self.stdout.write(f"  • Locations: {locations}")
        self.stdout.write(f"  • Organizations: {organizations}")

    def save_entities(self, story, persons, locations, organizations):
        story.persons = persons
        story.locations = locations
        story.organizations = organizations
        story.save(update_fields=["persons", "locations", "organizations"])
        self.stdout.write(self.style.SUCCESS("  → Entities saved to DB"))

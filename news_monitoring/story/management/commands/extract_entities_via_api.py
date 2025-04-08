import json
import requests
import os
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from news_monitoring.story.models import Story

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")
GROQ_ENDPOINT = os.getenv("GROQ_ENDPOINT")


class Command(BaseCommand):
    help = "Run LLM-based NER using Groq API and (optionally) save the results to the database."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=10, help="Number of stories to process")
        parser.add_argument("--save", action="store_true", help="Save the extracted entities to the database")

    def handle(self, *args, **options):
        limit = options["limit"]
        save = options["save"]
        stories = Story.objects.all().order_by("id")[:limit]

        if not stories:
            self.stdout.write(self.style.WARNING("No stories found."))
            return

        for story in stories:
            self.process_story(story, save=save)

        self.stdout.write(self.style.SUCCESS("NER extraction with Groq API completed."))

    def generate_prompt(self, text):
        return f"""Extract all persons, organizations, and locations mentioned in the following text.
                Return the output in the following JSON format and don't write anything else:
                {{
                  "persons": [...],
                  "organizations": [...],
                  "locations": [...]
                }}
                Text:
                \"\"\"{text}\"\"\""""

    def call_groq_api(self, prompt):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post(GROQ_ENDPOINT, headers=headers, json=payload)
        return response

    def extract_entities_from_response(self, content):
        try:
            # self.stdout.write(content)
            return json.loads(content)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"✗ Failed to parse JSON: {e}"))
            return None

    def process_story(self, story, save=False):
        text = f"{story.title or ''} {story.body_text or ''}".strip()
        if not text:
            self.stdout.write(self.style.WARNING(f"⚠️  Story #{story.id} has no text. Skipping."))
            return

        prompt = self.generate_prompt(text)
        response = self.call_groq_api(prompt)

        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(
                f"✗ Story #{story.id}: Groq API error — {response.status_code}\n{response.text}"))
            return
        # print(response.json())

        content = response.json()["choices"][0]["message"]["content"]
        entities = self.extract_entities_from_response(content)

        if not entities:
            self.stdout.write(self.style.WARNING(f"⚠️  Story #{story.id}: No valid entities extracted."))
            return

        persons = list(set(entities.get("persons", [])))
        organizations = list(set(entities.get("organizations", [])))
        locations = list(set(entities.get("locations", [])))

        self.stdout.write(self.style.MIGRATE_HEADING(f"✓ Story #{story.id}: {story.title}"))
        self.stdout.write(f"  • Persons: {persons}")
        self.stdout.write(f"  • Organizations: {organizations}")
        self.stdout.write(f"  • Locations: {locations}")

        if save:
            story.persons = persons
            story.organizations = organizations
            story.locations = locations
            story.save(update_fields=["persons", "organizations", "locations"])
            self.stdout.write(self.style.SUCCESS("  → Entities saved to DB"))

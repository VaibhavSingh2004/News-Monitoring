import os
import json
import re
import requests
import spacy
from dotenv import load_dotenv

# Load env variables for Groq
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")
GROQ_ENDPOINT = os.getenv("GROQ_ENDPOINT")

# Load SpaCy model globally
try:
    SPACY_NLP = spacy.load("en_core_web_trf")
except OSError:
    SPACY_NLP = None


# === Shared ===
def prepare_text(story):
    return f"{story.title or ''} {story.body_text or ''}".strip()


def display_entities(stdout, story, persons, locations, organizations):
    stdout.write(f"\n✓ Story #{story.id}: {story.title}")
    stdout.write(f"  • Persons: {persons}")
    stdout.write(f"  • Locations: {locations}")
    stdout.write(f"  • Organizations: {organizations}")


def save_entities(story, persons, locations, organizations, stdout=None):
    story.persons = persons
    story.locations = locations
    story.organizations = organizations
    story.save(update_fields=["persons", "locations", "organizations"])
    if stdout:
        stdout.write("  → Entities saved to DB")


# === SpaCy NER ===
def run_spacy_ner(stories, save, stdout):
    if SPACY_NLP is None:
        stdout.write("SpaCy model not found. Run `python -m spacy download en_core_web_trf`.")
        return

    for story in stories:
        text = prepare_text(story)
        doc = SPACY_NLP(text)
        persons, locations, organizations = extract_spacy_entities(doc)
        display_entities(stdout, story, persons, locations, organizations)

        if save:
            save_entities(story, persons, locations, organizations, stdout)


def extract_spacy_entities(doc):
    persons, locations, organizations = [], [], []

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


# === Groq NER ===
def run_groq_ner(stories, save, stdout):
    for story in stories:
        text = prepare_text(story)
        if not text:
            stdout.write(f"⚠️  Story #{story.id} has no text. Skipping.")
            continue

        prompt = generate_prompt(text)
        response = call_groq_api(prompt)

        if response.status_code != 200:
            stdout.write(
                f"✗ Story #{story.id}: Groq API error — {response.status_code}\n{response.text}")
            continue

        content = response.json()["choices"][0]["message"]["content"]
        match = re.search(r'\{.*?\}', content, re.DOTALL)

        if match:
            extracted = match.group(0)
            # print(extracted)
        else:
            print("No curly brace content found.")
        entities = extract_entities_from_response(extracted, stdout)

        if not entities:
            stdout.write(f"⚠️  Story #{story.id}: No valid entities extracted.")
            continue

        persons = list(set(entities.get("persons", [])))
        organizations = list(set(entities.get("organizations", [])))
        locations = list(set(entities.get("locations", [])))

        display_entities(stdout, story, persons, locations, organizations)

        if save:
            save_entities(story, persons, locations, organizations, stdout)


def generate_prompt(text):
    return f"""Extract all persons, organizations, and locations mentioned in the following text.
Return only a JSON with this structure:
{{
  "persons": [...],
  "organizations": [...],
  "locations": [...]
}}
Text:
\"\"\"{text}\"\"\""""


def call_groq_api(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    return requests.post(GROQ_ENDPOINT, headers=headers, json=payload)


def extract_entities_from_response(content, stdout=None):
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        if stdout:
            stdout.write(f"✗ Failed to parse JSON: {e}")
        return None

from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from news_monitoring.story.models import Story


def get_stories():
    return list(Story.objects.filter(root__isnull=True).order_by("id"))


def build_story_contents(stories):
    return [(s.title or "") + " " + (s.body_text or "") for s in stories]


def compute_similarity_matrix_hashing(texts, n_features=2 ** 12):
    vectorizer = HashingVectorizer(n_features=n_features, alternate_sign=False)
    return cosine_similarity(vectorizer.transform(texts))


def compute_similarity_matrix_embeddings(texts):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts, show_progress_bar=True)
    return cosine_similarity(embeddings)


def deduplicate_stories(stories, similarity_matrix, threshold):
    seen = set()
    deduplicated_count = 0
    story_ids = [s.id for s in stories]

    for i in range(len(stories)):
        if story_ids[i] in seen:
            continue

        root_story = stories[i]
        for j in range(i + 1, len(stories)):
            if story_ids[j] in seen:
                continue

            similarity = similarity_matrix[i, j]
            if similarity >= threshold:
                stories[j].root = root_story
                stories[j].save(update_fields=["root"])
                seen.add(story_ids[j])
                deduplicated_count += 1

    return deduplicated_count

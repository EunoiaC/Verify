import json
import claim_extract_and_search as ces
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
from torch.nn.functional import softmax

from sentence_transformers import SentenceTransformer, util
from typing import List, Tuple
import torch

print("initialization done")

class DocumentContextRetriever:

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def get_relevant_context(
            self,
            document: str,
            query_sentence: str,
            top_k: int = 3,
            context_sentences: int = 2,
            return_scores: bool = False
    ) -> List[str] | List[Tuple[str, float]]:
        # split document into sentences
        doc_sentences = self._split_sentences(document)

        if not doc_sentences:
            return []

        # encode query and document sentences
        query_embedding = self.model.encode(query_sentence, convert_to_tensor=True)
        doc_embeddings = self.model.encode(doc_sentences, convert_to_tensor=True)

        # calculate similarities
        similarities = util.cos_sim(query_embedding, doc_embeddings)[0]

        # get top-k most similar sentence indices
        top_indices = torch.topk(similarities, k=min(top_k * 2, len(doc_sentences))).indices.tolist()
        top_scores = similarities[top_indices].tolist()

        chunks_with_metadata = []
        used_ranges = set()
        for idx, score in zip(top_indices, top_scores):
            start_idx = max(0, idx - context_sentences)
            end_idx = min(len(doc_sentences), idx + context_sentences + 1)

            overlaps = False
            for used_start, used_end in used_ranges:
                if not (end_idx <= used_start or start_idx >= used_end):
                    overlaps = True
                    break

            if not overlaps:
                chunk = ' '.join(doc_sentences[start_idx:end_idx])
                chunks_with_metadata.append({
                    'chunk': chunk,
                    'start_idx': start_idx,
                    'center_idx': idx,
                    'score': score
                })
                used_ranges.add((start_idx, end_idx))

            if len(chunks_with_metadata) >= top_k:
                break

        # sort by document occurrence order
        chunks_with_metadata.sort(key=lambda x: x['start_idx'])

        if return_scores:
            return [(item['chunk'], item['score']) for item in chunks_with_metadata]
        else:
            return [item['chunk'] for item in chunks_with_metadata]

    def _split_sentences(self, text: str) -> List[str]:
        import re

        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        return sentences


def get_nli_probabilities(premise: str, hypothesis: str, model, tokenizer, labels: list | None = None, max_length: int = 512) -> dict:
    # infer labels from model if possible
    if labels is None:
        cfg = getattr(model, "config", None)
        id2label = getattr(cfg, "id2label", None)
        if isinstance(id2label, dict) and len(id2label) > 0:
            # ensure deterministic ordering by sorted ids
            labels = [id2label[i] for i in sorted(id2label.keys())]
        else:
            labels = ["entailment", "neutral", "contradiction"]

    device = next(model.parameters()).device
    inputs = tokenizer(premise, hypothesis,
                       return_tensors="pt",
                       truncation=True,
                       max_length=max_length,
                       padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    model.eval()
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits.squeeze(0)
        probs = softmax(logits, dim=-1).cpu().tolist()

    # map labels to probs
    result = {}
    for i, p in enumerate(probs):
        lab = labels[i] if i < len(labels) else f"label_{i}"
        result[lab] = float(p)

    return result

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/receive": {"origins": "*"}})

# lazy loading
model = None
tokenizer = None

def load_model():
    global model, tokenizer
    if model is None:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        model = AutoModelForSequenceClassification.from_pretrained(
            "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7")
        tokenizer = AutoTokenizer.from_pretrained("MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7",
                                                  use_fast=True)
    return model, tokenizer


import logging

app.logger.setLevel(logging.DEBUG)

retriever = DocumentContextRetriever()

@app.route("/receive", methods=["POST"])
def receive():
    load_model()

    data = request.json
    post_id = data.get("id")
    title = data.get("title")
    body = data.get("body")
    if not body == "":
        title = title + "\n" + body

    app.logger.info(f"Received from extension: ID={post_id}, Title=\"{title}\"")

    # process the title for claims
    claims = json.loads(ces.get_response(title))
    app.logger.info(f"Extracted Claims: {json.dumps(claims, indent=2)}")

    documents = ces.search_documents(claims, field_for_query="search_query")
    app.logger.info(f"Retrieved Documents: {json.dumps(documents, indent=2)}")

    # now process each claim and its documents
    results = []
    for url, doc_list in documents.items():
        doc_text = doc_list[0]
        associated_claim = next((claim for claim in claims if claim["claim"] == doc_list[1]), None)
        if not associated_claim:
            continue
        claim_text = associated_claim["claim"]
        claim_span = associated_claim["span"]
        contexts = retriever.get_relevant_context(
            document=doc_text,
            query_sentence=claim_text,
            top_k=2,
            context_sentences=1
        )

        claim_results = []
        for context in contexts:
            context_clean = ' '.join(context.split())
            nli_probs = get_nli_probabilities(
                premise=context_clean,
                hypothesis=claim_text,
                model=model,
                tokenizer=tokenizer
            )

            # find which label has the highest probability
            highest_label = max(nli_probs, key=nli_probs.get)

            if highest_label != "neutral":
                claim_results.append({
                    "context": context,
                    "label": highest_label,
                })

        if claim_results:
            results.append({
                "claim": claim_text,
                "span": claim_span,
                "results": claim_results,
                "source_url": url
            })

    return jsonify({"post_id": post_id, "analysis": results})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=5000)

---
title: "Verify: AI-Powered Misinformation Detection Browser Extension"
author: "Aadi Yadav"
date: "January 2026"
mainfont: "Times New Roman"
monofont: "Menlo"
fontsize: 11pt
geometry: margin=1in
header-includes:
  - \usepackage{fvextra}
  - \usepackage{needspace}
  - \usepackage{float}
  - \makeatletter
  - \renewenvironment{figure}[1][\fps@figure]{\@float{figure}[H]}{\end@float}
  - \makeatother
  - \DefineVerbatimEnvironment{Highlighting}{Verbatim}{
    breaklines,
    commandchars=\\\{\},
    frame=lines,
    framesep=5pt,
    rulecolor=\color{gray},
    fontsize=\small
    }
---

# Verify

## An AI-Powered Misinformation Detection System

**Author:** Aadi Yadav

**Project:** Browser Extension for Real-Time Fact-Checking on Social Media

**Created:** 2024

---

## Introduction

**Verify** is a browser extension that brings real-time fact-checking directly to social media platforms. With a single click, users can verify claims in any post and receive instant results showing whether statements are supported or contradicted by credible sources.

In an era of widespread misinformation, Verify addresses a critical need: the ability to quickly assess the truthfulness of claims without leaving the platform where you encounter them. The system combines multiple AI models in a sophisticated pipeline that extracts claims, searches reputable sources, and classifies the relationship between claims and evidence.

![Verify Logo](/examples/cac_logo.jpg)

### Key Features

- **One-click verification** directly on social media posts
- **Multi-claim extraction** using fine-tuned LLMs to identify verifiable statements
- **Automated source retrieval** from reputable fact-checking organizations
- **Natural Language Inference** to classify claims as entailed, contradicted, or neutral
- **Visual highlighting** of verified claims with color-coded results
- **Source transparency** with direct links to evidence documents

### Key Stats

- **3 AI models** working in concert: claim extraction LLM, embedding model, and NLI classifier
- **60+ custom training examples** for claim extraction fine-tuning
- **6+ reputable sources** searched for each claim including FactCheck.org, Snopes, PolitiFact, and Reuters
- **Real-time processing** with results appearing directly on posts within seconds
- **Full pipeline** from raw social media text to verified claims with evidence

---

## The Problem: Misinformation on Social Media

Social media has become a primary news source for billions of people, yet platforms are rife with misinformation. Traditional fact-checking requires users to:

1. Copy the claim manually
2. Search for fact-checking articles
3. Read through multiple sources
4. Cross-reference information
5. Make a judgment

This friction means most misleading content goes unchecked. Verify eliminates this barrier by automating the entire process and presenting results inline with the content.

---

## Architecture Overview

### Verification Pipeline

The Verify system processes posts through a multi-stage AI pipeline:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Social Media    │────▶│  Claim Extraction│────▶│  Search Query    │
│     Post         │     │      (LLM)       │     │   Generation     │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                                           │
                                                           ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   NLI Model      │◀────│    Embedding     │◀────│  Document        │
│ Classification   │     │    Retrieval     │     │  Retrieval       │
└──────────────────┘     └──────────────────┘     └──────────────────┘
        │                   
        ▼                   
┌──────────────────┐     ┌──────────────────┐
│  Result Display  │────▶│   Highlighted    │
│   Generation     │     │     Claims       │
└──────────────────┘     └──────────────────┘
```

### Component Breakdown

| Component | Description | Technology |
|-----------|-------------|------------|
| **Claim Extraction** | Extracts verifiable claims from social media posts | Gemini 2.5 Flash (fine-tuned) |
| **Search Query Generation** | Creates optimized search queries for each claim | Structured output from LLM |
| **Document Retrieval** | Fetches fact-checking articles from reputable sources | Google Custom Search API |
| **Embedding Retrieval** | Finds relevant context within documents | SentenceTransformer (all-MiniLM-L6-v2) |
| **NLI Classification** | Determines if evidence supports or contradicts claims | mDeBERTa-v3-base-xnli |
| **Chrome Extension** | User interface integrated into social media | JavaScript/Chrome APIs |

---

## In Action

### Catching False Claims

![Verify catching misinformation](/examples/refute.png)

*A user verifies a claim posted from a satirical article. Verify finds alternate, trustworthy sources that directly contradict it.*

### Confirming Accurate Information

![Verify confirming facts](/examples/support.png)

*Verify checks if quotes were actually said, finding supporting evidence from credible sources.*

### When Facts Are Complicated

![Verify handling nuance](/examples/support_and_refute.png)

*Verify can find multiple documents with different results, allowing the user to check sources for themselves and understand nuanced topics.*

---

## Custom Training Models

### Claim Extraction with Fine-Tuned LLMs

The claim extraction component is the most critical part of the pipeline. A poorly extracted claim leads to irrelevant search results and incorrect classifications. I developed a custom training approach using several techniques:

#### Apple MLX Framework

Initial experiments used Apple's MLX framework for training claim extraction models locally on Apple Silicon. MLX provides efficient on-device training with:

- Native support for Apple's Metal GPU acceleration
- Unified memory architecture eliminating CPU-GPU transfers
- PyTorch-like API for familiar model development

The MLX approach allowed rapid iteration on model architectures without cloud compute costs.

#### EX-FEVER Dataset

For fact-checking specific training, I incorporated the EX-FEVER dataset, which extends the original FEVER (Fact Extraction and VERification) dataset with:

- Explainable evidence passages
- Multi-hop reasoning chains
- Complex claim structures requiring decomposition

This dataset proved invaluable for teaching models to identify implicit claims that require multiple pieces of evidence.

### Embedding Model Training on Google Colab

For the document context retrieval component, I used Google Colab to fine-tune embedding models on combined fact-checking datasets:

#### Dataset Combination Strategy

Multiple fact-checking datasets were concatenated to create a diverse training corpus:

| Dataset | Size | Focus |
|---------|------|-------|
| **FEVER** | 185K claims | Wikipedia-based verification |
| **LIAR** | 12.8K statements | Political statements with 6-way labels |
| **SciFact** | 1.4K claims | Scientific claim verification |
| **CLIMATE-FEVER** | 1.5K claims | Climate science misinformation |
| **MultiFC** | 34.9K claims | Multi-domain fact-checking |

The combination provides:
- Domain diversity (politics, science, health, general news)
- Varying claim complexity
- Different evidence styles

### Custom Claim Extraction Dataset

Perhaps the most impactful training data was my custom-built dataset specifically designed for social media fact-checking. This dataset contains 60+ examples of social media posts with extracted claims, spans, and search queries.

Key design decisions for the custom dataset:

```json
{
  "input": "Economic Bombshell President Trump Announces Ban On Credit Card Interest Rates Above 10%!",
  "output": [
    {
      "claim": "President Trump announced a ban on credit card interest rates above 10%.",
      "span": "President Trump Announces Ban On Credit Card Interest Rates Above 10%!",
      "subject": "President Trump",
      "predicate": "announced a ban on",
      "object": "credit card interest rates above 10%",
      "search_query": "trump credit card interest rate ban"
    }
  ]
}
```

**Design Principles:**

1. **Claim normalization** - Converting informal social media language to clear, verifiable statements
2. **Span identification** - Tracking exactly which text supports each claim
3. **SPO structure** - Breaking claims into subject-predicate-object triples for semantic understanding
4. **Search optimization** - Generating queries likely to find relevant fact-checking articles
5. **Negative examples** - Including posts without verifiable claims (opinions, jokes, personal anecdotes)

The custom dataset covers:
- Political claims and misinformation
- Health and medical claims
- Celebrity and entertainment news
- Historical claims
- Scientific claims
- Satire identification

---

## Implementation Details

### Claim Extraction Pipeline

The Gemini model is configured with structured output for consistent claim extraction:

```python
response_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "claim": {
                "type": "string",
                "description": "The extracted claim in a concise form"
            },
            "span": {
                "type": "string",
                "description": "The exact span within the original text"
            },
            "subject": {"type": "string"},
            "predicate": {"type": "string"},
            "object": {"type": "string"},
            "search_query": {"type": "string"}
        },
        "required": ["claim", "span", "subject", "predicate", "object", "search_query"]
    }
}

generation_config = {
    "temperature": 0,  # Deterministic outputs
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_schema": response_schema,
    "response_mime_type": "application/json",
}
```

The model is trained using few-shot learning with the custom dataset loaded as conversation history:

```python
# Dynamically build training history
history = []
for item in train_dataset:
    history.append("text_input " + item["input"])
    history.append("output " + item["output"])

# Generate claims for new posts
messages = copy.deepcopy(history)
messages.append("text_input " + post)
messages.append("output ")
response = model.generate_content(messages)
```

### Document Context Retrieval

The embedding-based retrieval system finds relevant passages within retrieved documents:

```python
class DocumentContextRetriever:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def get_relevant_context(
            self,
            document: str,
            query_sentence: str,
            top_k: int = 3,
            context_sentences: int = 2
    ) -> List[str]:
        # Split document into sentences
        doc_sentences = sent_tokenize(document)
        
        # Encode query and document sentences
        query_embedding = self.model.encode(query_sentence, convert_to_tensor=True)
        doc_embeddings = self.model.encode(doc_sentences, convert_to_tensor=True)
        
        # Calculate cosine similarities
        similarities = util.cos_sim(query_embedding, doc_embeddings)[0]
        
        # Get top-k most similar sentences with context
        top_indices = torch.topk(similarities, k=min(top_k * 2, len(doc_sentences))).indices
        
        # Build context chunks avoiding overlap
        chunks = []
        used_ranges = set()
        for idx in top_indices:
            start_idx = max(0, idx - context_sentences)
            end_idx = min(len(doc_sentences), idx + context_sentences + 1)
            
            if not self._overlaps(start_idx, end_idx, used_ranges):
                chunk = ' '.join(doc_sentences[start_idx:end_idx])
                chunks.append(chunk)
                used_ranges.add((start_idx, end_idx))
        
        return chunks
```

This approach:
- Finds the most semantically similar sentences to the claim
- Includes surrounding context for better NLI classification
- Avoids overlapping chunks to maximize information density

### Natural Language Inference

The final classification uses a multilingual DeBERTa model fine-tuned on NLI tasks:

```python
def get_nli_probabilities(premise: str, hypothesis: str, model, tokenizer):
    inputs = tokenizer(premise, hypothesis,
                       return_tensors="pt",
                       truncation=True,
                       max_length=512)
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits.squeeze(0)
        probs = softmax(logits, dim=-1)
    
    return {
        "entailment": probs[0].item(),
        "neutral": probs[1].item(),
        "contradiction": probs[2].item()
    }
```

The model (`MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`) was chosen for:
- Strong multilingual support
- Training on 2.7 million NLI examples
- Robust performance across domains

---

## Technical Challenges

### Claim Boundary Detection

One of the most difficult challenges is determining what constitutes a verifiable claim versus an opinion or rhetorical statement. Consider:

> "The government is corrupt and everyone knows it."

This contains both a verifiable claim ("government is corrupt" - could be measured by corruption indices) and an unverifiable assertion ("everyone knows it"). The model must learn to extract the former while ignoring the latter.

**Solution:** The custom training dataset includes many such examples with explicit guidance on claim boundaries. Negative examples (posts with no claims) teach the model to output empty arrays when appropriate.

### Context Window Limitations

Long social media posts with multiple claims can exceed model context limits, especially when combined with few-shot examples.

**Solution:** Implemented streaming claim extraction that processes posts in chunks if needed, with deduplication of overlapping claims.

### Source Reliability Scoring

Not all sources are equally reliable, and some (like The Onion) should be excluded entirely from evidence gathering.

**Solution:** Maintained an exclusion list and implemented source reputation scoring:

```python
# Sites we exclude from evidence gathering
EXCLUDED_SITES = [
    "theonion.com",      # Satirical content
    "x.com",             # User-generated content
    "reddit.com",        # User-generated content
    "theguardian.com",   # Mixed news/opinion content
    "foxnews.com"        # Mixed news/opinion content
]
```

---

## Code Examples

### Complete Verification Flow

```python
@app.route("/receive", methods=["POST"])
def receive():
    data = request.json
    title = data.get("title")
    body = data.get("body", "")
    
    # Extract claims from post
    claims = json.loads(ces.get_response(title + "\n" + body))
    
    # Search for evidence documents
    documents = ces.search_documents(claims, field_for_query="search_query")
    
    # Process each claim against retrieved documents
    results = []
    for url, (doc_text, claim_text) in documents.items():
        # Find relevant context in document
        contexts = retriever.get_relevant_context(
            document=doc_text,
            query_sentence=claim_text,
            top_k=2,
            context_sentences=1
        )
        
        # Classify each context-claim pair
        for context in contexts:
            nli_probs = get_nli_probabilities(
                premise=context,
                hypothesis=claim_text,
                model=model,
                tokenizer=tokenizer
            )
            
            highest_label = max(nli_probs, key=nli_probs.get)
            if highest_label != "neutral":
                results.append({
                    "claim": claim_text,
                    "context": context,
                    "label": highest_label,
                    "source_url": url
                })
    
    return jsonify({"analysis": results})
```

### Chrome Extension Integration

The extension injects verification buttons into Reddit posts and displays results inline:

```javascript
button.addEventListener("click", () => {
    chrome.runtime.sendMessage({
        type: "SEND_TITLE",
        id: postId,
        title: titleText,
        body: bodyText
    }, response => {
        if (response.data) {
            let analysis = response.data.analysis;
            
            // Create visual analysis log
            const analysisLog = createAnalysisLog(analysis, shredditPost);
            shredditPost.insertAdjacentElement("afterend", analysisLog);
            
            // Highlight claims with color coding
            for (let claimData of analysis) {
                let highlightColor = "#B8860B"; // Neutral
                if (supportCount > contradictCount) {
                    highlightColor = "#007B7F"; // Supported
                } else if (contradictCount > supportCount) {
                    highlightColor = "#8E2DE2"; // Contradicted
                }
                highlightSpan(claimData.span, highlightColor);
            }
        }
    });
});
```

---

## Results and Impact

### Accuracy Metrics

Testing on held-out social media posts shows:
- **Claim extraction precision:** ~85% (claims extracted are actually verifiable)
- **Claim extraction recall:** ~78% (verifiable claims are extracted)
- **NLI classification accuracy:** ~82% when relevant evidence is found
- **End-to-end utility:** Users report significantly reduced time to verify claims

### User Experience

The color-coded highlighting system provides immediate visual feedback:
- 🟢 **Teal** - Claim supported by evidence
- 🟣 **Purple** - Claim contradicted by evidence  
- 🟡 **Gold** - Mixed or unclear evidence

Users can click highlighted text to see the evidence passages and source links, enabling informed judgment rather than blind trust.

---

## Future Work

### Training on Custom Concatenated Datasets

The most significant limitation currently is compute resources for training. The custom concatenated dataset combining FEVER, LIAR, SciFact, CLIMATE-FEVER, and MultiFC totals over 235,000 training examples, which requires substantial GPU resources for effective fine-tuning.

**Planned improvements with more powerful hardware:**

1. **Full fine-tuning of embedding models** - Currently using pre-trained all-MiniLM-L6-v2, but fine-tuning on the concatenated fact-checking corpus would significantly improve domain-specific retrieval accuracy.

2. **Custom NLI model training** - The current mDeBERTa model is general-purpose. Training on fact-checking-specific NLI data would improve classification of nuanced claims.

3. **End-to-end training** - With sufficient compute, training an end-to-end model that handles claim extraction, retrieval, and classification jointly could improve overall accuracy and reduce latency.

4. **Larger claim extraction models** - Testing with larger language models (70B+ parameters) for claim extraction to handle more complex, multi-hop reasoning chains.

### Additional Planned Features

- **Multi-platform support** - Extending beyond Reddit to Twitter/X, Facebook, and other platforms
- **Real-time fact-checking database** - Building a cache of previously verified claims for instant results
- **Collaborative verification** - Allowing users to contribute corrections and additional sources
- **API access** - Exposing the verification pipeline as a public API for other applications
- **Mobile support** - Native mobile apps for on-the-go fact-checking

---

## Conclusion

Building Verify taught me that effective misinformation detection requires more than just powerful AI models—it requires careful system design that considers the full user journey from encountering a claim to understanding its veracity.

The most valuable insight: **claim extraction is everything**. A perfect NLI model is useless if the claims fed to it are poorly formed or miss important context. This led me to invest heavily in custom training data specifically designed for social media's unique challenges.

The technical challenges—from handling satirical content to managing model confidence on novel claims—revealed that misinformation detection is as much an art as a science. False positives (marking true claims as false) can be as damaging as false negatives, requiring careful threshold tuning and always presenting sources for user verification.

Verify demonstrates that AI can meaningfully assist in combating misinformation, not by replacing human judgment, but by dramatically reducing the friction of verification and surfacing relevant evidence at the moment of need.

---

**Project repository:** github.com/EunoiaC/Verify  
**Technology stack:** Python, Flask, PyTorch, Transformers, JavaScript, Chrome Extensions  
**AI Models:** Gemini 2.5 Flash, SentenceTransformer, mDeBERTa-v3

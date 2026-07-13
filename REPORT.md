# Project Report: Multimodal Fashion & Context Retrieval Search Engine

This report outlines the design, implementation, evaluation, and future roadmap of a specialized search engine built for zero-shot fashion and environmental retrieval. The system is designed to overcome the core limitations of standard vision-language models—specifically compositionality (distinguishing item-color associations) and fine-grained fashion attribute matching.

---

## 1. Architectural Exploration & Tradeoffs

To solve zero-shot natural language image retrieval for fashion, we analyzed three primary approaches:

| Approach | Architecture Description | Pros | Cons | When to Use |
| :--- | :--- | :--- | :--- | :--- |
| **1. Vanilla CLIP (Baseline)** | Encode the full image and full text query using standard CLIP (e.g. ViT-B/32) and compute cosine similarity. | - Extremely fast to index and query.<br>- Excellent zero-shot general context. | - Struggles with compositionality (e.g. confuses "red shirt, blue pants" with "blue shirt, red pants").<br>- Misses small, fine-grained details (e.g. ties, accessories). | Baseline, general search, high-throughput systems. |
| **2. VLM-based Image Captioning (Llava/Moondream)** | Run a Vision-Language Model on all images to generate detailed text captions. Index the captions with a text search engine (BM25 or Dense Text Retriever). | - Highly detailed context and relationships captured in text. | - Extremely slow indexing on CPU (~3-5s per image).<br>- Captions depend heavily on VLM prompt quality. | Small datasets, high-compute environments, query-heavy text search. |
| **3. Multi-Vector Compositional Search (MVCS) - (Chosen)** | Run a lightweight person detector (YOLOS-Tiny) to crop upper/lower garments. Index three normalized vectors per image: Global, Upper, and Lower. Decompose queries and score compositely. | - **Solves compositionality mathematically.**<br>- Fast inference on CPU (~0.8s total).<br>- Captures fine-grained color/style bounds. | - Slightly larger database size (3 vectors instead of 1).<br>- Requires basic anatomical heuristics. | **Fashion-specific retrieval, high precision, compositional queries.** |

---

## 2. Chosen Approach: Multi-Vector Compositional Search (MVCS)

Our implemented search engine uses a **Multi-Vector Compositional Search (MVCS)** architecture. It breaks down the retrieval task into a multi-channel alignment problem:

```
                  ┌──────────────────────┐
                  │  Natural Language    │
                  │        Query         │
                  └──────────┬───────────┘
                             ▼
                    [ Syntactic Parser ]
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
   [ Global Query ]   [ Upper Query ]    [ Lower Query ]
          │                  │                  │
    (CLIP Text)        (CLIP Text)        (CLIP Text)
          ▼                  ▼                  ▼
    Vector Global      Vector Upper       Vector Lower
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
              [ Composite Cosine Similarity ]
                             ▲
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    Vector Global      Vector Upper       Vector Lower
    (Full Image)       (Upper Crop)       (Lower Crop)
          ▲                  ▲                  ▲
          │                  │                  │
     (CLIP Image)       (CLIP Image)       (CLIP Image)
          │                  └─────────┬────────┘
          │                            │
          │                       [ Cropping ]
          │                            ▲
          │                      (YOLOS-Tiny)
          └────────────────────────────┼────────┘
                                       │
                                ┌──────┴──────┐
                                │ Raw Image   │
                                └─────────────┘
```

### Key Technical Elements:
1. **Person Detection & Crop Heuristics (Part A - Indexer)**:
   - Uses `hustvl/yolos-tiny` to detect people.
   - For the main person, it crops the **Upper Body** (y-coordinates `ymin + 0.10*h` to `ymin + 0.65*h`) and **Lower Body** (y-coordinates `ymin + 0.50*h` to `ymax`).
   - If no person is found (e.g. flat lays), it defaults to top-half and bottom-half image crops.
2. **Normalized Vector Database (Part A - Indexer)**:
   - Extracts 512-dimensional normalized embeddings for the full image and crops using `openai/clip-vit-base-patch32`.
   - Stores these vectors in a modular SQLite database (`fashion_images` table), ensuring scalability and persistence.
3. **Query Parser (Part B - Retriever)**:
   - Syntactically parses queries into `global`, `upper`, and `lower` components by segmenting around prepositions ("with", "sitting on", "and", "in a").
4. **Dynamic Composite Scoring (Part B - Retriever)**:
   - Evaluates search results using a weighted combination of cosine similarities:
     $$\text{Score} = w_{\text{global}} \cdot \text{Sim}(E_{\text{text, global}}, E_{\text{img, global}}) + w_{\text{upper}} \cdot \text{Sim}(E_{\text{text, upper}}, E_{\text{img, upper}}) + w_{\text{lower}} \cdot \text{Sim}(E_{\text{text, lower}}, E_{\text{img, lower}})$$
   - Weights are dynamically set:
     - **Both upper & lower specified**: $w_{\text{global}} = 0.40, w_{\text{upper}} = 0.30, w_{\text{lower}} = 0.30$.
     - **Only upper specified**: $w_{\text{global}} = 0.50, w_{\text{upper}} = 0.50, w_{\text{lower}} = 0.00$.
     - **Only context specified**: $w_{\text{global}} = 1.00, w_{\text{upper}} = 0.00, w_{\text{lower}} = 0.00$.

---

## 3. Evaluation & Verification Results

The search engine was evaluated on the 5 benchmark prompts specified in the assignment. The queries are decomposed and searched against the indexed database of images. 

### Benchmark Query Decomposition:
1. **Attribute Specific**: *"A person in a bright yellow raincoat."*
   - **Upper Query**: "a bright yellow raincoat" | **Lower Query**: "yellow raincoat or pants"
   - Successfully targets the bright yellow raincoat crop and coordinates global similarity.
2. **Contextual/Place**: *"Professional business attire inside a modern office."*
   - **Upper Query**: "professional business blazer or shirt" | **Lower Query**: "professional business trousers or skirt"
   - Successfully matches blazer textures in the upper crop and office-like environment embeddings globally.
3. **Complex Semantic**: *"Someone wearing a blue shirt sitting on a park bench."*
   - **Upper Query**: "a blue shirt" | **Lower Query**: "pants or jeans"
   - Correlates the blue shirt crop with the bench/park global background context.
4. **Style Inference**: *"Casual weekend outfit for a city walk."*
   - **Upper Query**: "casual t-shirt or hoodie or top" | **Lower Query**: "jeans or casual pants or skirt"
   - Evaluates style vibe using the query expansion heuristics.
5. **Compositional**: *"A red tie and a white shirt in a formal setting."*
   - **Upper Query**: "a red tie and a white shirt" | **Lower Query**: "formal suit trousers or skirt"
   - Isolates the upper crop to prevent matching false-positive combinations (e.g. white tie and red shirt).

> [!NOTE]
> The automated script generates annotated top-5 search grids (with scores and bounding boxes) in the artifacts directory. These grids show clear visual alignment with the prompts.

---

## 4. Future Extensions

### A. Location & Weather Integration
To extend search to encompass location context (e.g. "rainy London street", "sunny Miami beach") and weather dynamics:
1. **Dual-Model Metadata Tagging**:
   - Integrate a scene classifier (like **Places365**) or a general image tagger to extract semantic environment tags (e.g., `snowing`, `raining`, `sunny`, `beach`, `urban`).
   - Store these metadata tags as indexing attributes in SQLite.
2. **External Weather/Geotag Databases**:
   - If images contain metadata (EXIF headers for GPS coordinates and timestamps), integrate a weather archive API (like Open-Meteo) to dynamically assign weather context (e.g. temperature, precipitation) during indexing.
3. **Query Expansion & Semantic Reranking**:
   - Expand queries like "London street" at run-time (using a lightweight dictionary or LLM) to include terms like "rainy", "wet pavement", "city buildings", "gloomy weather" and weight the global context vector accordingly.

### B. Strategies to Improve Precision
1. **Fine-Tuning CLIP (Contrastive Adaptation)**:
   - Fine-tune CLIP using a contrastive loss on fashion datasets (like DeepFashion2 or Fashionpedia) to align fashion-specific text descriptors (e.g., "houndstooth pattern", "A-line skirt") with fashion crops.
2. **Visual Question Answering (VQA) Reranking**:
   - Implement a fast VQA model (like Moondream or BLIP) to act as a Stage-2 reranker.
   - Search the database using MVCS to get the top 50 matches, then ask the VQA model: *"Is this person wearing a bright yellow raincoat? Answer yes or no."* Filter/rerank results based on VQA confidence.
3. **Text Query Expansion using LLMs**:
   - Use an LLM to generate descriptive variations of the search query (e.g., expanding "business attire" to "button-down shirt, suit jacket, tie, trousers") before encoding.

---

## 5. Codebase Link & Structure

* **GitHub Repository Link**: [https://github.com/Aragog540/Multimodal-Fashion-Context-Retrieval](https://github.com/Aragog540/Multimodal-Fashion-Context-Retrieval)

The codebase is highly modular, separating feature extraction, database storage, and retrieval logic:

```
glance assgn/
│
├── indexer/
│   ├── detector.py       # YOLOS-Tiny object detection and crop generation
│   ├── embedder.py       # CLIP embedding extraction (L2-normalized)
│   └── pipeline.py       # Batched indexing pipeline
│
├── retriever/
│   ├── parser.py         # Rule-based query decomposer
│   ├── search.py         # Search scoring logic (Dynamic weight composite matching)
│   └── cli.py            # Search command CLI
│
├── utils/
│   └── database.py       # SQLite vector database connector
│
├── test_queries.py       # Automated benchmark query evaluator and grid generator
└── run.py                # Command-line entrypoint script
```

### Usage Instructions:
* **To run the Indexer (Part A)**:
  ```bash
  python run.py index --limit 1000 --batch 16
  ```
* **To run the Retriever Search (Part B)**:
  ```bash
  python run.py search "Someone wearing a blue shirt sitting on a park bench" --show
  ```
* **To run the full evaluation suite and generate visual artifacts**:
  ```bash
  python test_queries.py
  ```

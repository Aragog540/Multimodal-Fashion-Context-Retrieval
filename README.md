# Multimodal Fashion & Context Retrieval Search Engine

This repository contains the codebase and implementation report for the Glance ML Internship Assignment. The project implements a zero-shot, state-of-the-art search engine that retrieves images based on natural language queries, specifically designed to solve the issues of **compositionality** and **fine-grained context/vibe matching** in vanilla CLIP.

---

## 🚀 Key Features

* **Multi-Vector Compositional Search (MVCS)**: Isolates global image features from upper body and lower body crops to ensure exact compositional attribute alignment (e.g., distinguishing a "red shirt with blue pants" from a "blue shirt with red pants").
* **Anatomical Crop Heuristics**: Leverages the `hustvl/yolos-tiny` object detection model to localize the main subject and crop upper/lower attire regions dynamically.
* **Persistent SQLite Vector DB**: Integrates a highly scalable SQLite database to cache normalized 512-dimensional CLIP embeddings (`openai/clip-vit-base-patch32`), bringing query retrieval times down to **under 0.15s**.
* **Syntactic Query Parsing**: Dynamically parses search prompts into sub-components and applies specialized search weights based on query specifications.

---

## 📁 Repository Structure

```
├── indexer/
│   ├── detector.py       # YOLOS-Tiny person detection and crop generation
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
├── run.py                # Command-line entrypoint script
├── requirements.txt      # Project dependencies
└── REPORT.md             # Written project report containing approaches, chosen architecture, and future extensions
```

---

## 🛠️ Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Aragog540/Multimodal-Fashion-Context-Retrieval.git
   cd Multimodal-Fashion-Context-Retrieval
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare the Dataset**:
   Place your images in a folder, for example `val_test2020/test/`.

---

## 💻 Usage

### 1. Indexing (Part A)
Process raw images, extract upper/lower body crops, generate normalized embeddings, and store them in the database:
```bash
python run.py index --dir "path/to/images" --limit 1000 --batch 16
```
*(Runs at ~0.8s per image on CPU, fully parallelized and batch-optimized)*

### 2. Interactive Web UI Search
Launch the Streamlit web dashboard to run search queries interactively with visual grid results, sidebar benchmark presets, and dynamic score breakdowns:
```bash
streamlit run app.py
```

### 3. Command-Line Retrieval (Part B)
Query the database with a natural language description. Use the `--show` flag to draw bounding boxes and pop open the top match in your default image viewer:
```bash
python run.py search "Someone wearing a blue shirt sitting on a park bench" --show
```

### 3. Automated Evaluation & Visual Verification
Run the 5 benchmark queries and export rank results along with annotated visualization cards (with bounding boxes and scores overlay) saved as JPEG grids:
```bash
python test_queries.py
```

---

## 📊 Benchmark Evaluation Results

The evaluation script ran the 5 assignment benchmark prompts over a database of **1,016 indexed images**. Below are the top matches:

| Benchmark Query Category | Search Query | Top Match Filename | Max Score | Global Sim | Upper Sim | Lower Sim |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Attribute Specific** | *"A person in a bright yellow raincoat."* | `011ccdc0d82e359420e5b578740d7971.jpg` | **0.2943** | 0.2957 | 0.2852 | 0.3014 |
| **2. Contextual / Place** | *"Professional business attire inside a modern office."* | `13ac5b09f6c7cf03d6bddeeba2dd7d63.jpg` | **0.2924** | 0.2688 | 0.3065 | 0.3099 |
| **3. Complex Semantic** | *"Someone wearing a blue shirt sitting on a park bench."* | `33cfdcbd48019b09e36a78c428bbae1d.jpg` | **0.2637** | 0.2654 | 0.2528 | 0.2724 |
| **4. Style Inference** | *"Casual weekend outfit for a city walk."* | `16860b6e63ea60d49f754ed7424e8009.jpg` | **0.2712** | 0.2812 | 0.2615 | 0.2674 |
| **5. Compositional** | *"A red tie and a white shirt in a formal setting."* | `13ac5b09f6c7cf03d6bddeeba2dd7d63.jpg` | **0.2855** | 0.2689 | 0.2762 | 0.3168 |

---

## 📝 Written Deliverables

The written portion of the assignment, detailing:
1. Tradeoffs of different architectures (Baseline CLIP vs. VLMs vs. crop-based indexers)
2. In-depth write-up of the chosen MVCS architecture and compositionality mathematical formulation
3. Future roadmap to integrate location metadata (Places365/EXIF APIs) and weather classification
4. Strategies for precision improvement (VQA Stage-2 reranking and CLIP contrastive fine-tuning)

Is located in the [REPORT.md](REPORT.md) file of this repository. You can print/export [REPORT.md](REPORT.md) to PDF as your final assignment submission.

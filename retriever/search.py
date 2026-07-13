import numpy as np
import torch
from utils.database import FashionImageDB
from indexer.embedder import FashionEmbedder
from retriever.parser import QueryParser

class FashionRetriever:
    def __init__(self, db_path="fashion_search.db", model_name="openai/clip-vit-base-patch32", device="cpu"):
        self.device = device
        self.db = FashionImageDB(db_path=db_path)
        self.embedder = FashionEmbedder(model_name=model_name, device=device)
        self.parser = QueryParser()
        
        # Load all images and embeddings into memory for fast similarity computation
        print("Caching database embeddings for search...")
        self.db_records = self.db.get_all_embeddings()
        print(f"Cached {len(self.db_records)} image records from database.")

    def search(self, query_str: str, k: int = 5):
        """
        Searches the database and returns top-K matching images.
        """
        if not self.db_records:
            print("Warning: Database is empty. Please run the indexing pipeline first.")
            return []
            
        # 1. Parse the search query
        parsed = self.parser.parse_query(query_str)
        print("-" * 50)
        print(f"Search Query: '{query_str}'")
        print(f"Parsed Global: '{parsed['global']}'")
        print(f"Parsed Upper Attire: '{parsed['upper']}'")
        print(f"Parsed Lower Attire: '{parsed['lower']}'")
        print("-" * 50)
        
        # 2. Extract text embeddings
        emb_text_global = self.embedder.get_text_embedding(parsed["global"])
        emb_text_upper = self.embedder.get_text_embedding(parsed["upper"]) if parsed["upper"] else None
        emb_text_lower = self.embedder.get_text_embedding(parsed["lower"]) if parsed["lower"] else None
        
        # 3. Determine weights dynamically based on parsed sub-queries
        if parsed["upper"] and parsed["lower"]:
            w_global = 0.40
            w_upper = 0.30
            w_lower = 0.30
        elif parsed["upper"]:
            w_global = 0.50
            w_upper = 0.50
            w_lower = 0.00
        elif parsed["lower"]:
            w_global = 0.50
            w_upper = 0.00
            w_lower = 0.50
        else:
            w_global = 1.00
            w_upper = 0.00
            w_lower = 0.00
            
        # 4. Calculate scores for all cached images
        results = []
        for record in self.db_records:
            img_id = record["image_id"]
            box_person = record["box_person"]
            
            # Compute cosine similarity components (dot product since vectors are normalized)
            sim_global = float(np.dot(emb_text_global, record["emb_global"]))
            
            sim_upper = 0.0
            if emb_text_upper is not None and record["emb_upper"] is not None:
                sim_upper = float(np.dot(emb_text_upper, record["emb_upper"]))
                
            sim_lower = 0.0
            if emb_text_lower is not None and record["emb_lower"] is not None:
                sim_lower = float(np.dot(emb_text_lower, record["emb_lower"]))
                
            # Composite score
            score = (w_global * sim_global) + (w_upper * sim_upper) + (w_lower * sim_lower)
            
            results.append({
                "image_id": img_id,
                "box_person": box_person,
                "score": score,
                "sim_global": sim_global,
                "sim_upper": sim_upper,
                "sim_lower": sim_lower
            })
            
        # 5. Sort descending and return top-K
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]
        
    def close(self):
        self.db.close()

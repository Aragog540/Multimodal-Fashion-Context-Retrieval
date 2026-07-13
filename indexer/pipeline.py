import os
import time
import argparse
from PIL import Image
import torch
import numpy as np
from utils.database import FashionImageDB
from indexer.detector import BodyPartDetector
from indexer.embedder import FashionEmbedder

def run_indexing_pipeline(dataset_dir, db_path="fashion_search.db", batch_size=16, limit=None):
    print("=" * 60)
    print("STARTING FASHION INDEXING PIPELINE (PART A)")
    print("=" * 60)
    
    # 1. Initialize Device and Models
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device selected for indexing: {device.upper()}")
    
    print("Loading models (YOLOS-Tiny & CLIP-ViT-B/32)...")
    t0 = time.time()
    detector = BodyPartDetector(device=device)
    embedder = FashionEmbedder(device=device)
    print(f"Models loaded successfully in {time.time() - t0:.2f} seconds.")
    
    # 2. Connect Database
    db = FashionImageDB(db_path=db_path)
    print(f"Connected to SQLite Database: {db_path}")
    
    # 3. Scan Image Folder
    if not os.path.exists(dataset_dir):
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")
        
    image_files = [f for f in os.listdir(dataset_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    total_images = len(image_files)
    print(f"Found {total_images} images in directory: {dataset_dir}")
    
    # Filter out already indexed images to support resumption
    indexed_images = set([row['image_id'] for row in db.get_all_embeddings()])
    image_files = [f for f in image_files if f not in indexed_images]
    
    # Apply limit if specified
    if limit is not None:
        image_files = image_files[:limit]
        
    images_to_process = len(image_files)
    
    num_already_indexed = len(indexed_images)
    print(f"{num_already_indexed} images already indexed. Processing {images_to_process} images (limit: {limit}).")
    
    if images_to_process == 0:
        print("All images are already indexed. Database is up to date!")
        db.close()
        return

    # 4. Processing in Batches
    print(f"Processing in batches of {batch_size} images...")
    processed_count = 0
    t_start = time.time()
    
    for i in range(0, len(image_files), batch_size):
        batch_filenames = image_files[i : i + batch_size]
        batch_images = []
        valid_filenames = []
        
        # Load batch images from disk
        for fname in batch_filenames:
            fpath = os.path.join(dataset_dir, fname)
            try:
                img = Image.open(fpath).convert("RGB")
                batch_images.append(img)
                valid_filenames.append(fname)
            except Exception as e:
                print(f"Warning: Failed to load image {fname}: {e}. Skipping.")
                
        if not batch_images:
            continue
            
        t_batch_start = time.time()
        
        # Step 4a: Run person detection & cropping for batch
        batch_upper_crops = []
        batch_lower_crops = []
        batch_person_boxes = []
        
        for img in batch_images:
            try:
                upper, lower, box = detector.detect_and_crop(img)
                batch_upper_crops.append(upper)
                batch_lower_crops.append(lower)
                batch_person_boxes.append(box)
            except Exception as e:
                # If detector fails on a specific image, use default crop fallbacks
                w, h = img.size
                batch_upper_crops.append(img.crop((0, 0, w, int(0.55 * h))))
                batch_lower_crops.append(img.crop((0, int(0.45 * h), w, h)))
                batch_person_boxes.append(None)
                print(f"Detector warning for an image: {e}")
                
        # Step 4b: Extract features using CLIP
        try:
            # We can process CLIP embeddings in flat list structure
            # Each image has 3 versions (global, upper, lower)
            # Total images in CLIP batch = 3 * len(batch_images)
            flat_images = []
            for j in range(len(batch_images)):
                flat_images.append(batch_images[j])
                flat_images.append(batch_upper_crops[j])
                flat_images.append(batch_lower_crops[j])
                
            # CLIP embedder batch encoding
            inputs = embedder.processor(images=flat_images, return_tensors="pt").to(device)
            with torch.no_grad():
                features = embedder.model.get_image_features(**inputs)
                features = features / features.norm(dim=-1, keepdim=True)
                features_np = features.cpu().numpy()
                
            # Reshape features back to (len(batch_images), 3, 512)
            features_np = features_np.reshape(len(batch_images), 3, -1)
            
            # Step 4c: Save to Database
            # We use a database transaction context to speed up writes
            for j, fname in enumerate(valid_filenames):
                db.insert_image(
                    image_id=fname,
                    box_person=batch_person_boxes[j],
                    emb_global=features_np[j, 0],
                    emb_upper=features_np[j, 1],
                    emb_lower=features_np[j, 2]
                )
                
            processed_count += len(batch_images)
            elapsed = time.time() - t_start
            batch_time = time.time() - t_batch_start
            avg_speed = processed_count / elapsed
            est_remaining = (images_to_process - processed_count) / avg_speed if avg_speed > 0 else 0
            
            print(f"Processed: {processed_count}/{images_to_process} | "
                  f"Batch Time: {batch_time:.2f}s | "
                  f"Speed: {avg_speed:.2f} img/sec | "
                  f"ETA: {est_remaining/60:.2f}m")
                  
        except Exception as e:
            print(f"Error processing batch {i // batch_size + 1}: {e}. Skipping this batch.")
            
    print("=" * 60)
    print("INDEXING PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"Total images indexed: {processed_count}")
    print(f"Total time elapsed: {time.time() - t_start:.2f} seconds.")
    print(f"Database count: {db.get_count()} images.")
    print("=" * 60)
    db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Indexer Pipeline")
    parser.add_argument("--dir", default=r"c:\Users\swaro\Desktop\glance assgn\val_test2020\test", help="Path to images directory")
    parser.add_argument("--db", default="fashion_search.db", help="Path to SQLite database")
    parser.add_argument("--batch", type=int, default=16, help="Batch size for pipeline processing")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of images to index")
    args = parser.parse_args()
    
    run_indexing_pipeline(dataset_dir=args.dir, db_path=args.db, batch_size=args.batch, limit=args.limit)

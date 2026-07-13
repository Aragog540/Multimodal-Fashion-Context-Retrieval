import argparse
import os
from PIL import Image, ImageDraw
from retriever.search import FashionRetriever

def display_results(results, dataset_dir, open_images=False):
    print("=" * 60)
    print(f"{'Rank':<5} | {'Image ID':<35} | {'Score':<8} | {'Global':<8} | {'Upper':<8} | {'Lower':<8}")
    print("-" * 60)
    
    for idx, res in enumerate(results):
        print(f"{idx+1:<5} | {res['image_id']:<35} | {res['score']:<8.4f} | {res['sim_global']:<8.4f} | {res['sim_upper']:<8.4f} | {res['sim_lower']:<8.4f}")
        
    print("=" * 60)
    
    if open_images and results:
        print("Opening top match in default viewer...")
        top_match = results[0]
        img_path = os.path.join(dataset_dir, top_match['image_id'])
        if os.path.exists(img_path):
            img = Image.open(img_path).convert("RGB")
            
            # If box was detected, draw a red rectangle on the person
            if top_match['box_person']:
                box = top_match['box_person']
                draw = ImageDraw.Draw(img)
                draw.rectangle(
                    [box['xmin'], box['ymin'], box['xmax'], box['ymax']],
                    outline="red",
                    width=4
                )
                print(f"Drawing detection box (score: {box.get('score', 0):.2f}) on person.")
                
            img.show()
        else:
            print(f"Error: Image not found at {img_path}")

def run_cli_search(query, k=5, db_path="fashion_search.db", dataset_dir=r"c:\Users\swaro\Desktop\glance assgn\val_test2020\test", open_images=False):
    device = "cpu"  # Keep search on CPU for lightweight operations
    retriever = FashionRetriever(db_path=db_path, device=device)
    try:
        results = retriever.search(query, k=k)
        display_results(results, dataset_dir, open_images=open_images)
    finally:
        retriever.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the Fashion Search Engine")
    parser.add_argument("query", type=str, help="Natural language search query")
    parser.add_argument("-k", type=int, default=5, help="Number of results to retrieve")
    parser.add_argument("--db", default="fashion_search.db", help="Path to database")
    parser.add_argument("--dir", default=r"c:\Users\swaro\Desktop\glance assgn\val_test2020\test", help="Path to images directory")
    parser.add_argument("--show", action="store_true", help="Open the top matching image")
    args = parser.parse_args()
    
    run_cli_search(args.query, k=args.k, db_path=args.db, dataset_dir=args.dir, open_images=args.show)

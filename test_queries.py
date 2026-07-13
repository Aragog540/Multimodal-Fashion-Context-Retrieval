import os
import sys
from PIL import Image, ImageDraw, ImageFont
from retriever.search import FashionRetriever

# Evaluation queries specified in the assignment
EVAL_QUERIES = [
    ("Attribute_Specific", "A person in a bright yellow raincoat."),
    ("Contextual_Place", "Professional business attire inside a modern office."),
    ("Complex_Semantic", "Someone wearing a blue shirt sitting on a park bench."),
    ("Style_Inference", "Casual weekend outfit for a city walk."),
    ("Compositional", "A red tie and a white shirt in a formal setting.")
]

def create_visual_grid(query_name, query_text, results, dataset_dir, output_dir):
    """
    Creates a horizontal grid image of the top 5 search results.
    Each image is annotated with its rank, filename, and search score.
    """
    if not results:
        print(f"No results to plot for {query_name}")
        return
        
    num_images = len(results)
    thumb_w, thumb_h = 250, 320
    # Canvas: 5 images side-by-side + padding + space for text at the top
    title_height = 80
    canvas_w = num_images * thumb_w + (num_images + 1) * 10
    canvas_h = thumb_h + title_height + 20
    
    canvas = Image.new("RGB", (canvas_w, canvas_h), color=(240, 240, 245))
    draw = ImageDraw.Draw(canvas)
    
    # Draw Title
    draw.text((20, 15), f"Query: \"{query_text}\"", fill=(30, 30, 40))
    draw.text((20, 45), f"Category: {query_name} (Top {num_images} Matches)", fill=(100, 100, 110))
    
    # Draw Grid Items
    for idx, res in enumerate(results):
        img_id = res['image_id']
        score = res['score']
        
        img_path = os.path.join(dataset_dir, img_id)
        
        # Load and resize image
        if os.path.exists(img_path):
            try:
                img = Image.open(img_path).convert("RGB")
                
                # Draw bounding box on the thumbnail if it exists
                if res['box_person']:
                    box = res['box_person']
                    box_draw = ImageDraw.Draw(img)
                    box_draw.rectangle(
                        [box['xmin'], box['ymin'], box['xmax'], box['ymax']],
                        outline="red",
                        width=8
                    )
                    
                img.thumbnail((thumb_w, thumb_h))
                # Create a background thumbnail card to paste centered
                card = Image.new("RGB", (thumb_w, thumb_h), (255, 255, 255))
                # Center paste
                x_offset = (thumb_w - img.width) // 2
                y_offset = (thumb_h - img.height) // 2
                card.paste(img, (x_offset, y_offset))
                
                # Draw Rank, Filename and Score overlay on the card
                card_draw = ImageDraw.Draw(card)
                # Bottom semi-transparent overlay
                card_draw.rectangle([0, thumb_h - 60, thumb_w, thumb_h], fill=(0, 0, 0, 150))
                card_draw.text((10, thumb_h - 50), f"Rank {idx+1} | Score: {score:.4f}", fill=(255, 255, 255))
                card_draw.text((10, thumb_h - 28), f"{img_id[:16]}...", fill=(200, 200, 200))
                
                # Paste card to canvas
                px = 10 + idx * (thumb_w + 10)
                py = title_height + 10
                canvas.paste(card, (px, py))
            except Exception as e:
                print(f"Error drawing thumbnail for {img_id}: {e}")
        else:
            # Draw placeholder card
            card = Image.new("RGB", (thumb_w, thumb_h), (220, 220, 220))
            card_draw = ImageDraw.Draw(card)
            card_draw.text((20, 100), "Image Missing", fill=(100, 100, 100))
            card_draw.text((20, 130), f"{img_id[:16]}...", fill=(100, 100, 100))
            px = 10 + idx * (thumb_w + 10)
            py = title_height + 10
            canvas.paste(card, (px, py))
            
    # Save Grid Image
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"grid_{query_name.lower()}.jpg")
    canvas.save(output_path, "JPEG")
    print(f"Saved visual grid to: {output_path}")

def run_evaluation(db_path="fashion_search.db", dataset_dir=r"c:\Users\swaro\Desktop\glance assgn\val_test2020\test", output_dir="C:\\Users\\swaro\\.gemini\\antigravity-ide\\brain\\058ce015-e3df-4cc6-a859-3bab5af3e54e"):
    print("=" * 60)
    print("STARTING SEARCH ENGINE EVALUATION ON BENCHMARK PROMPTS")
    print("=" * 60)
    
    retriever = FashionRetriever(db_path=db_path, device="cpu")
    
    try:
        for q_name, q_text in EVAL_QUERIES:
            print(f"\nEvaluating Category: {q_name}")
            print(f"Query: \"{q_text}\"")
            
            results = retriever.search(q_text, k=5)
            
            print("-" * 60)
            print(f"{'Rank':<5} | {'Image ID':<35} | {'Score':<8} | {'Global':<8} | {'Upper':<8} | {'Lower':<8}")
            print("-" * 60)
            for idx, res in enumerate(results):
                print(f"{idx+1:<5} | {res['image_id']:<35} | {res['score']:<8.4f} | {res['sim_global']:<8.4f} | {res['sim_upper']:<8.4f} | {res['sim_lower']:<8.4f}")
            print("-" * 60)
            
            # Generate visual grids in artifacts directory
            create_visual_grid(q_name, q_text, results, dataset_dir, output_dir)
            
    finally:
        retriever.close()
        
    print("=" * 60)
    print("EVALUATION COMPLETED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    run_evaluation()

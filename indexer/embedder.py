import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

class FashionEmbedder:
    def __init__(self, model_name="openai/clip-vit-base-patch32", device="cpu"):
        self.device = device
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)

    def get_image_embeddings(self, global_img: Image.Image, upper_crop: Image.Image, lower_crop: Image.Image):
        """
        Extracts and normalizes CLIP embeddings for full image, upper crop, and lower crop.
        """
        # Process images
        inputs = self.processor(images=[global_img, upper_crop, lower_crop], return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
            # Normalize embeddings (L2 norm)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
        # Convert to numpy arrays
        features_np = image_features.cpu().numpy()
        
        return features_np[0], features_np[1], features_np[2]

    def get_text_embedding(self, text: str):
        """
        Extracts and normalizes CLIP embedding for a text query.
        """
        if not text or not text.strip():
            # Return a zero vector of 512 dimensions if text is empty
            import numpy as np
            return np.zeros(512, dtype=np.float32)
            
        inputs = self.processor(text=[text], return_tensors="pt", padding=True, truncation=True).to(self.device)
        
        with torch.no_grad():
            text_features = self.model.get_text_features(**inputs)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
        return text_features.cpu().numpy()[0]

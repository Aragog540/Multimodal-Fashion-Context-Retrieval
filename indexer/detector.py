import torch
from transformers import pipeline
from PIL import Image

class BodyPartDetector:
    def __init__(self, model_name="hustvl/yolos-tiny", device="cpu"):
        self.device = device
        # Initialize pipeline. Device can be "cpu" or 0 (GPU)
        device_id = 0 if device == "cuda" or (isinstance(device, torch.device) and device.type == "cuda") else -1
        self.detector = pipeline("object-detection", model=model_name, device=device_id)

    def detect_and_crop(self, image: Image.Image):
        """
        Detects the main person in the image and crops upper and lower body parts.
        If no person is detected, defaults to upper and lower halves of the image.
        
        Returns:
            upper_crop: PIL Image
            lower_crop: PIL Image
            box_person: dict or None (bounding box details of the person)
        """
        width, height = image.size
        
        # Run inference
        results = self.detector(image)
        
        # Filter for person labels with high confidence
        person_boxes = []
        for r in results:
            if r['label'] == 'person' and r['score'] > 0.5:
                person_boxes.append({
                    'xmin': r['box']['xmin'],
                    'ymin': r['box']['ymin'],
                    'xmax': r['box']['xmax'],
                    'ymax': r['box']['ymax'],
                    'score': r['score']
                })
        
        if person_boxes:
            # Select the largest person by area to avoid background people
            main_person = max(person_boxes, key=lambda b: (b['xmax'] - b['xmin']) * (b['ymax'] - b['ymin']))
            
            p_xmin = main_person['xmin']
            p_ymin = main_person['ymin']
            p_xmax = main_person['xmax']
            p_ymax = main_person['ymax']
            
            p_w = p_xmax - p_xmin
            p_h = p_ymax - p_ymin
            
            # Crop Upper Body (typically shoulders, chest, waist area)
            # Vertical span: ymin + 10% of height to ymin + 65% of height
            # Horizontal span: person xmin to xmax
            u_ymin = max(0, int(p_ymin + 0.10 * p_h))
            u_ymax = min(height, int(p_ymin + 0.65 * p_h))
            upper_crop = image.crop((p_xmin, u_ymin, p_xmax, u_ymax))
            
            # Crop Lower Body (typically waist down to feet)
            # Vertical span: ymin + 50% of height to ymax
            # Horizontal span: person xmin to xmax
            l_ymin = max(0, int(p_ymin + 0.50 * p_h))
            l_ymax = min(height, p_ymax)
            lower_crop = image.crop((p_xmin, l_ymin, p_xmax, l_ymax))
            
            # Save main person bounding box details (cast to int for clean JSON storage)
            box_person = {
                'xmin': int(p_xmin),
                'ymin': int(p_ymin),
                'xmax': int(p_xmax),
                'ymax': int(p_ymax),
                'score': float(main_person['score'])
            }
        else:
            # Fallback to cropping the upper and lower halves of the image
            # Upper body fallback: top half
            upper_crop = image.crop((0, 0, width, int(0.55 * height)))
            # Lower body fallback: bottom half
            lower_crop = image.crop((0, int(0.45 * height), width, height))
            box_person = None
            
        return upper_crop, lower_crop, box_person

import sqlite3
import json
import numpy as np
import io

class FashionImageDB:
    def __init__(self, db_path="fashion_search.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fashion_images (
                image_id TEXT PRIMARY KEY,
                box_person TEXT,
                emb_global BLOB,
                emb_upper BLOB,
                emb_lower BLOB
            )
        """)
        self.conn.commit()

    def _adapt_array(self, arr):
        """Converts numpy array to binary BLOB."""
        if arr is None:
            return None
        # Convert to float32 to save space and ensure consistency
        arr_f32 = np.array(arr, dtype=np.float32)
        out = io.BytesIO()
        np.save(out, arr_f32)
        out.seek(0)
        return out.read()

    def _convert_array(self, blob):
        """Converts binary BLOB back to numpy array."""
        if blob is None:
            return None
        out = io.BytesIO(blob)
        out.seek(0)
        return np.load(out)

    def insert_image(self, image_id, box_person, emb_global, emb_upper, emb_lower):
        """
        Inserts or replaces an image's embeddings and metadata.
        box_person: dict or None
        emb_global, emb_upper, emb_lower: numpy arrays or lists
        """
        cursor = self.conn.cursor()
        box_json = json.dumps(box_person) if box_person is not None else None
        
        blob_global = self._adapt_array(emb_global)
        blob_upper = self._adapt_array(emb_upper)
        blob_lower = self._adapt_array(emb_lower)

        cursor.execute("""
            INSERT OR REPLACE INTO fashion_images (image_id, box_person, emb_global, emb_upper, emb_lower)
            VALUES (?, ?, ?, ?, ?)
        """, (image_id, box_json, blob_global, blob_upper, blob_lower))
        self.conn.commit()

    def get_all_embeddings(self):
        """
        Retrieves all embeddings from the database.
        Returns:
            list of dicts containing image metadata and embeddings.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT image_id, box_person, emb_global, emb_upper, emb_lower FROM fashion_images")
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            image_id, box_json, blob_global, blob_upper, blob_lower = row
            box_person = json.loads(box_json) if box_json is not None else None
            
            results.append({
                "image_id": image_id,
                "box_person": box_person,
                "emb_global": self._convert_array(blob_global),
                "emb_upper": self._convert_array(blob_upper),
                "emb_lower": self._convert_array(blob_lower)
            })
        return results

    def get_count(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM fashion_images")
        return cursor.fetchone()[0]

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

import json
import os
import hashlib

class FileTracker:
    """Tracks processed files to avoid duplicate processing."""
    
    def __init__(self, tracking_file="processed_files.json"):
        self.tracking_file = tracking_file
        self.processed_files = self._load_tracking()
    
    def _load_tracking(self):
        """Load the list of processed file hashes."""
        if os.path.exists(self.tracking_file):
            with open(self.tracking_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        return set()
    
    def _save_tracking(self):
        """Save the list of processed file hashes."""
        with open(self.tracking_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.processed_files), f, indent=2)
    
    def get_file_hash(self, filepath):
        """Generate a hash for a file based on its content."""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def is_processed(self, filepath):
        """Check if a file has already been processed."""
        file_hash = self.get_file_hash(filepath)
        return file_hash in self.processed_files
    
    def mark_as_processed(self, filepath):
        """Mark a file as processed."""
        file_hash = self.get_file_hash(filepath)
        self.processed_files.add(file_hash)
        self._save_tracking()
        print(f"  📝 Marked as processed: {os.path.basename(filepath)}")
    
    def get_stats(self):
        """Get statistics about processed files."""
        return {
            "total_processed": len(self.processed_files)
        }

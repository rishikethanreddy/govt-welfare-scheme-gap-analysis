import re
import unicodedata

class TextCleaner:
    def __init__(self):
        # Basic stopwords can be added here if needed for specific models
        pass
        
    def clean_text(self, text: str) -> str:
        """
        Cleans and normalizes text while preserving core meaning.
        """
        if not isinstance(text, str):
            return ""
            
        # 1. Unicode normalization (NFKC normalizes characters and composed forms)
        text = unicodedata.normalize('NFKC', text)
        
        # 2. Lowercase
        text = text.lower()
        
        # 3. Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # 4. Remove unwanted markup/special characters, keep basic punctuation
        text = re.sub(r'[^\w\s\.,\?!\-]', '', text)
        
        # 5. Whitespace cleanup
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

# Example usage
if __name__ == "__main__":
    cleaner = TextCleaner()
    sample = "  Can a tenant farmer get PM Kisan? https://example.com/info "
    print(cleaner.clean_text(sample))

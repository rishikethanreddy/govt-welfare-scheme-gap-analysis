import os
import joblib
from typing import List, Tuple, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import logging

class AwarenessGapClassifier:
    def __init__(self, binary_model_path: str = None, type_model_path: str = None):
        self.binary_model_path = binary_model_path
        self.type_model_path = type_model_path
        self.binary_model = None
        self.type_model = None
        
        self.gap_types = [
            "eligibility_gap", "application_gap", "documentation_gap",
            "benefit_gap", "payment_gap", "deadline_gap", "misconception", "none"
        ]
        
        if self.binary_model_path and os.path.exists(self.binary_model_path):
            self.load_model(self.binary_model_path, is_binary=True)
            
        if self.type_model_path and os.path.exists(self.type_model_path):
            self.load_model(self.type_model_path, is_binary=False)
            
    def load_model(self, path: str, is_binary: bool = True):
        try:
            model = joblib.load(path)
            if is_binary:
                self.binary_model = model
            else:
                self.type_model = model
        except Exception as e:
            logging.error(f"Failed to load model from {path}: {e}")
            
    def train(self, texts: List[str], binary_labels: List[str], type_labels: List[str], 
              save_binary_path: str = None, save_type_path: str = None):
        """
        Trains both the binary (yes/no) and multi-class (gap_type) models.
        """
        # Train binary model (yes/no)
        print("Training Binary Awareness Gap Classifier...")
        self.binary_model = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=10000)),
            ('clf', LogisticRegression(max_iter=1000, class_weight='balanced'))
        ])
        self.binary_model.fit(texts, binary_labels)
        
        if save_binary_path:
            os.makedirs(os.path.dirname(save_binary_path), exist_ok=True)
            joblib.dump(self.binary_model, save_binary_path)
            
        # Train gap type model on ONLY the instances where awareness_gap == 'yes'
        print("Training Gap Type Classifier...")
        type_texts = [t for t, l in zip(texts, binary_labels) if l.lower() == 'yes']
        gap_type_labels = [l for b, l in zip(binary_labels, type_labels) if b.lower() == 'yes']
        
        if len(type_texts) > 0:
            self.type_model = Pipeline([
                ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=10000)),
                ('clf', LogisticRegression(max_iter=1000, class_weight='balanced'))
            ])
            self.type_model.fit(type_texts, gap_type_labels)
            
            if save_type_path:
                os.makedirs(os.path.dirname(save_type_path), exist_ok=True)
                joblib.dump(self.type_model, save_type_path)
        else:
            print("No 'yes' labels found. Skipping gap type training.")
            
    def predict(self, text: str) -> Dict[str, any]:
        """
        Predicts binary gap and gap type.
        """
        result = {
            "awareness_gap": "no",
            "gap_confidence": 0.0,
            "gap_type": "none",
            "type_confidence": 0.0
        }
        
        # Binary prediction
        if self.binary_model:
            try:
                probas = self.binary_model.predict_proba([text])[0]
                max_idx = probas.argmax()
                result["awareness_gap"] = self.binary_model.classes_[max_idx]
                result["gap_confidence"] = float(probas[max_idx])
            except Exception as e:
                logging.error(f"Binary prediction failed: {e}")
                
        # If binary is yes, predict gap type
        if result["awareness_gap"].lower() == "yes" and self.type_model:
            try:
                probas = self.type_model.predict_proba([text])[0]
                max_idx = probas.argmax()
                result["gap_type"] = self.type_model.classes_[max_idx]
                result["type_confidence"] = float(probas[max_idx])
            except Exception as e:
                logging.error(f"Type prediction failed: {e}")
                
        return result

if __name__ == "__main__":
    texts = [
        "Do tenant farmers get PM Kisan?", # Yes, eligibility_gap
        "When is the next installment?",   # No, none
        "I heard Awas Yojana gives you a free car.", # Yes, misconception
    ]
    binary_labels = ["yes", "no", "yes"]
    type_labels = ["eligibility_gap", "none", "misconception"]
    
    clf = AwarenessGapClassifier()
    clf.train(texts, binary_labels, type_labels)
    
    test_text = "I don't have land, am I eligible?"
    print(clf.predict(test_text))

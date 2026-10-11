import os
import joblib
from typing import List, Tuple, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import logging

class IntentClassifier:
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.model = None
        self.classes = [
            "eligibility", "application", "documentation", 
            "benefits", "payment", "deadline", 
            "complaint", "general_information"
        ]
        
        if self.model_path and os.path.exists(self.model_path):
            self.load_model(self.model_path)
            
    def load_model(self, path: str):
        try:
            self.model = joblib.load(path)
        except Exception as e:
            logging.error(f"Failed to load model from {path}: {e}")
            self.model = None
            
    def train(self, texts: List[str], labels: List[str], save_path: str = None):
        """
        Trains the baseline TF-IDF + Logistic Regression model.
        """
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=10000)),
            ('clf', LogisticRegression(max_iter=1000, class_weight='balanced'))
        ])
        
        print(f"Training Intent Classifier on {len(texts)} samples...")
        pipeline.fit(texts, labels)
        self.model = pipeline
        
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            joblib.dump(self.model, save_path)
            print(f"Model saved to {save_path}")
            
    def predict(self, text: str) -> Tuple[str, float]:
        """
        Predicts intent and confidence for a single text.
        Returns ("unknown", 0.0) if model is not trained.
        """
        if not self.model:
            return "general_information", 0.0
            
        try:
            probas = self.model.predict_proba([text])[0]
            max_idx = probas.argmax()
            intent = self.model.classes_[max_idx]
            confidence = float(probas[max_idx])
            return intent, confidence
        except Exception as e:
            logging.error(f"Prediction failed: {e}")
            return "general_information", 0.0

if __name__ == "__main__":
    # Quick test
    texts = [
        "How do I apply for PM-KISAN?",
        "When is the next installment coming?",
        "What are the eligibility criteria for Awas Yojana?",
        "My money has not arrived, where do I complain?"
    ]
    labels = ["application", "payment", "eligibility", "complaint"]
    
    classifier = IntentClassifier()
    classifier.train(texts, labels)
    
    test_text = "I want to apply for the scheme but don't know how."
    intent, conf = classifier.predict(test_text)
    print(f"Text: '{test_text}' -> Intent: {intent} (Confidence: {conf:.2f})")

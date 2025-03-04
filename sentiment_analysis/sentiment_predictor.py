from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

class SentimentAnalyser:
    def __init__(self, model_path="sentiment_analysis/sentiment_model"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

    def predict(self, text):
        # Tokenize input
        inputs = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        ).to(self.device)

        # Predict
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Convert logits to probabilities and labels
        probabilities = torch.softmax(outputs.logits, dim=1).cpu().numpy()[0]
        predicted_label = torch.argmax(outputs.logits).item()

        return {
            "label": predicted_label,
            "probabilities": probabilities,
            "sentiment": self._label_to_sentiment(predicted_label)
        }

    def _label_to_sentiment(self, label):
        # Update these labels based on your training setup
        return {
            0: "negative",
            1: "neutral",
            2: "positive"
        }.get(label, "unknown")
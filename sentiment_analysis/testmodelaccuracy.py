# test_accuracy.py
from datasets import load_from_disk
from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
import torch
import numpy as np
from sklearn.metrics import accuracy_score

# Load the trained model and tokenizer
model_path = "sentiment_analysis/sentiment_model"
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
model = AutoModelForSequenceClassification.from_pretrained(model_path)

# Load the tokenized test dataset
dataset = load_from_disk("sentiment_analysis/dataset/tokenized")
test_dataset = dataset["test"]

# Define function to compute accuracy
def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc}

# Minimal training args (only what's needed for evaluation)
training_args = TrainingArguments(
    output_dir="./eval_results",
    per_device_eval_batch_size=32,  # Adjust based on GPU memory
    report_to="none",
)

# Initialize Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    compute_metrics=compute_metrics,
)

# Evaluate the model
results = trainer.evaluate(test_dataset)
print(f"Test Accuracy: {results['eval_accuracy'] * 100:.2f}%")
from datasets import load_from_disk
from transformers import AutoTokenizer

# Load dataset
dataset = load_from_disk("sentiment_analysis/dataset/sentiment140")

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

# Tokenize dataset
def tokenize_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True)

dataset = dataset.map(tokenize_function, batched=True)

# Split into train/test (90% train, 10% test)
dataset = dataset.train_test_split(test_size=0.1)

# Save processed dataset
dataset.save_to_disk("sentiment_analysis/dataset/tokenized")
print("Tokenized dataset saved successfully")
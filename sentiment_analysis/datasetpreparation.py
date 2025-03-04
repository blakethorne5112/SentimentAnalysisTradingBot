import pandas as pd
from datasets import Dataset

# Load Sentiment140 dataset (update path if needed)
file_path = "sentiment_analysis/dataset/training.1600000.processed.noemoticon.csv"

df = pd.read_csv(file_path, encoding="ISO-8859-1", header=None, names=["labels", "id", "date", "flag", "user", "text"])

# Keep only relevant columns
df = df[["labels", "text"]]

# Map labels: 0 → Negative, 2 → Neutral, 4 → Positive
df["labels"] = df["labels"].map({0: 0, 2: 1, 4: 2})

# Convert to Hugging Face Dataset format
dataset = Dataset.from_pandas(df)

# Save dataset
dataset.save_to_disk("sentiment_analysis/dataset/sentiment140")
print("Dataset saved successfully")
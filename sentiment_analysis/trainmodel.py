from datasets import load_from_disk
from transformers import AutoModelForSequenceClassification, TrainingArguments, Trainer
import torch

# Load tokenized dataset
dataset = load_from_disk("sentiment_analysis/dataset/tokenized")

# Load pre-trained DistilBERT model with 3 output labels
model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=3)

# Move model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Training arguments
training_args = TrainingArguments(
    output_dir="./results",
    eval_strategy="epoch",
    save_strategy="epoch",
    per_device_train_batch_size=16,  # Reduce batch size if running out of VRAM
    per_device_eval_batch_size=16,
    num_train_epochs=3,
    dataloader_pin_memory=True,
    dataloader_num_workers=0,
    report_to="none",
    gradient_accumulation_steps=2,  # Accumulates gradients over 2 steps
)

# Define Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    data_collator=None,  # Ensure you are not manually overriding device here
)

print(f"Model is on device: {model.device}")
print(f"Trainer is using device: {trainer.args.device}")

# Start Training
trainer.train()

# Save trained model
trainer.save_model("sentiment_model")
print("Model training complete. Training saved")
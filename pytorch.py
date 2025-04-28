import torch
# Debug to check if PyTorch is installed and CUDA is available. This is used for training the model.
print("CUDA Available:", torch.cuda.is_available())
print("GPU Name:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU detected")
print("PyTorch Version:", torch.__version__)
print("CUDA Version:", torch.version.cuda)
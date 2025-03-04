import torch
print("CUDA Available:", torch.cuda.is_available())
print("GPU Name:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU detected")
print("PyTorch Version:", torch.__version__)
print("CUDA Version:", torch.version.cuda)
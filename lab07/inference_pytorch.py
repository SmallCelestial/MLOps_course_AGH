import torch
from transformers import AutoTokenizer, AutoModel
import time

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

tokenizer = AutoTokenizer.from_pretrained("tokenizer/")

model = AutoModel.from_pretrained("models/")
model.to(device)
model.eval()


@torch.inference_mode()
def run_inference(text):
    inputs = tokenizer(
        text,
        padding=True,
        truncation=True,
        return_tensors="pt"
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    outputs = model(**inputs)
    return outputs.last_hidden_state


if __name__ == "__main__":
    text = "This is a test sentence for PyTorch inference."
    result = run_inference(text)
    print(f"Inference completed. Output shape: {result.shape}")


    while True:
        time.sleep(60)
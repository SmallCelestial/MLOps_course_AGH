import torch
from transformers import AutoModel, AutoTokenizer
from flask import Flask, request, jsonify

app = Flask(__name__)

device = torch.device("cpu")

model_name = "sentence-transformers/multi-qa-mpnet-base-cos-v1"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

model.to(device)
model.eval()

@app.route('/predict', methods=['POST'])
@torch.inference_mode()
def predict():
    text = request.json.get('text', '')
    inputs = tokenizer(text, padding=True, truncation=True, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    outputs = model(**inputs)
    return jsonify({"shape": list(outputs.last_hidden_state.shape)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
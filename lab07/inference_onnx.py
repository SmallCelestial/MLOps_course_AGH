import onnxruntime as ort
from transformers import AutoTokenizer
from flask import Flask, request, jsonify

app = Flask(__name__)

model_name = "sentence-transformers/multi-qa-mpnet-base-cos-v1"
tokenizer = AutoTokenizer.from_pretrained(model_name)

sess_options = ort.SessionOptions()
sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
session = ort.InferenceSession(
    "model_optimized.onnx",
    sess_options=sess_options,
    providers=["CPUExecutionProvider"]
)


@app.route('/predict', methods=['POST'])
def predict():
    text = request.json.get('text', '')
    inputs = tokenizer(text, padding=True, truncation=True, return_tensors="np")
    onnx_inputs = {
        "input_ids": inputs["input_ids"],
        "attention_mask": inputs["attention_mask"]
    }
    outputs = session.run(None, onnx_inputs)
    return jsonify({"shape": list(outputs[0].shape)})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
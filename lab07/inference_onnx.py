import onnxruntime as ort
from transformers import AutoTokenizer
import time

tokenizer = AutoTokenizer.from_pretrained("tokenizer/")

sess_options = ort.SessionOptions()
sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
session = ort.InferenceSession(
    "model_optimized.onnx",
    sess_options=sess_options,
    providers=["CPUExecutionProvider"]
)


def run_inference(text):
    inputs = tokenizer(
        text,
        padding=True,
        truncation=True,
        return_tensors="np"
    )

    onnx_inputs = {
        "input_ids": inputs["input_ids"],
        "attention_mask": inputs["attention_mask"]
    }

    outputs = session.run(None, onnx_inputs)
    return outputs


if __name__ == "__main__":
    text = "This is a test sentence for ONNX inference."
    result = run_inference(text)
    print(f"Inference completed. Output shape: {result[0].shape}")


    while True:
        time.sleep(60)
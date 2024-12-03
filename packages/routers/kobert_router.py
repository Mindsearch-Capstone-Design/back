""" 모델 로드
model = torch.load("model.pth")
model.eval()

@app.post("/predict")
def predict(data: dict):
    input_tensor = torch.tensor(data["input"])
    with torch.no_grad():
        output = model(input_tensor)
    return {"output": output.tolist()}
"""
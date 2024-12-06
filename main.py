from fastapi import FastAPI
from fastapi.responses import FileResponse  # FileResponse를 임포트
import os
import torch


app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/download-csv")
def download_csv():
    # CSV 파일 경로 설정
    file_path = "dataset/youtube_comments_2.csv"
    if os.path.exists(file_path):
        return FileResponse(path=file_path, media_type='text/csv', filename="example.csv")
    return {"error": "File not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
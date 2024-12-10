from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from packages.routers import youtube_crawler
from fastapi.responses import FileResponse  # FileResponse를 임포트
import os
import torch


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(youtube_crawler.router)

@app.get("/download-csv")
def download_csv():
    # CSV 파일 경로 설정
    file_path = "dataset/comments.csv"
    if os.path.exists(file_path):
        return FileResponse(path=file_path, media_type='text/csv', filename="example.csv")
    return {"error": "File not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
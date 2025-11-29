from fastapi import FastAPI

app = FastAPI(title="Debug App")


@app.get("/health")
def health():
    return {"status": "ok"}

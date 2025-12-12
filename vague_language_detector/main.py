from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .classifier import DetectionResult, detect


class TextRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Sentence or short paragraph to analyze")


class DetectionResponse(BaseModel):
    has_cognitive_distortion: bool

    @classmethod
    def from_result(cls, result: DetectionResult) -> "DetectionResponse":
        return cls(has_cognitive_distortion=result.has_cognitive_distortion)


app = FastAPI(title="Vague Language Detector", version="0.3.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/classify", response_model=DetectionResponse)
def classify_text(request: TextRequest):
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    result = detect(text)
    return DetectionResponse.from_result(result)

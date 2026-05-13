import json
import uvicorn
from pydantic import BaseModel, Field
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from recommend_engine import recommend_stream

app = FastAPI(title="AI Tools Nav - 智能助手 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://lflaitool.top"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)


class RecommendRequest(BaseModel):
    query: str = Field(..., description="用户的自然语言需求描述", examples=["我想做一个视频"])


@app.post("/api/recommend")
async def recommend(body: RecommendRequest):
    query = body.query.strip()
    if not query:
        return StreamingResponse(
            iter(["data: " + json.dumps({"token": "请提供您的问题。"}, ensure_ascii=False) + "\n\n"]),
            media_type="text/event-stream",
        )

    async def event_stream():
        try:
            async for token in recommend_stream(query):
                yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
        except Exception:
            yield f"data: {json.dumps({'token': '推荐服务暂时不可用，请稍后再试。'}, ensure_ascii=False)}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

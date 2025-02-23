from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from agent import CityWalkAgent, CityWalkResponse

# 加载环境变量
load_dotenv()

# 设置OpenAI API密钥

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = CityWalkAgent()

class Landmark(BaseModel):
    name: str
    latitude: float
    longitude: float

class City(BaseModel):
    name: str
    latitude: float
    longitude: float

class MetaData(BaseModel):
    city: City
    is_first_request: bool

@app.post("/answer", response_model=CityWalkResponse)
async def answer(query: str, metadata: MetaData = None) -> CityWalkResponse:
    """
    调用CityWalkAgent回答问题
    """
    try:
        if metadata.is_first_request:
            agent.conversation_reset()
        return agent.answer(query, metadata)
    except Exception as e:
        print(f"Error talking to agent: {str(e)}")
        return HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
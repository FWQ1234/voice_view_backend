from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import openai
import json

# 加载环境变量
load_dotenv()

# 设置OpenAI API密钥
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

class Landmark(BaseModel):
    name: str
    latitude: float
    longitude: float

class CityLandmarksRequest(BaseModel):
    city: str
    landmarks: List[Landmark]
    is_first_request: bool
    text: str

class CityLandmarksResponse(BaseModel):
    landmarks: List[Landmark]

class LandmarkRequest(BaseModel):
    landmark: str

class LandmarkResponse(BaseModel):
    response_text: str

def read_reddit_discussions(city: str) -> str:
    """
    读取城市的Reddit讨论文件
    文件命名规则: reddit_discussions/{city}.txt
    """
    try:
        filename = f"reddit_discussions/{city.lower().replace(' ', '_')}.txt"
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            print(f"No discussion file found for {city}")
            return ""
    except Exception as e:
        print(f"Error reading file for {city}: {str(e)}")
        return ""

async def get_openai_response(prompt: str) -> str:
    """
    调用OpenAI API获取响应
    """
    try:
        response = "Success Call OpenAI API"
        return response
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return None

@app.post("/process_city_landmarks_text", response_model=CityLandmarksResponse)
async def process_city_landmarks(request: CityLandmarksRequest):
    try:
        # 获取所有地标名称
        landmark_names = [landmark.name for landmark in request.landmarks]
        
        # 读取城市的Reddit讨论内容
        reddit_content = read_reddit_discussions(request.city)
        
        # 构建提示
        prompt = f"""
        City: {request.city}
        User Request: {request.text}
        Landmarks to focus on: {', '.join(landmark_names)}
        
        Reddit Discussions about {request.city}:
        {reddit_content}
        
        Based on the Reddit discussions above, please analyze these specific landmarks: {', '.join(landmark_names)}.
        Consider the user's request: {request.text}
        """
        
        # 如果是首次请求，调用OpenAI API
        ai_response = await get_openai_response(prompt)
        if ai_response:
            # 这里可以根据AI响应处理地标列表
            # 当前示例仅返回原始地标列表
            pass
        
        return CityLandmarksResponse(landmarks=request.landmarks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_landmark", response_model=LandmarkResponse)
async def process_landmark(request: LandmarkRequest):
    try:
        # 这里可以添加实际的地标描述逻辑
        # 示例中使用硬编码的响应
        landmark_descriptions = {
            "Statue of Liberty": "The Statue of Liberty is an iconic symbol of freedom, located on Liberty Island in New York Harbor.",
            "Times Square": "Times Square is a major commercial intersection, tourist destination, and entertainment center in New York City.",
            "Central Park": "Central Park is an urban park in New York City, located between the Upper West and Upper East Sides of Manhattan."
        }
        
        description = landmark_descriptions.get(
            request.landmark, 
            f"Description for {request.landmark} is not available."
        )
        
        return LandmarkResponse(response_text=description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
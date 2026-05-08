from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from database import (
    get_db, init_db, get_categories, get_category_by_id,
    get_news_list, get_news_detail, create_news, update_news, delete_news,
    get_config, update_config, verify_user, save_token, verify_token, remove_token
)

# ==================== 数据模型 ====================
class BannerModel(BaseModel):
    title: str
    description: str
    image_url: str

class ConfigModel(BaseModel):
    site_title: str
    slogan: str
    banners: List[BannerModel]

class NewsCreate(BaseModel):
    title: str
    summary: str
    content: str
    cover_image: str
    category: int
    author: Optional[str] = "管理员"

class NewsUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = None
    category: Optional[int] = None
    author: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# ==================== 生命周期管理 ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    init_db()
    print("数据库初始化完成")
    yield
    # 关闭时清理
    print("应用关闭")

# ==================== 创建应用 ====================
app = FastAPI(title="新闻管理系统API", lifespan=lifespan)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# ==================== 辅助函数 ====================
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user = verify_token(db, credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")
    return user

# ==================== API接口 ====================
@app.get("/api/config")
async def get_config_api(db: Session = Depends(get_db)):
    return get_config(db)

@app.put("/api/config")
async def update_config_api(config: ConfigModel, user=Depends(get_current_user), db: Session = Depends(get_db)):
    update_config(db, config.dict())
    return {"success": True}

@app.get("/api/news")
async def get_news_list_api(category: Optional[int] = None, page: int = 1, page_size: int = 12, db: Session = Depends(get_db)):
    return get_news_list(db, category, page, page_size)

@app.get("/api/news/{news_id}")
async def get_news_detail_api(news_id: int, db: Session = Depends(get_db)):
    news = get_news_detail(db, news_id)
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    return news

@app.post("/api/news")
async def create_news_api(news: NewsCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not get_category_by_id(db, news.category):
        raise HTTPException(status_code=400, detail="分类不存在")
    return create_news(db, news.dict())

@app.put("/api/news/{news_id}")
async def update_news_api(news_id: int, news: NewsUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    update_data = {k: v for k, v in news.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="没有提供更新数据")
    if "category" in update_data and not get_category_by_id(db, update_data["category"]):
        raise HTTPException(status_code=400, detail="分类不存在")
    updated_news = update_news(db, news_id, update_data)
    if not updated_news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    return updated_news

@app.delete("/api/news/{news_id}")
async def delete_news_api(news_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not delete_news(db, news_id):
        raise HTTPException(status_code=404, detail="新闻不存在")
    return {"success": True}

@app.get("/api/categories")
async def get_categories_api(db: Session = Depends(get_db)):
    return get_categories(db)

@app.post("/api/admin/login")
async def admin_login(login: LoginRequest, db: Session = Depends(get_db)):
    user = verify_user(db, login.username, login.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = str(uuid.uuid4())
    save_token(db, token, user["username"])
    return {"token": token, "user": user}

@app.post("/api/admin/logout")
async def admin_logout(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    remove_token(db, credentials.credentials)
    return {"success": True}

@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...), user=Depends(get_current_user)):
    return {"url": f"https://picsum.photos/seed/upload_{int(datetime.now().timestamp())}/800/500"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
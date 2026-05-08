from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
from typing import Optional, List
from datetime import timedelta
import hashlib

# 创建SQLite数据库引擎
engine = create_engine('sqlite:///news.db', connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==================== 数据库模型 ====================
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(200))
    news_list = relationship("News", back_populates="category_rel")


class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    cover_image = Column(String(500), nullable=False)
    category = Column(Integer, ForeignKey("categories.id"), nullable=False)
    author = Column(String(100), default="管理员")
    created_at = Column(DateTime, default=datetime.now)
    view_count = Column(Integer, default=0)
    category_rel = relationship("Category", back_populates="news_list")


class Banner(Base):
    __tablename__ = "banners"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=False)
    order = Column(Integer, default=0)


class Config(Base):
    __tablename__ = "config"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="admin")


class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), nullable=False)
    expires_at = Column(DateTime)


# 创建所有表
Base.metadata.create_all(bind=engine)


# ==================== 数据库操作函数 ====================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库"""
    db = SessionLocal()
    try:
        # 初始化分类
        if db.query(Category).count() == 0:
            categories = [
                Category(id=1, name="校园新闻", description="学校最新动态"),
                Category(id=2, name="通知公告", description="官方通知和公告"),
                Category(id=3, name="学术活动", description="讲座、研讨会信息"),
                Category(id=4, name="校园生活", description="社团活动、赛事")
            ]
            for cat in categories:
                db.add(cat)

        # 初始化用户 (admin/admin123)
        if db.query(User).count() == 0:
            password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            admin = User(username="admin", password_hash=password_hash, role="admin")
            db.add(admin)

        # 初始化模拟新闻
        if db.query(News).count() == 0:
            titles = [
                '2026年春季田径运动会圆满落幕 — 多项校纪录被打破',
                '人工智能学院正式揭牌成立，首批招收200名本科生',
                '图书馆新馆即将开放，新增24小时自习区和智慧阅览室',
                '我校博士生团队在国际顶级期刊发表重要研究成果',
                '2026年暑期社会实践项目申报通知',
                '校园歌手大赛决赛门票今日开抢！',
                '计算机学院举办人工智能前沿技术讲座',
                '关于2026届毕业生毕业典礼安排的通知',
                '我校男篮夺得省大学生篮球联赛冠军！',
                '研究生学术论坛征稿启事',
                '校园一卡通系统升级维护通知',
                '创新创业大赛校内选拔赛报名开启',
                '本周学术讲座汇总（4月20日-4月26日）',
                '学生食堂三楼装修升级，新增特色窗口',
                '关于五一劳动节放假安排的通知',
                '英语四六级考试报名通知',
                '我校与华为签署战略合作协议',
                '春季校园招聘会参展企业名单公布',
                '校园马拉松开始报名，等你来跑！',
                '优秀毕业生事迹展播：他们从这里出发'
            ]
            for i in range(20):
                news = News(
                    title=titles[i % len(titles)],
                    summary="这是新闻摘要...",
                    content="<p>这是新闻内容...</p>",
                    cover_image=f"https://picsum.photos/seed/news{i + 1}/400/280",
                    category=(i % 4) + 1,
                    author=['管理员', '校团委', '教务处', '宣传部'][i % 4],
                    created_at=datetime(2026, 3, 15, 8, 0, 0) + timedelta(days=i),
                    view_count=100 + i * 250
                )
                db.add(news)

        db.commit()
    finally:
        db.close()


def get_categories(db: Session):
    return [{"id": c.id, "name": c.name, "description": c.description} for c in db.query(Category).all()]


def get_category_by_id(db: Session, category_id: int):
    cat = db.query(Category).filter(Category.id == category_id).first()
    return {"id": cat.id, "name": cat.name, "description": cat.description} if cat else None


def get_news_list(db: Session, category: Optional[int] = None, page: int = 1, page_size: int = 12):
    query = db.query(News)
    if category:
        query = query.filter(News.category == category)
    total = query.count()
    news_list = query.order_by(News.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    results = [{
        "id": n.id, "title": n.title, "summary": n.summary, "content": n.content,
        "cover_image": n.cover_image, "category": n.category,
        "category_name": n.category_rel.name, "author": n.author,
        "created_at": n.created_at.isoformat(), "view_count": n.view_count
    } for n in news_list]
    return {"count": total, "results": results}


def get_news_detail(db: Session, news_id: int):
    news = db.query(News).filter(News.id == news_id).first()
    if news:
        news.view_count += 1
        db.commit()
        return {
            "id": news.id, "title": news.title, "summary": news.summary,
            "content": news.content, "cover_image": news.cover_image,
            "category": news.category, "category_name": news.category_rel.name,
            "author": news.author, "created_at": news.created_at.isoformat(),
            "view_count": news.view_count
        }
    return None


def create_news(db: Session, news_data: dict):
    news = News(**news_data)
    db.add(news)
    db.commit()
    db.refresh(news)
    return get_news_detail(db, news.id)


def update_news(db: Session, news_id: int, news_data: dict):
    news = db.query(News).filter(News.id == news_id).first()
    if news:
        for key, value in news_data.items():
            if value is not None:
                setattr(news, key, value)
        db.commit()
        return get_news_detail(db, news_id)
    return None


def delete_news(db: Session, news_id: int):
    news = db.query(News).filter(News.id == news_id).first()
    if news:
        db.delete(news)
        db.commit()
        return True
    return False


def get_config(db: Session):
    configs = {c.key: c.value for c in db.query(Config).all()}
    banners = [{"title": b.title, "description": b.description, "image_url": b.image_url}
               for b in db.query(Banner).order_by(Banner.order).all()]
    return {
        "site_title": configs.get("site_title", "西柚新闻网"),
        "slogan": configs.get("slogan", "传递校园最新动态 • 服务全体师生"),
        "banners": banners if banners else [
            {"title": "默认横幅", "description": "描述", "image_url": "https://picsum.photos/1200/400"}]
    }


def update_config(db: Session, config_data: dict):
    for key in ["site_title", "slogan"]:
        if key in config_data:
            conf = db.query(Config).filter(Config.key == key).first()
            if conf:
                conf.value = config_data[key]
            else:
                db.add(Config(key=key, value=config_data[key]))
    if "banners" in config_data:
        db.query(Banner).delete()
        for i, banner in enumerate(config_data["banners"]):
            db.add(Banner(**banner, order=i))
    db.commit()


def verify_user(db: Session, username: str, password: str):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user = db.query(User).filter(User.username == username, User.password_hash == password_hash).first()
    return {"username": user.username, "role": user.role} if user else None


def save_token(db: Session, token: str, username: str):
    from datetime import timedelta
    token_obj = Token(token=token, username=username, expires_at=datetime.now() + timedelta(hours=24))
    db.add(token_obj)
    db.commit()


def verify_token(db: Session, token: str):
    token_obj = db.query(Token).filter(Token.token == token, Token.expires_at > datetime.now()).first()
    return {"username": token_obj.username} if token_obj else None


def remove_token(db: Session, token: str):
    db.query(Token).filter(Token.token == token).delete()
    db.commit()
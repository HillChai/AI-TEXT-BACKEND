from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from admin import create_admin
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tasks import reset_model_quota  # 导入定时任务函数

# 初始化 FastAPI 应用
app = FastAPI()

# 初始化定时任务
# 每天凌晨 0 点执行一次 reset_model_quota
scheduler = AsyncIOScheduler()
scheduler.add_job(reset_model_quota, 'cron', hour=0, minute=0)

# 配置管理面板
create_admin(app)

# 注册路由
from routes import gpt_routes, prompt_routes, question_routes, user_routes
app.include_router(user_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(question_routes.router, prefix="/questions", tags=["Questions"])
app.include_router(gpt_routes.router, prefix="/gpt", tags=["GPT"])
app.include_router(prompt_routes.router, prefix="/prompts", tags=["Prompts"])

# 添加全局异常处理
from mylogger import logger
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"请求校验失败: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request format or missing fields"}
    )

# 配置允许的来源
origins = [
    "http://localhost:5173",  # 前端开发环境的地址
    "http://127.0.0.1:5173",  # 或其他需要的域名
]

# 添加跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 替换为前端的真实地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 打印启动日志
logger.info("FastAPI application started!")
logger.info("Access admin panel at: http://127.0.0.1:8000/admin")

# 根路由
@app.get("/")
def home():
    return {"message": "Welcome to the API!"}

# 在应用启动时启动 APScheduler
@app.on_event("startup")
async def startup_event():
    scheduler.start()
    print("APScheduler started.")
    print("Executing reset_model_quota task on startup.")
    await reset_model_quota()  # 直接调用异步任务

# 在应用关闭时停止 APScheduler
@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from routes import gpt_routes, prompt_routes, question_routes, user_routes
from mylogger import logger
from admin import create_admin
from fastapi.staticfiles import StaticFiles

# 初始化 FastAPI 应用
app = FastAPI()

# 配置管理面板
create_admin(app)

# 注册路由
app.include_router(user_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(question_routes.router, prefix="/questions", tags=["Questions"])
app.include_router(gpt_routes.router, prefix="/gpt", tags=["GPT"])
app.include_router(prompt_routes.router, prefix="/prompts", tags=["Prompts"])

# 添加全局异常处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"请求校验失败: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request format or missing fields"}
    )

# 添加跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 替换为前端的真实地址
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

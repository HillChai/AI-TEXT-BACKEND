from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from fastapi import Request, HTTPException
from models import User, Prompt  # 修改为实际的模型导入路径
from database import engine
from fastapi import FastAPI
from crud.user import get_user_by_username, verify_password
from mylogger import logger
from database import async_session_maker, engine  # 使用异步会话工厂

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username", "")
        password = form.get("password", "")

        # 日志记录
        logger.info(f"Login attempt for user: {username}")

        # 从数据库验证用户
        async with async_session_maker() as session:  # 使用异步会话
            db_user = await get_user_by_username(session, username)

            # 检查用户是否存在、密码是否正确以及是否为管理员
            if db_user and verify_password(password, db_user.password_hash):
                if db_user.user_type == "admin":  # 检查是否为管理员
                    logger.info(f"Admin user {username} logged in successfully.")
                    return True

        logger.warning(f"Failed login attempt for user: {username}")
        raise HTTPException(status_code=401, detail="Invalid credentials or not authorized")


# 初始化管理面板
def create_admin(app: FastAPI):
    auth_backend = AdminAuth(secret_key="your_secret_key")  # 替换为实际的 secret key
    admin = Admin(app, engine, authentication_backend=auth_backend)

    # 定义模型视图
    class UserAdmin(ModelView, model=User):
        column_list = [User.id, User.username, User.model_quota, User.membership_type]
        searchable_columns = [User.username]

    class PromptAdmin(ModelView, model=Prompt):
        column_list = [Prompt.id, Prompt.content, Prompt.user_id]

    # 注册视图
    admin.add_view(UserAdmin)
    admin.add_view(PromptAdmin)


from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from fastapi import Request, HTTPException
from models import User, Prompt  # 修改为实际的模型导入路径
from database import engine
from fastapi import FastAPI
from config import settings

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        # Validate username/password credentials
        # And update session
        request.session.update({"token": "..."})

        return True

    async def logout(self, request: Request) -> bool:
        # Usually you'd want to just clear the session
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            return False

        # Check the token in depth
        return True


# 初始化管理面板
def create_admin(app: FastAPI):
    auth_backend = AdminAuth(secret_key=settings.ADMIN_KEY)  # 替换为实际的 secret key
    admin = Admin(app, engine, authentication_backend=auth_backend)
    # admin = Admin(app, engine)

    # 定义模型视图
    class UserAdmin(ModelView, model=User):
        column_list = [User.id, User.username, User.model_quota, User.membership_type]
        searchable_columns = [User.username]

    class PromptAdmin(ModelView, model=Prompt):
        column_list = [Prompt.id, Prompt.content, Prompt.user_id]

    # 注册视图
    admin.add_view(UserAdmin)
    admin.add_view(PromptAdmin)


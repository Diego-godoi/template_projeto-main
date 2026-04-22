from fastapi import APIRouter

from .file import router as file_router
from .login import router as login_router
from .roles import router as roles_router
from .user_roles import router as user_roles_router
from .users import router as users_router

routers = APIRouter()

routers.include_router(login_router)
routers.include_router(file_router)
routers.include_router(roles_router)
routers.include_router(users_router)
routers.include_router(user_roles_router)

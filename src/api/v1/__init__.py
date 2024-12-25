from fastapi.routing import APIRouter

from api.v1.admin import router as admin_router
from api.v1.auth import router as auth_router
from api.v1.oauth import router as oauth_router
from api.v1.profile import router as profile_router

router = APIRouter()
router.include_router(profile_router)
router.include_router(auth_router)
router.include_router(oauth_router)
router.include_router(admin_router)

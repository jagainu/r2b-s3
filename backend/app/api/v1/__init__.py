from fastapi import APIRouter

from app.api.v1.endpoints import auth, cat_breeds, health, masters, quiz, users

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(auth.router)
router.include_router(cat_breeds.router)
router.include_router(masters.router)
router.include_router(quiz.router)
router.include_router(users.router)

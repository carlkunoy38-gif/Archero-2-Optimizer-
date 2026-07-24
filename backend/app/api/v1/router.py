"""Aggregates all v1 routers under a single APIRouter."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import accounts, heroes, skills, weapons

api_router = APIRouter()
api_router.include_router(heroes.router)
api_router.include_router(weapons.router)
api_router.include_router(skills.router)
api_router.include_router(accounts.router)

"""Aggregates every route module under a single APIRouter.

`app/main.py` mounts this once, under `Settings.api_v1_prefix`.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    accounts,
    amulets,
    armor,
    chapters,
    equipment,
    heroes,
    ownership,
    pets,
    rings,
    runes,
    skills,
    weapons,
)

api_router = APIRouter()

# Catalog (read-only)
api_router.include_router(heroes.router)
api_router.include_router(weapons.router)
api_router.include_router(armor.router)
api_router.include_router(rings.router)
api_router.include_router(amulets.router)
api_router.include_router(pets.router)
api_router.include_router(runes.router)
api_router.include_router(skills.router)
api_router.include_router(chapters.router)

# Accounts: core CRUD, ownership sub-resources, equipment actions
api_router.include_router(accounts.router)
api_router.include_router(ownership.router)
api_router.include_router(equipment.router)

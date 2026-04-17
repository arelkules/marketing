from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database import get_db
from app.models.asset import GeneratedAsset
from app.routers.assets import _to_out
from app.schemas.asset import AssetOut

router = APIRouter()

STAGES = ["ideas", "draft", "review", "published", "archived"]


@router.get("", response_model=dict[str, list[AssetOut]])
async def get_pipeline(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GeneratedAsset).order_by(GeneratedAsset.created_at.desc())
    )
    assets = result.scalars().all()
    board: dict[str, list[AssetOut]] = {stage: [] for stage in STAGES}
    for asset in assets:
        stage = asset.pipeline_stage if asset.pipeline_stage in STAGES else "draft"
        board[stage].append(_to_out(asset))
    return board


@router.patch("/{asset_id}/stage", response_model=AssetOut)
async def move_stage(asset_id: str, stage: str, db: AsyncSession = Depends(get_db)):
    if stage not in STAGES:
        raise HTTPException(400, f"Stage must be one of: {STAGES}")
    asset = await db.get(GeneratedAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")
    asset.pipeline_stage = stage
    await db.commit()
    await db.refresh(asset)
    return _to_out(asset)

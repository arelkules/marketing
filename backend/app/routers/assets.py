import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.asset import GeneratedAsset
from app.schemas.asset import AssetCreate, AssetUpdate, AssetOut

router = APIRouter()


def _to_out(asset: GeneratedAsset) -> AssetOut:
    tags = asset.tags
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = []
    return AssetOut(
        id=asset.id,
        agent_type=asset.agent_type,
        title=asset.title,
        content=asset.content,
        tags=tags,
        pipeline_stage=asset.pipeline_stage,
        word_count=asset.word_count,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.post("", response_model=AssetOut)
async def create_asset(data: AssetCreate, db: AsyncSession = Depends(get_db)):
    asset = GeneratedAsset(
        id=str(uuid.uuid4()),
        message_id=data.message_id,
        agent_type=data.agent_type,
        title=data.title,
        content=data.content,
        tags=json.dumps(data.tags),
        pipeline_stage=data.pipeline_stage,
        word_count=len(data.content.split()),
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return _to_out(asset)


@router.get("", response_model=list[AssetOut])
async def list_assets(
    agent_type: str | None = None,
    pipeline_stage: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(GeneratedAsset).order_by(GeneratedAsset.created_at.desc())
    if agent_type:
        q = q.where(GeneratedAsset.agent_type == agent_type)
    if pipeline_stage:
        q = q.where(GeneratedAsset.pipeline_stage == pipeline_stage)
    result = await db.execute(q)
    return [_to_out(a) for a in result.scalars().all()]


@router.get("/{asset_id}", response_model=AssetOut)
async def get_asset(asset_id: str, db: AsyncSession = Depends(get_db)):
    asset = await db.get(GeneratedAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")
    return _to_out(asset)


@router.patch("/{asset_id}", response_model=AssetOut)
async def update_asset(asset_id: str, data: AssetUpdate, db: AsyncSession = Depends(get_db)):
    asset = await db.get(GeneratedAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")
    if data.title is not None:
        asset.title = data.title
    if data.content is not None:
        asset.content = data.content
        asset.word_count = len(data.content.split())
    if data.tags is not None:
        asset.tags = json.dumps(data.tags)
    if data.pipeline_stage is not None:
        asset.pipeline_stage = data.pipeline_stage
    await db.commit()
    await db.refresh(asset)
    return _to_out(asset)


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(asset_id: str, db: AsyncSession = Depends(get_db)):
    asset = await db.get(GeneratedAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")
    await db.delete(asset)
    await db.commit()

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ai.ambient.code_review_agent import code_review_agent
from app.core.logger import logger

router = APIRouter(prefix="/code-review", tags=["code-review"])


class AnalyzeDiffRequest(BaseModel):
    repo_path: str
    base_branch: str = "main"
    head_branch: Optional[str] = None


class AnalyzeCommitRequest(BaseModel):
    repo_path: str
    commit_hash: str


class AddRepoRequest(BaseModel):
    path: str
    name: Optional[str] = None


@router.post("/analyze")
async def analyze_diff(req: AnalyzeDiffRequest):
    try:
        res = await code_review_agent.analyze_diff(
            repo_path=req.repo_path,
            base_branch=req.base_branch,
            head_branch=req.head_branch,
        )
        return res
    except Exception as e:
        logger.error(f"Error analyzing diff: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-commit")
async def analyze_commit(req: AnalyzeCommitRequest):
    try:
        res = await code_review_agent.analyze_commit(
            repo_path=req.repo_path,
            commit_hash=req.commit_hash,
        )
        return res
    except Exception as e:
        logger.error(f"Error analyzing commit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reviews")
async def list_reviews(repo_path: Optional[str] = None, limit: int = 20):
    return code_review_agent.list_reviews(repo_path=repo_path, limit=limit)


@router.get("/reviews/{review_id}")
async def get_review(review_id: str):
    rev = code_review_agent.get_review(review_id)
    if not rev:
        raise HTTPException(status_code=404, detail="Review not found")
    return rev


@router.post("/repos")
async def add_repo(req: AddRepoRequest):
    code_review_agent.add_repo(repo_path=req.path, name=req.name)
    return {"status": "success", "message": "Repo added to watch list"}


@router.get("/repos")
async def list_repos():
    return await code_review_agent.list_repos()

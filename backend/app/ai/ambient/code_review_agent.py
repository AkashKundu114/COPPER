import asyncio
import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.ai.llm.ollama_client import ollama_client
from app.core.constants import AgentType
from app.core.logger import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
os.makedirs(DATA_DIR, exist_ok=True)
WATCHED_REPOS_FILE = DATA_DIR / "watched_repos.json"
CODE_REVIEWS_FILE = DATA_DIR / "code_reviews.json"

@dataclass
class ReviewResult:
    review_id: str
    repo_path: str
    branch: str
    commit_hash: str
    files_changed: int
    insertions: int
    deletions: int
    pr_description: str
    risk_analysis: list[dict]
    suggestions: list[dict]
    test_gaps: list[str]
    created_at: datetime


class CodeReviewAgent:
    def __init__(self):
        self.watched_repos: list[dict[str, str]] = self._load_json(WATCHED_REPOS_FILE, [])
        self.reviews: dict[str, ReviewResult] = self._load_reviews()

    def _load_json(self, path: Path, default: Any) -> Any:
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
        return default

    def _save_json(self, path: Path, data: Any):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving {path}: {e}")

    def _load_reviews(self) -> dict[str, ReviewResult]:
        raw_data = self._load_json(CODE_REVIEWS_FILE, {})
        reviews = {}
        for k, v in raw_data.items():
            try:
                v["created_at"] = datetime.fromisoformat(v["created_at"])
                reviews[k] = ReviewResult(**v)
            except Exception as e:
                logger.error(f"Error parsing review {k}: {e}")
        return reviews

    def _save_reviews(self):
        data = {k: asdict(v) for k, v in self.reviews.items()}
        for k, v in data.items():
            v["created_at"] = v["created_at"].isoformat()
        self._save_json(CODE_REVIEWS_FILE, data)

    def add_repo(self, repo_path: str, name: str | None = None):
        for r in self.watched_repos:
            if r["path"] == repo_path:
                return
        self.watched_repos.append({"path": repo_path, "name": name or Path(repo_path).name})
        self._save_json(WATCHED_REPOS_FILE, self.watched_repos)

    async def list_repos(self) -> list[dict]:
        return self.watched_repos

    def get_review(self, review_id: str) -> ReviewResult | None:
        return self.reviews.get(review_id)

    def list_reviews(self, repo_path: str | None = None, limit: int = 20) -> list[ReviewResult]:
        res = list(self.reviews.values())
        if repo_path:
            res = [r for r in res if r.repo_path == repo_path]
        res.sort(key=lambda x: x.created_at, reverse=True)
        return res[:limit]

    async def _run_git(self, repo_path: str, *args) -> tuple[int, str, str]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", *args,
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            return proc.returncode or 0, stdout.decode("utf-8", errors="ignore"), stderr.decode("utf-8", errors="ignore")
        except FileNotFoundError:
            logger.error("Git is not installed or not in PATH")
            return 1, "", "Git is not installed"
        except Exception as e:
            logger.error(f"Error running git {args} in {repo_path}: {e}")
            return 1, "", str(e)

    def _parse_diff_stats(self, diff_text: str) -> tuple[int, int, int]:
        files, ins, dels = 0, 0, 0
        for line in diff_text.splitlines():
            if line.startswith("diff --git"):
                files += 1
            elif line.startswith("+") and not line.startswith("+++"):
                ins += 1
            elif line.startswith("-") and not line.startswith("---"):
                dels += 1
        return files, ins, dels

    def _get_changed_files(self, diff_text: str) -> list[str]:
        files = []
        for line in diff_text.splitlines():
            if line.startswith("--- a/"):
                files.append(line[6:])
            elif line.startswith("+++ b/"):
                files.append(line[6:])
        return list(set(files))

    def _detect_test_gaps(self, changed_files: list[str]) -> list[str]:
        gaps = []
        # Filter for source files
        src_files = [f for f in changed_files if (f.startswith("src/") or f.startswith("app/")) and f.endswith(".py")]
        # Any test files changed?
        test_files = [f for f in changed_files if "test" in f]
        
        if src_files and not test_files:
            return src_files
        
        return []

    async def _analyze_with_llm(self, diff_text: str) -> tuple[str, list[dict], list[dict]]:
        llm_avail = await ollama_client.is_available()
        if not llm_avail:
            return "Basic PR description (LLM offline)", [{"file": "all", "risk_level": "unknown", "issues": "LLM offline"}], []
        
        try:
            model = "qwen2.5-coder:7b"
            prompt_desc = f"Generate a concise PR description for these changes:\n\n{diff_text[:4000]}"
            pr_desc = await ollama_client.chat([{"role": "user", "content": prompt_desc}], model=model)
            
            prompt_risk = f"Identify potential bugs or issues in these changes. Rate risk as low/medium/high. Respond in JSON array format [{{'file': '...', 'risk_level': '...', 'issues': '...'}}]. Diff:\n\n{diff_text[:4000]}"
            risk_text = await ollama_client.chat([{"role": "user", "content": prompt_risk}], model=model)
            
            prompt_sugg = f"Suggest improvements for code quality, performance, or readability. Respond in JSON array format [{{'file': '...', 'line': '...', 'suggestion': '...', 'reason': '...'}}]. Diff:\n\n{diff_text[:4000]}"
            sugg_text = await ollama_client.chat([{"role": "user", "content": prompt_sugg}], model=model)
            
            # Simple JSON extraction (best effort)
            def _extract_json(text: str) -> list[dict]:
                import re
                try:
                    match = re.search(r'\[.*\]', text.replace('\n', ' '))
                    if match:
                        return json.loads(match.group(0))
                except:
                    pass
                return []
            
            return pr_desc, _extract_json(risk_text), _extract_json(sugg_text)
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return "Error generating description", [], []

    async def analyze_diff(self, repo_path: str, base_branch: str = "main", head_branch: str | None = None) -> ReviewResult:
        if head_branch:
            code, diff_out, err = await self._run_git(repo_path, "diff", f"{base_branch}...{head_branch}")
            branch = head_branch
        else:
            code, diff_out, err = await self._run_git(repo_path, "diff", "--staged")
            branch = "staged"
            
        if code != 0:
            logger.error(f"Git diff failed: {err}")
            diff_out = ""

        files_changed, insertions, deletions = self._parse_diff_stats(diff_out)
        changed_file_list = self._get_changed_files(diff_out)
        test_gaps = self._detect_test_gaps(changed_file_list)
        
        pr_description, risk_analysis, suggestions = await self._analyze_with_llm(diff_out)
        
        # Get latest commit hash
        c_code, c_out, c_err = await self._run_git(repo_path, "rev-parse", "HEAD")
        commit_hash = c_out.strip() if c_code == 0 else "unknown"
        
        review = ReviewResult(
            review_id=str(uuid.uuid4()),
            repo_path=repo_path,
            branch=branch,
            commit_hash=commit_hash,
            files_changed=files_changed,
            insertions=insertions,
            deletions=deletions,
            pr_description=pr_description,
            risk_analysis=risk_analysis,
            suggestions=suggestions,
            test_gaps=test_gaps,
            created_at=datetime.utcnow()
        )
        
        self.reviews[review.review_id] = review
        self._save_reviews()
        return review

    async def analyze_commit(self, repo_path: str, commit_hash: str) -> ReviewResult:
        code, diff_out, err = await self._run_git(repo_path, "show", commit_hash)
        if code != 0:
            logger.error(f"Git show failed: {err}")
            diff_out = ""

        files_changed, insertions, deletions = self._parse_diff_stats(diff_out)
        changed_file_list = self._get_changed_files(diff_out)
        test_gaps = self._detect_test_gaps(changed_file_list)
        
        pr_description, risk_analysis, suggestions = await self._analyze_with_llm(diff_out)
        
        review = ReviewResult(
            review_id=str(uuid.uuid4()),
            repo_path=repo_path,
            branch="commit",
            commit_hash=commit_hash,
            files_changed=files_changed,
            insertions=insertions,
            deletions=deletions,
            pr_description=pr_description,
            risk_analysis=risk_analysis,
            suggestions=suggestions,
            test_gaps=test_gaps,
            created_at=datetime.utcnow()
        )
        
        self.reviews[review.review_id] = review
        self._save_reviews()
        return review

code_review_agent = CodeReviewAgent()

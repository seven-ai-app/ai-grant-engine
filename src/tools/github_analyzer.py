import logging
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


async def analyze_github_repos(urls: list[str]) -> dict:
    """Analyze GitHub repositories for technical depth, architecture, and complexity."""
    combined = {
        "repositories": [],
        "total_files": 0,
        "languages": {},
        "architecture_summary": "",
        "complexity_indicators": [],
        "key_algorithms": [],
        "dependencies": [],
    }

    for url in urls:
        repo_data = await _analyze_single_repo(url)
        combined["repositories"].append(repo_data)
        combined["total_files"] += repo_data.get("file_count", 0)
        for lang, pct in repo_data.get("languages", {}).items():
            combined["languages"][lang] = combined["languages"].get(lang, 0) + pct

    combined["architecture_summary"] = _summarize_architecture(combined["repositories"])
    return combined


async def _analyze_single_repo(url: str) -> dict:
    """Analyze a single GitHub repository."""
    try:
        import httpx
        from ..config.settings import Settings

        settings = Settings()
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            return {"url": url, "error": "Invalid GitHub URL"}

        owner, repo = path_parts[0], path_parts[1]
        headers = {"Accept": "application/vnd.github.v3+json"}
        if settings.github_token:
            headers["Authorization"] = f"token {settings.github_token}"

        async with httpx.AsyncClient(timeout=30) as client:
            # Get repo info
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}", headers=headers
            )
            if resp.status_code != 200:
                return {"url": url, "error": f"GitHub API error: {resp.status_code}"}
            repo_info = resp.json()

            # Get languages
            lang_resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/languages", headers=headers
            )
            languages = lang_resp.json() if lang_resp.status_code == 200 else {}

            # Get tree for file structure
            tree_resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1",
                headers=headers,
            )
            tree_data = tree_resp.json() if tree_resp.status_code == 200 else {}
            files = tree_data.get("tree", [])

        # Analyze structure
        file_types = {}
        dirs = set()
        for f in files:
            if f["type"] == "blob":
                ext = Path(f["path"]).suffix
                file_types[ext] = file_types.get(ext, 0) + 1
            elif f["type"] == "tree":
                dirs.add(f["path"].split("/")[0])

        # Detect architectural patterns
        patterns = _detect_patterns(dirs, [f["path"] for f in files if f["type"] == "blob"])

        return {
            "url": url,
            "name": repo_info.get("name", repo),
            "description": repo_info.get("description", ""),
            "stars": repo_info.get("stargazers_count", 0),
            "languages": languages,
            "file_count": len([f for f in files if f["type"] == "blob"]),
            "file_types": file_types,
            "top_dirs": list(dirs)[:20],
            "patterns": patterns,
            "topics": repo_info.get("topics", []),
            "created_at": repo_info.get("created_at", ""),
            "updated_at": repo_info.get("pushed_at", ""),
        }

    except Exception as e:
        logger.error(f"Error analyzing {url}: {e}")
        return {"url": url, "error": str(e)}


def _detect_patterns(dirs: set, file_paths: list[str]) -> list[str]:
    """Detect architectural patterns from directory structure."""
    patterns = []
    dir_lower = {d.lower() for d in dirs}
    paths_lower = [p.lower() for p in file_paths]

    if "src" in dir_lower or "lib" in dir_lower:
        patterns.append("structured_source")
    if "tests" in dir_lower or "test" in dir_lower or "__tests__" in dir_lower:
        patterns.append("has_tests")
    if "docker-compose.yml" in paths_lower or "dockerfile" in paths_lower:
        patterns.append("containerized")
    if any("ci" in p or "github/workflows" in p for p in paths_lower):
        patterns.append("ci_cd")
    if "api" in dir_lower or "routes" in dir_lower:
        patterns.append("api_service")
    if any("ml" in d or "model" in d for d in dir_lower):
        patterns.append("machine_learning")
    if any("algorithm" in p or "solver" in p for p in paths_lower):
        patterns.append("algorithmic")
    if "infra" in dir_lower or "terraform" in dir_lower:
        patterns.append("infrastructure_as_code")

    return patterns


def _summarize_architecture(repos: list[dict]) -> str:
    """Create a text summary of the overall architecture."""
    if not repos:
        return "No repositories analyzed."

    all_languages = {}
    all_patterns = set()
    for repo in repos:
        for lang, count in repo.get("languages", {}).items():
            all_languages[lang] = all_languages.get(lang, 0) + count
        all_patterns.update(repo.get("patterns", []))

    top_langs = sorted(all_languages.items(), key=lambda x: -x[1])[:5]
    lang_str = ", ".join(f"{l[0]}" for l in top_langs)

    summary = f"Primary languages: {lang_str}. "
    summary += f"Architectural patterns detected: {', '.join(all_patterns)}. "
    summary += f"Total repositories: {len(repos)}, "
    summary += f"Total files: {sum(r.get('file_count', 0) for r in repos)}."

    return summary

"""Public GitHub/GitLab adapters. Requests only reach fixed provider API hosts."""
import base64
import hashlib
import os
import re
import time
from collections import Counter
from urllib.parse import quote, urlsplit

import requests
from django.core.cache import cache
from django.utils import timezone

from .utils.skill_detector import MANIFESTS, audit_readme, detect_evidence

MAX_REPOS = 500
MAX_FILES = 12
MAX_FILE_BYTES = 150_000


class AnalysisError(Exception):
    pass


def parse_target(value, provider):
    if provider not in {"github", "gitlab"}:
        raise AnalysisError("Choose GitHub or GitLab.")
    value = value.strip()
    if "://" in value:
        parsed = urlsplit(value)
        if parsed.scheme != "https" or parsed.netloc.lower() != provider + ".com" or parsed.query or parsed.fragment:
            raise AnalysisError(f"Use a public https://{provider}.com profile or repository URL without query parameters.")
        value = parsed.path.strip("/")
    value = value.strip("/").removesuffix(".git")
    parts = value.split("/")
    if not value or len(value) > 250 or any(not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", part) or part in {".", ".."} for part in parts):
        raise AnalysisError("Enter a username or a repository path such as owner/project.")
    if provider == "github" and len(parts) > 2:
        raise AnalysisError("Use a GitHub username or owner/repository path.")
    return value


class Provider:
    def __init__(self, name):
        self.name = name
        self.base = "https://api.github.com" if name == "github" else "https://gitlab.com/api/v4"
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/vnd.github+json" if name == "github" else "application/json", "User-Agent": "DevProfile-Toolkit"})
        token = os.environ.get("GITHUB_TOKEN" if name == "github" else "GITLAB_TOKEN")
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"} if name == "github" else {"PRIVATE-TOKEN": token})
        self.deadline = time.monotonic() + 35

    def get(self, path, params=None, optional=False):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise AnalysisError("The scan time limit was reached. Try a single repository instead.")
        try:
            response = self.session.get(self.base + path, params=params, timeout=min(8, remaining), allow_redirects=False)
        except requests.RequestException as exc:
            raise AnalysisError("The provider could not be reached. Please try again.") from exc
        if response.status_code == 404 and optional:
            return None
        if response.status_code in {403, 429}:
            raise AnalysisError("The provider denied access or reached its API rate limit. Try later; a server-side read-only token can increase access.")
        if response.status_code == 404:
            raise AnalysisError("Public profile or repository not found. Check the provider and path.")
        if response.status_code == 401:
            raise AnalysisError("The server's provider token is invalid or expired.")
        if response.status_code != 200:
            raise AnalysisError("The provider returned an unexpected response. Please try again.")
        if len(response.content) > 3_000_000:
            raise AnalysisError("The provider response exceeded the scan size limit.")
        try:
            return response.json()
        except ValueError as exc:
            raise AnalysisError("The provider returned an invalid response.") from exc

    def normalize(self, repo):
        github = self.name == "github"
        return {"name": repo.get("full_name") if github else repo.get("path_with_namespace"), "description": repo.get("description") or "No description provided.", "url": repo.get("html_url") if github else repo.get("web_url"), "stars": repo.get("stargazers_count", 0) if github else repo.get("star_count", 0), "fork": bool(repo.get("fork") if github else repo.get("forked_from_project")), "archived": repo.get("archived", False), "language": repo.get("language") if github else None, "updated": repo.get("pushed_at") if github else repo.get("last_activity_at"), "branch": repo.get("default_branch") or "HEAD", "id": repo.get("full_name") if github else repo["id"]}

    def repositories(self, target):
        if "/" in target:
            path = f"/repos/{target}" if self.name == "github" else f"/projects/{quote(target, safe='')}"
            raw = self.get(path)
            if raw.get("private") or (self.name == "gitlab" and raw.get("visibility") != "public"):
                raise AnalysisError("Only public repositories are supported.")
            return {"name": target, "bio": "Repository analysis", "url": f"https://{self.name}.com/{target}"}, [self.normalize(raw)], True
        if self.name == "github":
            user = self.get(f"/users/{target}")
            path = f"/users/{target}/repos"
            params = {"sort": "updated", "type": "owner"}
            profile = {"name": user.get("name") or target, "bio": user.get("bio") or "Public GitHub profile", "url": user["html_url"]}
        else:
            users = self.get("/users", {"username": target})
            if not users:
                raise AnalysisError("GitLab user not found. For groups, enter the full group/project path.")
            user = users[0]
            path = f"/users/{user['id']}/projects"
            params = {"order_by": "updated_at", "visibility": "public"}
            profile = {"name": user.get("name") or target, "bio": "Public projects owned by this GitLab user", "url": user["web_url"]}
        repos = []
        for page in range(1, MAX_REPOS // 100 + 1):
            batch = self.get(path, {**params, "per_page": 100, "page": page})
            repos.extend(self.normalize(repo) for repo in batch)
            if len(batch) < 100:
                return profile, repos, True
        return profile, repos, False

    def inspect(self, repo):
        github = self.name == "github"
        root = f"/repos/{repo['id']}" if github else f"/projects/{repo['id']}"
        params = {"ref": repo["branch"]}
        entries = []
        listing_complete = False
        for page in range(1, 6):
            batch = self.get(root + ("/contents" if github else "/repository/tree"), {**params, "per_page": 100, "page": page}, optional=True)
            if batch is None:
                listing_complete = True
                break
            entries.extend(batch)
            if github or len(batch) < 100:
                listing_complete = len(batch) < (1000 if github else 100)
                break
        files = {}
        selected = [e for e in entries if e.get("type") in {"file", "blob"} and (e["name"] in MANIFESTS or re.fullmatch(r"readme(?:\.(?:md|markdown|rst|txt))?", e["name"], re.I))]
        selected.sort(key=lambda e: (not e["name"].lower().startswith("readme"), e["name"]))
        notes = []
        if not listing_complete:
            notes.append("Root directory listing reached the provider scan limit.")
        if len(selected) > MAX_FILES:
            notes.append(f"Only the first {MAX_FILES} README and manifest files were read.")
        for entry in selected[:MAX_FILES]:
            if entry.get("size", 0) > MAX_FILE_BYTES:
                notes.append(f"Skipped oversized file: {entry['name']}")
                continue
            path = entry["path"]
            endpoint = root + (f"/contents/{quote(path, safe='/')}" if github else f"/repository/files/{quote(path, safe='')}")
            obj = self.get(endpoint, params, optional=True)
            if obj and obj.get("encoding") == "base64":
                try:
                    raw = base64.b64decode(obj.get("content", ""), validate=False)
                    if len(raw) <= MAX_FILE_BYTES:
                        files[path] = raw.decode("utf-8", errors="replace")
                    else:
                        notes.append(f"Skipped oversized file: {path}")
                except (ValueError, TypeError):
                    notes.append(f"Could not decode {path}.")
        languages = self.get(root + "/languages", optional=True) or {}
        readme_name = next((path for path in files if path.lower().startswith("readme")), "")
        readme = files.get(readme_name, "")
        audit = audit_readme(readme)
        total = sum(languages.values())
        return {"repository": repo, "files": list(files), "evidence": detect_evidence(files), "audit": audit, "readme": readme, "readme_name": readme_name, "readme_score": round(sum(c["passed"] for c in audit) / len(audit) * 100), "languages": [{"name": name, "percent": round(value / total * 100, 1)} for name, value in sorted(languages.items(), key=lambda pair: -pair[1]) if total], "notes": notes, "import_data": import_fields(repo, files)}


def import_fields(repo, files):
    install = usage = ""
    if "package.json" in files:
        install = "npm install"
        try:
            import json
            scripts = json.loads(files["package.json"]).get("scripts", {})
            command = next((name for name in ("dev", "start") if name in scripts), None)
            usage = f"```shell\nnpm run {command}\n```" if command else ""
        except (ValueError, AttributeError):
            pass
    elif "requirements.txt" in files:
        install = "python -m pip install -r requirements.txt"
    return {"document_type": "project", "name": repo["name"].split("/")[-1], "tagline": repo["description"], "repository": repo["url"], "installation": install, "usage": usage, "tech_stack": ", ".join(dict.fromkeys(e["name"] for e in detect_evidence(files)))}


def analyze(target, provider, include_forks=False, include_archived=False):
    target = parse_target(target, provider)
    identity = f"{provider}:{target}:{include_forks}:{include_archived}"
    key = "analysis:v2:" + hashlib.sha256(identity.encode()).hexdigest()
    cached = cache.get(key)
    if cached:
        return cached
    api = Provider(provider)
    try:
        profile, repos, complete = api.repositories(target)
        filtered = [r for r in repos if (include_forks or not r["fork"]) and (include_archived or not r["archived"])]
        ranked = sorted(filtered, key=lambda r: (r["stars"], r["updated"] or ""), reverse=True)
        counts = Counter(r["language"] for r in filtered if r["language"])
        result = {"provider": provider, "target": target, "profile": profile, "repositories": ranked, "count": len(filtered), "fetched": len(repos), "complete": complete, "stars": sum(r["stars"] for r in filtered), "scanned_at": timezone.now().isoformat(), "language_counts": [{"name": name, "count": count} for name, count in counts.most_common()], "inspection": None, "warnings": [], "include_forks": include_forks, "include_archived": include_archived}
        if "/" in target and ranked:
            try:
                result["inspection"] = api.inspect(ranked[0])
            except AnalysisError as exc:
                result["warnings"].append(f"Repository metadata loaded, but file inspection is unavailable: {exc}")
        cache.set(key, result, 600)
        return result
    finally:
        api.session.close()

"""Conservative file-based stack detection; no claims about developer skill."""
import json
import re
from pathlib import PurePosixPath

MANIFESTS = {"package.json", "requirements.txt", "pyproject.toml", "Pipfile", "pubspec.yaml", "Cargo.toml", "go.mod", "composer.json", "pom.xml", "build.gradle", "Gemfile", "Dockerfile", ".gitlab-ci.yml"}


def detect_evidence(files):
    evidence = []
    for path, content in files.items():
        filename = PurePosixPath(path).name
        if filename == "package.json":
            try:
                obj = json.loads(content)
                names = set()
                for key in ("dependencies", "devDependencies", "peerDependencies"):
                    if isinstance(obj.get(key), dict):
                        names.update(obj[key])
            except (ValueError, AttributeError, TypeError):
                continue
            mapping = {"react": "React", "next": "Next.js", "vue": "Vue", "express": "Express", "@angular/core": "Angular", "svelte": "Svelte", "tailwindcss": "Tailwind CSS", "typescript": "TypeScript", "mongoose": "MongoDB (Mongoose)"}
            for dependency, label in mapping.items():
                if dependency in names:
                    evidence.append({"name": label, "file": path, "reason": f"Declared dependency: {dependency}"})
            evidence.append({"name": "Node.js ecosystem", "file": path, "reason": "package.json present"})
        elif filename in {"requirements.txt", "pyproject.toml", "Pipfile"}:
            for dependency, label in {"django": "Django", "flask": "Flask", "fastapi": "FastAPI", "pytest": "pytest", "sqlalchemy": "SQLAlchemy"}.items():
                if re.search(r'(?im)^\s*(?:["\[])?' + dependency + r'(?:["\]\s<>=!~;]|$)', content):
                    evidence.append({"name": label, "file": path, "reason": f"Dependency declaration: {dependency}"})
            evidence.append({"name": "Python", "file": path, "reason": "Python dependency manifest"})
        else:
            label = {"pubspec.yaml": "Dart", "Cargo.toml": "Rust", "go.mod": "Go", "composer.json": "PHP", "pom.xml": "Java / Maven", "build.gradle": "Gradle", "Gemfile": "Ruby", "Dockerfile": "Docker", ".gitlab-ci.yml": "GitLab CI"}.get(filename)
            if label:
                evidence.append({"name": label, "file": path, "reason": "Configuration file present"})
            if filename == "pubspec.yaml" and re.search(r"(?m)^\s*flutter:", content):
                evidence.append({"name": "Flutter", "file": path, "reason": "Flutter declaration"})
    return evidence


def audit_readme(text):
    # Example headings inside fenced code are not documentation sections.
    visible = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            run = marker.group(1)
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence) and not line[marker.end():].strip():
                fence = None
            continue
        if fence is None:
            visible.append(line)
    text = "\n".join(visible)
    checks = [
        ("Overview", bool(re.search(r"(?m)^#[ \t]+\S", text))),
        ("Installation / setup", bool(re.search(r"(?im)^#{2,6}[ \t]+.*\b(install\w*|setup|getting started|quick ?start)\b", text))),
        ("Usage / examples", bool(re.search(r"(?im)^#{2,6}[ \t]+.*\b(usage|examples?|how to use)\b", text))),
        ("Configuration", bool(re.search(r"(?im)^#{2,6}[ \t]+.*\b(config\w*|environment)\b", text))),
        ("License", bool(re.search(r"(?im)^#{2,6}[ \t]+.*\blicen[cs]e\b", text))),
        ("Contributing", bool(re.search(r"(?im)^#{2,6}[ \t]+.*\bcontribut\w*\b", text))),
    ]
    return [{"name": name, "passed": passed} for name, passed in checks]

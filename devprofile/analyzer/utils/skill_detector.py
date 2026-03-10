import json
import os


def load_tech_stack():

    path = os.path.join("analyzer", "data", "tech_stack.json")

    with open(path) as f:
        return json.load(f)


def detect_tech_stack(repo_languages, repos):

    tech_stack = load_tech_stack()

    detected = {
        "frontend": set(),
        "backend": set(),
        "database": set(),
        "devops": set(),
        "mobile": set()
    }

    # -----------------------------
    # Detect from languages
    # -----------------------------

    for lang in repo_languages:

        lang = lang.lower()

        for category, skills in tech_stack.items():

            skills_lower = [s.lower() for s in skills]

            if lang in skills_lower:
                detected[category].add(lang)

    # -----------------------------
    # Detect from repo names
    # -----------------------------

    for repo in repos:

        name = repo.get("name", "").lower()
        desc = (repo.get("description") or "").lower()

        text = name + " " + desc

        # Backend frameworks
        if "django" in text:
            detected["backend"].add("django")

        if "flask" in text:
            detected["backend"].add("flask")

        if "node" in text:
            detected["backend"].add("node")

        if "express" in text:
            detected["backend"].add("express")

        # Frontend frameworks
        if "react" in text:
            detected["frontend"].add("react")

        if "vue" in text:
            detected["frontend"].add("vue")

        if "next" in text:
            detected["frontend"].add("next.js")

        # Database
        if "mysql" in text:
            detected["database"].add("mysql")

        if "postgres" in text:
            detected["database"].add("postgresql")

        if "mongodb" in text:
            detected["database"].add("mongodb")

        # DevOps
        if "docker" in text:
            detected["devops"].add("docker")

        if "kubernetes" in text:
            detected["devops"].add("kubernetes")

    # Convert sets to lists (for Django template)
    for category in detected:
        detected[category] = list(detected[category])

    return detected
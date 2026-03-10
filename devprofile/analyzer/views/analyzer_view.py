from django.shortcuts import render
import requests
from django.core.cache import cache
from analyzer.utils.skill_detector import detect_tech_stack


def analyzer_home(request):

    # Support shared link
    if request.method == "GET":

        username = request.GET.get("user")

        if username:
            request.method = "POST"
            request.POST = request.POST.copy()
            request.POST["username"] = username

    data = None
    top_repos = []
    score = 0
    languages = {}
    language_stats = []
    tech_stack = {}
    level = "Beginner Developer"
    health = 0
    suggestions = []
    badges = []
    username = None
    error = None
    total_stars = 0

    if request.method == "POST":

        username = request.POST.get("username")

        if not username:
            return render(request, "analyzer/home.html")

        cache_key = f"github_{username}"
        cached = cache.get(cache_key)

        if cached:
            cached["username"] = username
            return render(request, "analyzer/home.html", cached)

        user_url = f"https://api.github.com/users/{username}"
        repo_url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"

        headers = {
            "Accept": "application/vnd.github+json"
        }

        try:

            user_res = requests.get(user_url, headers=headers, timeout=5)
            repo_res = requests.get(repo_url, headers=headers, timeout=5)

        except requests.exceptions.RequestException:

            error = "GitHub API not responding"
            return render(request, "analyzer/home.html", {"error": error})

        # ------------------------
        # USER DATA
        # ------------------------

        if user_res.status_code == 200:

            user_data = user_res.json()

            repos_count = user_data.get("public_repos", 0)
            followers = user_data.get("followers", 0)

            data = {
                "name": user_data.get("name"),
                "bio": user_data.get("bio"),
                "avatar": user_data.get("avatar_url"),
                "repos": repos_count,
                "followers": followers,
                "following": user_data.get("following"),
                "profile": user_data.get("html_url"),
            }

        else:

            error = "GitHub user not found"

        # ------------------------
        # REPOSITORIES
        # ------------------------

        if repo_res.status_code == 200:

            repos = repo_res.json()

            # Calculate total stars
            for repo in repos:
                total_stars += repo.get("stargazers_count", 0)

            # Sort repos
            repos_sorted = sorted(
                repos,
                key=lambda x: (x["stargazers_count"], x["updated_at"]),
                reverse=True
            )

            top_repos = repos_sorted[:5]

            repos = repos[:8]

            # Detect languages
            for repo in repos:

                lang = repo.get("language")

                if lang:
                    languages[lang] = languages.get(lang, 0) + 1

            # ------------------------
            # Language Percentage
            # ------------------------

            total_lang_repos = sum(languages.values())

            if total_lang_repos > 0:

                for lang, count in languages.items():

                    percent = round((count / total_lang_repos) * 100, 1)

                    language_stats.append({
                        "name": lang,
                        "count": count,
                        "percent": percent
                    })

            # ------------------------
            # Tech Stack Detection
            # ------------------------

            repo_languages = list(languages.keys())

            tech_stack = detect_tech_stack(repo_languages, repos)

        # ------------------------
        # Profile Score
        # ------------------------

        if data:

            repos_count = data["repos"]
            followers = data["followers"]

            score = min(100, repos_count * 2 + followers * 0.5 + total_stars * 0.5)

            # Developer Level

            if followers > 100000:
                level = "🏆 Legendary Developer"

            elif followers > 10000:
                level = "🔥 Expert Developer"

            elif repos_count >= 20 or followers > 1000:
                level = "🚀 Advanced Developer"

            elif repos_count >= 5:
                level = "⚡ Intermediate Developer"

            else:
                level = "🌱 Beginner Developer"

            # Profile Health

            health = 0

            health += min(40, repos_count * 2)
            health += min(20, followers)

            if data.get("bio"):
                health += 20

            if len(languages) >= 3:
                health += 20

            health = min(100, health)

            # Suggestions

            if repos_count < 5:
                suggestions.append("Add more repositories")

            if followers < 10:
                suggestions.append("Increase followers by sharing projects")

            if not data.get("bio"):
                suggestions.append("Add a profile bio")

            if len(languages) < 3:
                suggestions.append("Use more programming languages")

            # Badges

            if repos_count > 10:
                badges.append("🚀 Project Builder")

            if followers > 10:
                badges.append("🌍 Community Member")

            if len(languages) > 3:
                badges.append("🧠 Polyglot Developer")

        # ------------------------
        # Context
        # ------------------------

        context = {
            "data": data,
            "top_repos": top_repos,
            "score": score,
            "languages": languages,
            "language_stats": language_stats,
            "tech_stack": tech_stack,
            "level": level,
            "username": username,
            "health": health,
            "suggestions": suggestions,
            "badges": badges,
            "error": error,
        }

        cache.set(cache_key, context, 600)

        return render(request, "analyzer/home.html", context)

    return render(request, "analyzer/home.html")
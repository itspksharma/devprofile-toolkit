"""Portable Markdown templates. No arbitrary HTML is generated from form values."""
import re
from urllib.parse import quote


def inline(value):
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    return re.sub(r"([\\`*_{}\[\]<>()#!|])", r"\\\1", value)


def link(label, url):
    return f"[{inline(label)}](<{str(url).replace('>', '%3E').replace('<', '%3C')}>)"


def code_block(text):
    longest = max((len(match) for match in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}shell\n{text.strip()}\n{fence}"


def generate_readme(data):
    sections = []
    kind = data.get("document_type", "profile")
    template = data.get("template", "professional")
    name = inline(data.get("name"))
    if data.get("banner_url") and data.get("show_banner"):
        sections.append("!" + link("Project banner", data["banner_url"]))
    title = f"# {name}"
    if kind == "profile" and template == "showcase":
        title = f"# Hello, I'm {name}"
    sections.append(title)
    if data.get("tagline"):
        sections.append(inline(data["tagline"]))
    headings = {"About": "About me" if kind == "profile" else "Overview", "Stack": "Technologies", "Projects": "Featured projects"}

    def section(title, content):
        if content and content.strip():
            sections.append(f"## {title}\n\n{content.strip()}")

    if data.get("show_about"):
        about = data.get("about", "").strip()
        if kind == "profile":
            extras = []
            if data.get("learning"):
                extras.append("- Currently learning: " + inline(data["learning"]))
            if data.get("future_goals"):
                extras.append("- Working toward: " + inline(data["future_goals"]))
            about = "\n\n".join(filter(None, [about, "\n".join(extras)]))
        section(headings["About"], about)
    if data.get("show_stack") and data.get("tech_stack"):
        items = [inline(s.strip()) for s in data["tech_stack"].split(",") if s.strip()]
        section(headings["Stack"], " · ".join(items) if template == "minimal" else "\n".join(f"- {s}" for s in items))
    if data.get("features") and kind != "profile":
        section("Features", "\n".join("- " + inline(line.lstrip("-• ")) for line in data["features"].splitlines() if line.strip()))
    if data.get("show_projects"):
        projects = data.get("projects_json", [])
        cards = []
        for project in projects:
            title = link(project["name"], project["url"]) if project.get("url") else inline(project["name"])
            card = f"### {title}"
            if project.get("description"):
                card += "\n\n" + inline(project["description"])
            if project.get("tech"):
                card += "\n\nTechnologies: " + inline(project["tech"])
            cards.append(card)
        section(headings["Projects"], "\n\n".join(cards))
    if kind != "profile":
        if data.get("installation"):
            section("Installation", code_block(data["installation"]))
        section("Usage / examples" if kind != "cli" else "Commands & examples", data.get("usage", ""))
        section("Configuration", data.get("configuration", ""))
        section("Contributing", data.get("contributing", ""))
        if data.get("license_name"):
            section("License", inline(data["license_name"]))
    if data.get("cert_name") and data.get("show_certifications"):
        section("Certifications", link(data["cert_name"], data["cert_link"]) if data.get("cert_link") else inline(data["cert_name"]))
    if data.get("show_contact"):
        contacts = []
        for key, label in [("repository", "Repository"), ("portfolio", "Website"), ("linkedin", "LinkedIn")]:
            if data.get(key):
                contacts.append(link(label, data[key]))
        if data.get("email"):
            contacts.append(link("Email", "mailto:" + data["email"]))
        if data.get("github"):
            contacts.append(link("GitHub", "https://github.com/" + data["github"]))
        section("Contact" if kind == "profile" else "Links", " · ".join(contacts))
    username = data.get("github")
    if username and kind == "profile":
        theme = quote(data.get("theme", "tokyonight"))
        username = quote(username)
        cards = []
        endpoints = [("show_stats", "GitHub statistics", f"https://github-readme-stats.vercel.app/api?username={username}&show_icons=true&theme={theme}"), ("show_langs", "GitHub languages", f"https://github-readme-stats.vercel.app/api/top-langs/?username={username}&layout=compact&theme={theme}"), ("show_streak", "GitHub streak", f"https://streak-stats.demolab.com?user={username}&theme={theme}"), ("show_graph", "GitHub activity", f"https://github-readme-activity-graph.vercel.app/graph?username={username}")]
        for enabled, label, url in endpoints:
            if data.get(enabled):
                cards.append("!" + link(label, url))
        section("GitHub activity", "\n\n".join(cards))
    separator = "\n\n---\n\n" if template == "showcase" else "\n\n"
    return separator.join(sections).strip() + "\n"

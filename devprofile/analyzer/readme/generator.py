def generate_readme(data):

    banner = data.get("banner_url", "")
    greeting = data.get("greeting", "")
    name = data.get("name", "")
    tagline = data.get("tagline", "")

    github = data.get("github", "")
    linkedin = data.get("linkedin", "")
    email = data.get("email", "")
    whatsapp = data.get("whatsapp", "")
    portfolio = data.get("portfolio", "")
    devto = data.get("devto", "")

    goal_quote = data.get("goal_quote", "")
    goal_desc = data.get("goal_desc", "")

    languages = data.get("languages", "")
    learning = data.get("learning", "")
    future_goals = data.get("future_goals", "")
    interests = data.get("interests", "")

    tech_stack = data.get("tech_stack", [])

    project_names = data.get("project_name", [])
    project_descs = data.get("project_desc", [])
    project_techs = data.get("project_tech", [])
    project_links = data.get("project_link", [])

    cert_name = data.get("cert_name", "")
    cert_link = data.get("cert_link", "")

    website = data.get("website", "")
    contact_email = data.get("contact_email", "")
    contact_linkedin = data.get("contact_linkedin", "")

    theme = data.get("theme", "gruvbox")

    show_banner = data.get("show_banner")
    show_greeting = data.get("show_greeting")
    show_about = data.get("show_about")
    show_projects = data.get("show_projects")
    show_stack = data.get("show_stack")
    show_certifications = data.get("show_certifications")
    show_contact = data.get("show_contact")
    show_stats = data.get("show_stats")
    show_langs = data.get("show_langs")
    show_streak = data.get("show_streak")
    show_graph = data.get("show_graph")

    readme = ""

    # Banner
    if banner and show_banner:
        readme += f"""
<p align="center">
<img src="{banner}" width="100%" />
</p>
"""

    # Greeting
    if greeting and show_greeting:
        readme += f'\n<h1 align="center">{greeting}</h1>\n'

    if name:
        readme += f'\n<h1 align="center">I\'m {name}</h1>\n'

    if tagline:
        readme += f'\n<h3 align="center">{tagline}</h3>\n'

    # Social Links
    badges = ""

    if github:
        badges += f'[![GitHub](https://img.shields.io/github/followers/{github}?style=social)](https://github.com/{github}) '

    if linkedin:
        badges += f'[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue?logo=linkedin)]({linkedin}) '

    if email:
        badges += f'[![Gmail](https://img.shields.io/badge/Gmail-red?logo=gmail)](mailto:{email}) '

    if whatsapp:
        badges += f'[![WhatsApp](https://img.shields.io/badge/WhatsApp-25D366?logo=whatsapp)](https://wa.me/{whatsapp}) '

    if portfolio:
        badges += f'[![Portfolio](https://img.shields.io/badge/Portfolio-black)]({portfolio}) '

    if devto:
        badges += f'[![Dev.to](https://img.shields.io/badge/Dev.to-black)]({devto}) '

    if badges:
        readme += f"\n<p align='center'>\n{badges}\n</p>\n"

    if github:
        readme += f"""
    <p align="center">
    <img src="https://komarev.com/ghpvc/?username={github}&label=Profile%20views&color=0e75b6&style=flat" />
    </p>
    """

    # Goal
    if goal_quote or goal_desc:
        readme += "\n---\n\n### 🎯 Goal\n"

        if goal_quote:
            readme += f"\n**{goal_quote}**\n"

        if goal_desc:
            readme += f"\n{goal_desc}\n"

    # About Me
    if (languages or learning or interests) and show_about:

        readme += "\n---\n\n### 🧠 About Me\n\n```js\n"

        readme += "const developer = {\n"

        if languages:
            langs = [x.strip() for x in languages.split(",")]
            readme += f'  code: {langs},\n'

        if learning:
            learn = [x.strip() for x in learning.split(",")]
            readme += f'  learning: {learn},\n'

        if future_goals:
            readme += f'  futureGoals: ["{future_goals}"],\n'

        if interests:
            readme += f'  interests: ["{interests}"],\n'

        readme += "};\n```\n"

    # Projects
    if any(project_names) and show_projects:

        readme += "\n---\n\n## 🚀 Highlight Projects\n\n"

        readme += "| Project | Description | Tech | Link |\n"
        readme += "|--------|-------------|------|------|\n"

        for i in range(len(project_names)):

            name = project_names[i]
            desc = project_descs[i]
            tech = project_techs[i]
            link = project_links[i]

            if name:

                readme += f"| {name} | {desc} | {tech} | [Visit]({link}) |\n"
    # Tech Stack
    if tech_stack and show_stack:

        icons = ",".join(tech_stack)

        readme += "\n---\n\n### 🛠️ Tech Stack\n\n"

        readme += f'<p align="center">\n<img src="https://skillicons.dev/icons?i={icons}" />\n</p>\n'

    # GitHub Stats
    if github:

        readme += "\n---\n\n## 📊 GitHub Stats\n\n"

        if show_langs:
            readme += f'![Top Langs](https://github-readme-stats.vercel.app/api/top-langs/?username={github}&theme={theme})\n'

        if show_streak:
            readme += f'![Streak](https://streak-stats.demolab.com?user={github}&theme={theme})\n'

        if show_stats:
            readme += f'![Stats](https://github-readme-stats.vercel.app/api?username={github}&show_icons=true&theme={theme})\n'

        if show_graph:
            readme += f'![Graph](https://github-readme-activity-graph.vercel.app/graph?username={github}&theme={theme})\n'

    # Certifications
    if cert_name and show_certifications:

        readme += "\n---\n\n### 📜 Certifications\n"

        readme += f"- [{cert_name}]({cert_link})\n"

    # Contact
    if (website or contact_email or contact_linkedin) and show_contact:

        readme += "\n---\n\n### 📫 Contact\n\n"

    if website:

        if not website.startswith("http"):
            website = "https://" + website

        readme += f"🌐 Website: {website}\n\n"

        if contact_email:
            readme += f"📧 Email: {contact_email}\n\n"

        if contact_linkedin:
            readme += f"💼 LinkedIn: {contact_linkedin}\n\n"

    return readme
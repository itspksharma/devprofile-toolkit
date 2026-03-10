from django.shortcuts import render
from analyzer.readme.generator import generate_readme


def readme_generator(request):

    if request.method == "POST":

        data = {

            "banner_url": request.POST.get("banner_url"),
            "greeting": request.POST.get("greeting"),
            "name": request.POST.get("name"),
            "tagline": request.POST.get("tagline"),

            "github": request.POST.get("github"),
            "linkedin": request.POST.get("linkedin"),
            "email": request.POST.get("email"),
            "whatsapp": request.POST.get("whatsapp"),
            "portfolio": request.POST.get("portfolio"),
            "devto": request.POST.get("devto"),

            "goal_quote": request.POST.get("goal_quote"),
            "goal_desc": request.POST.get("goal_desc"),

            "languages": request.POST.get("languages"),
            "learning": request.POST.get("learning"),
            "future_goals": request.POST.get("future_goals"),
            "interests": request.POST.get("interests"),

            "tech_stack": request.POST.getlist("tech_stack"),

            "project_name": request.POST.getlist("project_name"),
            "project_desc": request.POST.getlist("project_desc"),
            "project_tech": request.POST.getlist("project_tech"),
            "project_link": request.POST.getlist("project_link"),

            "cert_name": request.POST.get("cert_name"),
            "cert_link": request.POST.get("cert_link"),

            "website": request.POST.get("website"),
            "contact_email": request.POST.get("contact_email"),
            "contact_linkedin": request.POST.get("contact_linkedin"),

            "theme": request.POST.get("theme"),

            "show_stats": request.POST.get("show_stats"),
            "show_langs": request.POST.get("show_langs"),
            "show_streak": request.POST.get("show_streak"),
            "show_graph": request.POST.get("show_graph"),
            "show_banner": request.POST.get("show_banner"),
            "show_greeting": request.POST.get("show_greeting"),
            "show_about": request.POST.get("show_about"),
            "show_projects": request.POST.get("show_projects"),
            "show_stack": request.POST.get("show_stack"),
            "show_certifications": request.POST.get("show_certifications"),
            "show_contact": request.POST.get("show_contact"),

            }

        readme = generate_readme(data)

        return render(request, "analyzer/readme_result.html", {
            "readme": readme
        })

    return render(request, "analyzer/readme_form.html")
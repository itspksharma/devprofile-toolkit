import json

from django import forms
from django.core.validators import URLValidator


class WebURLField(forms.URLField):
    default_validators = [URLValidator(schemes=["https", "http"])]


class ReadmeForm(forms.Form):
    document_type = forms.ChoiceField(label="README type", choices=[("profile", "Developer profile"), ("project", "Project"), ("library", "Library / package"), ("cli", "Command-line tool"), ("organization", "Organization")], initial="profile")
    template = forms.ChoiceField(choices=[("professional", "Professional"), ("minimal", "Minimal"), ("showcase", "Showcase")], initial="professional")
    name = forms.CharField(label="Name / project title", max_length=120, widget=forms.TextInput(attrs={"placeholder": "Your name or project name", "autocomplete": "name"}))
    tagline = forms.CharField(label="Short introduction", max_length=300, required=False, widget=forms.TextInput(attrs={"placeholder": "What you build, or what this project does"}))
    about = forms.CharField(label="Overview / about", max_length=6000, required=False, widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Describe the purpose, audience, and what makes it useful. Markdown is supported."}))
    banner_url = WebURLField(label="Banner image URL", required=False, max_length=1000, help_text="Use a public image URL, rather than SVG or HTML source.")
    github = forms.RegexField(label="GitHub username", regex=r"^[A-Za-z0-9][A-Za-z0-9-]{0,38}$", max_length=39, required=False, help_text="Used only for optional GitHub stats cards.")
    repository = WebURLField(label="Repository URL", required=False, max_length=1000)
    portfolio = WebURLField(label="Website / portfolio", required=False, max_length=1000)
    linkedin = WebURLField(label="LinkedIn URL", required=False, max_length=1000)
    email = forms.EmailField(label="Public contact email", required=False)
    tech_stack = forms.CharField(label="Technologies", max_length=1000, required=False, widget=forms.TextInput(attrs={"placeholder": "Python, Django, PostgreSQL"}), help_text="Separate technologies with commas.")
    learning = forms.CharField(label="Currently learning", max_length=500, required=False)
    future_goals = forms.CharField(label="Future goals", max_length=1000, required=False, widget=forms.Textarea(attrs={"rows": 2}))
    features = forms.CharField(label="Key features", max_length=4000, required=False, widget=forms.Textarea(attrs={"rows": 4, "placeholder": "One feature per line"}))
    installation = forms.CharField(label="Installation commands", max_length=4000, required=False, widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Commands verified for your project"}))
    usage = forms.CharField(label="Usage / examples", max_length=6000, required=False, widget=forms.Textarea(attrs={"rows": 4, "placeholder": "How to use the project; Markdown and fenced code are supported"}))
    configuration = forms.CharField(label="Configuration", max_length=4000, required=False, widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Environment variables and setup instructions; omit secret values"}))
    contributing = forms.CharField(label="Contribution guidelines", max_length=3000, required=False, widget=forms.Textarea(attrs={"rows": 3}))
    license_name = forms.CharField(label="License", max_length=120, required=False, help_text="Enter the license actually used by your project.")
    cert_name = forms.CharField(label="Certification name", max_length=200, required=False)
    cert_link = WebURLField(label="Certification URL", required=False, max_length=1000)
    theme = forms.ChoiceField(label="GitHub card theme", choices=[("tokyonight", "Tokyo Night"), ("dark", "Dark"), ("radical", "Radical"), ("gruvbox", "Gruvbox")], initial="tokyonight")
    projects_json = forms.CharField(required=False, widget=forms.HiddenInput, max_length=15000)
    show_banner = forms.BooleanField(label="Banner", required=False, initial=True)
    show_about = forms.BooleanField(label="About / overview", required=False, initial=True)
    show_projects = forms.BooleanField(label="Featured projects", required=False, initial=True)
    show_stack = forms.BooleanField(label="Technologies", required=False, initial=True)
    show_contact = forms.BooleanField(label="Contact links", required=False, initial=True)
    show_certifications = forms.BooleanField(label="Certification", required=False, initial=True)
    show_stats = forms.BooleanField(label="GitHub stats card", required=False)
    show_langs = forms.BooleanField(label="GitHub language card", required=False)
    show_streak = forms.BooleanField(label="GitHub streak card", required=False)
    show_graph = forms.BooleanField(label="GitHub activity graph", required=False)

    def clean_projects_json(self):
        try:
            projects = json.loads(self.cleaned_data.get("projects_json") or "[]")
        except (ValueError, TypeError):
            raise forms.ValidationError("Project data is invalid. Remove the affected project and try again.")
        if not isinstance(projects, list) or len(projects) > 12:
            raise forms.ValidationError("Add up to 12 projects.")
        cleaned = []
        for project in projects:
            if not isinstance(project, dict):
                raise forms.ValidationError("Project data is invalid.")
            item = {key: str(project.get(key, "")).strip() for key in ("name", "description", "tech", "url")}
            if any(len(value) > 1000 for value in item.values()):
                raise forms.ValidationError("Project fields must be 1,000 characters or fewer.")
            if not any(item.values()):
                continue
            if not item["name"]:
                raise forms.ValidationError("Each project needs a name.")
            if item["url"]:
                URLValidator(schemes=["https", "http"])(item["url"])
            cleaned.append(item)
        return cleaned

    def groups(self):
        definitions = [
            ("basics", "Start with the essentials", "Choose the document and give it a clear introduction.", ["document_type", "template", "name", "tagline", "about", "banner_url"]),
            ("links", "Your links", "Only add details you want to make public.", ["github", "repository", "portfolio", "linkedin", "email"]),
            ("stack", "Skills & direction", "Keep the focus on technologies you actually use.", ["tech_stack", "learning", "future_goals"]),
            ("details", "Project documentation", "Useful for projects, libraries, CLI tools, and organizations.", ["features", "installation", "usage", "configuration", "contributing", "license_name"]),
            ("projects", "Featured projects", "Add up to 12 projects. Each can link to any public repository, demo, or website.", []),
            ("certifications", "Certifications", "An optional credential with a public verification link.", ["cert_name", "cert_link"]),
            ("appearance", "Sections & cards", "Empty sections are omitted automatically. Stats cards work with GitHub usernames.", ["show_banner", "show_about", "show_projects", "show_stack", "show_contact", "show_certifications", "show_stats", "show_langs", "show_streak", "show_graph", "theme"]),
        ]
        return [{"id": key, "title": title, "description": description, "fields": [self[name] for name in names]} for key, title, description, names in definitions]

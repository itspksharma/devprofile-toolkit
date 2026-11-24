import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from analyzer.forms import ReadmeForm
from analyzer.readme.generator import generate_readme
from analyzer.services import AnalysisError, analyze


def readme_generator(request):
    imported = None
    error = None
    markdown = ""
    initial = {}
    if request.method == "GET" and request.GET.get("repository"):
        try:
            result = analyze(request.GET["repository"], request.GET.get("provider", "github"), True, True)
            inspection = result.get("inspection")
            if not inspection:
                raise AnalysisError("File inspection is unavailable. You can still fill in your README below.")
            initial = inspection["import_data"]
            imported = result["target"]
            if request.GET.get("existing") == "1":
                markdown = inspection["readme"]
                if not markdown:
                    error = "No readable root README was found. Start with the fields below."
        except AnalysisError as exc:
            error = str(exc)
    form = ReadmeForm(request.POST if request.method == "POST" else None, initial=initial)
    if request.method == "POST" and form.is_valid():
        markdown = generate_readme(form.cleaned_data)
    projects = request.POST.get("projects_json", "[]") if request.method == "POST" else "[]"
    try:
        projects = json.loads(projects)
        if not isinstance(projects, list):
            projects = []
    except (ValueError, TypeError):
        projects = []
    return render(request, "analyzer/readme_form.html", {"form": form, "markdown": markdown, "imported": imported, "error": error, "projects": projects})


@require_POST
def readme_preview(request):
    form = ReadmeForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"markdown": generate_readme(form.cleaned_data)})

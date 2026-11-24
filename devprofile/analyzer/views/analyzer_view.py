from django.http import JsonResponse
from django.shortcuts import render
from analyzer.services import AnalysisError, analyze
from analyzer.archive import analyze_archive


def analyzer_home(request):
    source = request.POST if request.method == "POST" else request.GET
    target = source.get("target", source.get("user", "")).strip()
    provider = source.get("provider", "github")
    context = {"target": target, "provider": provider, "include_forks": source.get("include_forks") == "on", "include_archived": source.get("include_archived") == "on"}
    if request.method == "POST" and request.FILES.get("archive"):
        try:
            context["result"] = analyze_archive(request.FILES["archive"])
            context["provider"] = "archive"
        except AnalysisError as exc:
            context["error"] = str(exc)
    elif target:
        try:
            context["result"] = analyze(target, provider, context["include_forks"], context["include_archived"])
            if source.get("format") == "json":
                response = JsonResponse(context["result"], json_dumps_params={"indent": 2})
                response["Content-Disposition"] = 'attachment; filename="repository-analysis.json"'
                return response
        except AnalysisError as exc:
            context["error"] = str(exc)
    elif request.method == "POST":
        context["error"] = "Enter a username or repository URL to begin."
    return render(request, "analyzer/home.html", context)

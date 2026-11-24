import base64
import io
import json
import zipfile
from unittest.mock import Mock, patch

import requests
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from .archive import analyze_archive
from .forms import ReadmeForm
from .readme.generator import generate_readme
from .services import AnalysisError, Provider, analyze, parse_target
from .utils.skill_detector import audit_readme, detect_evidence


def github_repo(name="owner/project", **changes):
    return {"full_name": name, "html_url": "https://github.com/" + name, "description": "Example", "stargazers_count": 4, "pushed_at": "2026-11-01T00:00:00Z", "default_branch": "main", "language": "Python", **changes}


def zip_upload(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return SimpleUploadedFile("source.zip", buffer.getvalue(), content_type="application/zip")


class InputTests(SimpleTestCase):
    def test_github_clone_url(self):
        self.assertEqual(parse_target("https://github.com/owner/project.git", "github"), "owner/project")

    def test_gitlab_subgroups(self):
        self.assertEqual(parse_target("https://gitlab.com/group/sub/project/", "gitlab"), "group/sub/project")

    def test_invalid_paths(self):
        for target in ("https://evil.example/x", "http://github.com/a/b", "https://github.com@localhost/a", "../a", "a/../b", "a/b?x=y", "a/%2f", "a//b", "https://github.com/a/b?x=y"):
            with self.subTest(target=target), self.assertRaises(AnalysisError):
                parse_target(target, "github")

    def test_invalid_provider(self):
        with self.assertRaises(AnalysisError):
            parse_target("user", "unsupported")


class ProviderTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    @patch.object(Provider, "get")
    def test_pagination_covers_more_than_one_hundred(self, get):
        get.side_effect = [{"name": "User", "html_url": "https://github.com/user"}, [github_repo(f"user/p{i}") for i in range(100)], [github_repo("user/last")]]
        result = analyze("user", "github")
        self.assertEqual(result["count"], 101)
        self.assertEqual(result["stars"], 404)
        self.assertEqual(result["language_counts"], [{"name": "Python", "count": 101}])
        self.assertTrue(result["complete"])
        self.assertEqual(get.call_args_list[-1].args[1]["page"], 2)

    @patch.object(Provider, "get")
    def test_profile_limit_is_explicit(self, get):
        get.side_effect = [{"html_url": "https://github.com/user"}] + [[github_repo(f"user/p{page}-{i}") for i in range(100)] for page in range(5)]
        result = analyze("user", "github")
        self.assertEqual(result["count"], 500)
        self.assertFalse(result["complete"])

    @patch.object(Provider, "get")
    def test_filtering_and_cache_are_independent(self, get):
        batch = [github_repo(), github_repo("owner/fork", fork=True), github_repo("owner/archive", archived=True)]
        get.side_effect = [{"html_url": "https://github.com/owner"}, batch, {"html_url": "https://github.com/owner"}, batch]
        self.assertEqual(analyze("owner", "github")["count"], 1)
        self.assertEqual(analyze("owner", "github", True, True)["count"], 3)
        self.assertEqual(analyze("owner", "github")["count"], 1)
        self.assertEqual(get.call_count, 4)

    @patch.object(Provider, "get")
    def test_gitlab_namespace_is_encoded(self, get):
        get.return_value = {"id": 4, "path_with_namespace": "group/sub/project", "visibility": "public", "web_url": "https://gitlab.com/group/sub/project"}
        api = Provider("gitlab")
        try:
            _, repos, _ = api.repositories("group/sub/project")
            self.assertEqual(get.call_args.args[0], "/projects/group%2Fsub%2Fproject")
            self.assertEqual(repos[0]["id"], 4)
        finally:
            api.session.close()

    @patch.object(Provider, "get")
    def test_gitlab_profile_uses_public_projects(self, get):
        get.side_effect = [[{"id": 7, "name": "Dev", "web_url": "https://gitlab.com/dev"}], []]
        result = analyze("dev", "gitlab")
        self.assertEqual(result["count"], 0)
        self.assertEqual(get.call_args.args[0], "/users/7/projects")
        self.assertEqual(get.call_args.args[1]["visibility"], "public")

    @patch.object(Provider, "get")
    def test_private_repository_is_rejected_even_with_token(self, get):
        get.return_value = github_repo(private=True)
        with self.assertRaisesMessage(AnalysisError, "Only public"):
            analyze("owner/project", "github")

    @patch.object(Provider, "inspect", side_effect=AnalysisError("Rate limit"))
    @patch.object(Provider, "get", return_value=github_repo())
    def test_inspection_failure_keeps_metadata(self, get, inspect):
        result = analyze("owner/project", "github")
        self.assertEqual(result["count"], 1)
        self.assertIsNone(result["inspection"])
        self.assertIn("Rate limit", result["warnings"][0])

    @patch.object(Provider, "get")
    def test_repository_files_and_language_bytes(self, get):
        content = json.dumps({"dependencies": {"react": "1"}})
        encode = lambda text: {"encoding": "base64", "content": base64.b64encode(text.encode()).decode()}
        get.side_effect = [[{"name": "README.md", "path": "README.md", "type": "file"}, {"name": "package.json", "path": "package.json", "type": "file"}], encode("# Example\n\n## Installation\n"), encode(content), {"JavaScript": 900, "CSS": 100}]
        api = Provider("github")
        try:
            scan = api.inspect(api.normalize(github_repo()))
            self.assertEqual(scan["languages"][0], {"name": "JavaScript", "percent": 90.0})
            self.assertTrue(any(e["name"] == "React" for e in scan["evidence"]))
            self.assertEqual(scan["readme_score"], 33)
            self.assertEqual(scan["import_data"]["installation"], "npm install")
        finally:
            api.session.close()

    @patch.object(Provider, "get")
    def test_gitlab_tree_and_file_endpoint(self, get):
        get.side_effect = [[{"name": "README.md", "path": "README.md", "type": "blob"}], {"encoding": "base64", "content": base64.b64encode(b"# Example").decode()}, {"Python": 100}]
        api = Provider("gitlab")
        try:
            scan = api.inspect({"id": 9, "name": "g/p", "url": "https://gitlab.com/g/p", "branch": "main", "description": "Example"})
            self.assertEqual(scan["readme"], "# Example")
            self.assertEqual(get.call_args_list[1].args[0], "/projects/9/repository/files/README.md")
        finally:
            api.session.close()

    @patch("analyzer.services.requests.Session")
    def test_provider_http_errors(self, session):
        for code, expected in [(404, "not found"), (429, "rate limit"), (403, "rate limit"), (401, "invalid"), (500, "unexpected"), (302, "unexpected")]:
            with self.subTest(code=code):
                session.return_value.get.return_value = Mock(status_code=code)
                api = Provider("github")
                with self.assertRaisesMessage(AnalysisError, expected):
                    api.get("/users/nope")
                self.assertFalse(session.return_value.get.call_args.kwargs["allow_redirects"])

    @patch("analyzer.services.requests.Session")
    def test_network_timeout(self, session):
        session.return_value.get.side_effect = requests.Timeout()
        with self.assertRaisesMessage(AnalysisError, "could not be reached"):
            Provider("github").get("/users/example")


class ReadmeTests(SimpleTestCase):
    def cleaned(self, **values):
        form = ReadmeForm({"name": "Example", "document_type": "profile", "template": "professional", "theme": "dark", **values})
        self.assertTrue(form.is_valid(), form.errors)
        return form.cleaned_data

    def test_email_only_contact(self):
        text = generate_readme(self.cleaned(email="dev@example.com", show_contact="on"))
        self.assertIn("mailto:dev@example.com", text)

    def test_hidden_contact_hides_every_contact(self):
        text = generate_readme(self.cleaned(email="dev@example.com", portfolio="https://example.com", linkedin="https://linkedin.com/in/example"))
        self.assertNotIn("https://example.com", text)
        self.assertNotIn("mailto:", text)

    def test_no_empty_stats_heading(self):
        self.assertNotIn("## GitHub activity", generate_readme(self.cleaned(github="example")))

    def test_future_goals_without_other_about_fields(self):
        self.assertIn("Ship a library", generate_readme(self.cleaned(future_goals="Ship a library", show_about="on")))

    def test_project_doc_has_setup_and_no_github_cards(self):
        text = generate_readme(self.cleaned(document_type="project", installation="pip install sample", usage="Run the command", github="example", show_stats="on"))
        self.assertIn("## Installation", text)
        self.assertIn("```shell", text)
        self.assertNotIn("github-readme-stats", text)

    def test_html_title_and_markdown_in_project_name_are_escaped(self):
        text = generate_readme(self.cleaned(name="<img src=x onerror=alert(1)>", projects_json=json.dumps([{"name": "[bad](x)", "description": "a|b", "url": "https://example.com"}]), show_projects="on"))
        self.assertNotIn("# <img", text)
        self.assertIn(r"\[bad\]", text)

    def test_invalid_urls_and_project_payload(self):
        for values in [{"portfolio": "javascript:alert(1)"}, {"banner_url": "<svg>"}, {"projects_json": "{}"}, {"projects_json": json.dumps([{"name": "x", "url": "javascript:alert(1)"}])}, {"projects_json": json.dumps([{"name": "x"}] * 13)}]:
            with self.subTest(values=values):
                form = ReadmeForm({"name": "Example", "document_type": "profile", "template": "professional", "theme": "dark", **values})
                self.assertFalse(form.is_valid())

    def test_fence_cannot_be_closed_by_command(self):
        text = generate_readme(self.cleaned(document_type="cli", installation="echo '```'"))
        self.assertIn("````shell", text)

    def test_templates_change_output(self):
        minimal = generate_readme(self.cleaned(template="minimal", tech_stack="Python,Django", show_stack="on"))
        showcase = generate_readme(self.cleaned(template="showcase", tech_stack="Python,Django", show_stack="on"))
        self.assertIn("Python · Django", minimal)
        self.assertIn("Hello, I'm", showcase)
        self.assertIn("\n---\n", showcase)

    def test_audit_requires_headings(self):
        self.assertFalse(any(item["passed"] for item in audit_readme("installation usage license")))

    def test_audit_ignores_code_examples(self):
        checks = audit_readme("# Project\n\n```md\n## Installation\n## Usage\n```\n\n## License\n")
        self.assertEqual([c["name"] for c in checks if c["passed"]], ["Overview", "License"])

    def test_dependencies_are_not_inferred_from_descriptions(self):
        self.assertFalse(detect_evidence({"README.md": "This might use React and Django"}))
        self.assertTrue(any(e["name"] == "Django" for e in detect_evidence({"requirements.txt": "Django==6.0.3"})))


class ArchiveTests(SimpleTestCase):
    def test_nested_source_archive(self):
        result = analyze_archive(zip_upload({"project/README.md": "# Project\n\n## Usage\n", "project/backend/requirements.txt": "Django==6.0.3", "project/node_modules/package.json": "{}"}))
        scan = result["inspection"]
        self.assertIsNone(result["stars"])
        self.assertEqual(len(scan["files"]), 2)
        self.assertTrue(any(e["name"] == "Django" for e in scan["evidence"]))

    def test_unsafe_archive_is_rejected(self):
        for path in ("../README.md", "/README.md"):
            with self.subTest(path=path), self.assertRaises(AnalysisError):
                analyze_archive(zip_upload({path: "# Unsafe"}))

    def test_invalid_archive_is_rejected(self):
        with self.assertRaises(AnalysisError):
            analyze_archive(SimpleUploadedFile("bad.zip", b"not a zip"))

    def test_archive_entry_limit(self):
        with self.assertRaisesMessage(AnalysisError, "5,000"):
            analyze_archive(zip_upload({f"src/{i}.txt": "" for i in range(5001)}))

    def test_archive_symlink_is_rejected(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            info = zipfile.ZipInfo("README.md")
            info.create_system = 3
            info.external_attr = 0o120777 << 16
            archive.writestr(info, "/etc/passwd")
        with self.assertRaisesMessage(AnalysisError, "symbolic links"):
            analyze_archive(SimpleUploadedFile("source.zip", buffer.getvalue()))

    def test_oversized_archive_is_rejected(self):
        upload = SimpleUploadedFile("big.zip", b"x")
        upload.size = 11 * 1024 * 1024
        with self.assertRaisesMessage(AnalysisError, "10 MB"):
            analyze_archive(upload)


class ViewTests(SimpleTestCase):
    def test_home_and_studio_render(self):
        for url in ("/", "/analyzer/", "/readme/"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_invalid_provider_is_visible(self):
        response = self.client.get("/", {"target": "user", "provider": "wrong"})
        self.assertContains(response, "Choose GitHub or GitLab.")

    def test_preview_validates_and_generates(self):
        response = self.client.post("/readme/preview/", {"name": "Example", "document_type": "project", "template": "minimal", "theme": "dark"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["markdown"], "# Example\n")
        self.assertEqual(self.client.post("/readme/preview/", {}).status_code, 400)
        self.assertEqual(self.client.get("/readme/preview/").status_code, 405)

    def test_preview_rejects_cross_site_post(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/readme/preview/", {"name": "Example"}).status_code, 403)

    def test_uploaded_archive_renders_and_can_import_to_studio(self):
        response = self.client.post("/", {"archive": zip_upload({"README.md": "# Project"})})
        self.assertContains(response, "Uploaded source")
        self.assertContains(response, "Build a README")

    @patch("analyzer.views.analyzer_view.analyze")
    def test_json_export(self, analyze_mock):
        analyze_mock.return_value = {"target": "user", "count": 0}
        response = self.client.get("/", {"target": "user", "format": "json"})
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn("attachment", response["Content-Disposition"])

    @patch("analyzer.views.readme_view.analyze")
    def test_existing_readme_import_is_escaped_in_editor(self, analyze_mock):
        analyze_mock.return_value = {"target": "owner/project", "inspection": {"import_data": {"name": "Project", "document_type": "project"}, "readme": "# Original\n</textarea><script>alert(1)</script>"}}
        response = self.client.get("/readme/", {"provider": "github", "repository": "owner/project", "existing": "1"})
        self.assertContains(response, "# Original")
        self.assertNotContains(response, "</textarea><script>alert(1)</script>")

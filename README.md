# DevProfile Toolkit

Understand public GitHub and GitLab repositories, audit their documentation, and create a README that explains your work clearly.

Built with Django, Python, and a responsive HTML/CSS/JavaScript interface. No sign-in is required for public scans.

## Features

- **Two hosting providers:** GitHub and GitLab.com profiles and repository URLs, including GitLab subgroup paths.
- **Repository inspection:** root README and dependency files, file-backed technology findings, branch information, and provider language composition.
- **Transparent profile reports:** paginated owned repositories, fork/archive filters, stars, activity dates, and explicit scan coverage. No follower-based developer ratings.
- **Source ZIP analysis:** inspect source from other Git hosts or local projects without cloning or executing it. Includes nested dependency files.
- **README Studio:** developer profile, project, library, CLI, and organization documents; Minimal, Professional, and Showcase templates.
- **Editing tools:** sanitized live preview, manual Markdown editing, local Markdown import, browser draft saving/restoration, copy, and `README.md` download.
- **Repository import:** prefill a project document from detected metadata or open an existing root README for editing.
- **Readable themes:** separate app light/dark mode, preview colors, and GitHub stats-card themes; responsive mobile controls.
- **Report export:** shareable links and JSON for hosted public scans, plus browser print / Save as PDF.

## Run the existing project on Windows

The repository's existing virtual environment can be used without activation. In PowerShell:

```powershell
cd D:\Projects_Pro\github-profile-toolkit\devprofile
$env:DJANGO_DEBUG = "true"
..\venv\Scripts\python.exe manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Press **Ctrl+C** to stop the server.

## Fresh installation

Use Python 3.12 or newer. From the repository root in PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r .\devprofile\requirements.txt
cd devprofile
$env:DJANGO_DEBUG = "true"
..\venv\Scripts\python.exe manage.py migrate
..\venv\Scripts\python.exe manage.py runserver
```

On macOS or Linux, from the repository root:

```bash
python3 -m venv venv
./venv/bin/python -m pip install -r devprofile/requirements.txt
cd devprofile
export DJANGO_DEBUG=true
../venv/bin/python manage.py migrate
../venv/bin/python manage.py runserver
```

## Usage

### Analyze a profile or repository

Choose GitHub or GitLab. Enter a username, `owner/project` path, or an HTTPS repository URL. Pasting a recognized URL automatically selects its platform.

- A **profile scan** lists public owned repositories and summarizes metadata. For GitHub, primary-language counts describe repository counts, not bytes or skill. GitLab profile-level language totals are unavailable.
- A **repository scan** reads recognized root README/dependency files and retrieves provider language data. Click **Build a README** to import detected facts or **Edit existing README** to preserve the current document.
- For other Git hosts, expand **Analyze a source ZIP** and upload an exported source archive. Upload reports are not shareable and are not put into the shared provider cache.

JSON is available through the report's JSON button or `/?provider=github&target=owner/project&format=json`. Older `?user=username` links remain supported.

### Build a README

Open `/readme/`, choose a document type and template, then complete the fields. Empty optional sections are omitted. Profile documents support optional GitHub stats images; other document types support setup, usage, configuration, contribution, and license sections.

The **Markdown** tab allows direct edits. In manual mode, field changes preserve your Markdown; **Generate from fields** asks before replacing it. **Open .md file** imports up to 150 KB of existing Markdown. Restore a saved draft explicitly using **Restore draft**. Drafts remain in that browser's local storage; they do not sync across devices.

The preview is sanitized and approximates Markdown rendering. GitHub/GitLab control their final page appearance: arbitrary CSS backgrounds do not travel with a README. Stats images are optional third-party services and may be unavailable independently of this app.

## Analysis scope and limits

| Area | Coverage |
| --- | --- |
| Hosting | Public GitHub.com and GitLab.com resources only. No self-hosted API endpoints or private repositories. |
| Profiles | Up to 500 repositories, fetched in pages of 100. Reaching the cap marks the report partial. The UI shows the top 50 included projects; JSON contains the complete fetched subset. |
| Repository files | Root directory only; up to 12 recognized README/manifests, 150 KB each. GitHub root listing is limited by its contents endpoint; GitLab root listing is capped at 500 entries. |
| Recognized files | `package.json`, `requirements.txt`, `pyproject.toml`, `Pipfile`, `pubspec.yaml`, `Cargo.toml`, `go.mod`, `composer.json`, `pom.xml`, `build.gradle`, `Gemfile`, `Dockerfile`, `.gitlab-ci.yml`, and common root README names. |
| Technology detection | Conservative checks for declared dependencies and configuration files. Evidence is shown for each finding; declarations do not prove runtime use. |
| Language composition | GitHub language byte proportions or GitLab language percentages for an individual repository. No invented language totals for source ZIPs. |
| README audit | Six heading checks: title/overview, installation, usage, configuration, license, and contributing. The percentage describes structural coverage, not writing quality, working links, or command correctness. |
| Source ZIP | Up to 10 MB compressed, 50 MB declared uncompressed, and 5,000 entries. Reads up to 40 relevant files, prioritizing shallow paths. Dependencies/build directories are ignored. Unsafe paths, symlinks, and encrypted archives are rejected. |
| Timing and caching | Provider requests have timeouts and a bounded scan window. Public results are cached in-process for 10 minutes. Multiple server workers have independent caches. |

Source ZIPs provide a file snapshot, without Git history, stars, followers, or hosting activity. The application does not clone arbitrary URLs, execute project code, perform vulnerability scans, or assess developer competence. Nested manifests in hosted repositories currently require a source ZIP.

## Configuration

[.env.example](.env.example) lists supported variables. It is a reference: export values in the shell or hosting dashboard; `.env` files are not automatically loaded.

| Variable | Purpose |
| --- | --- |
| `DJANGO_DEBUG` | Set `true` only for local development. Defaults to `false`. |
| `DJANGO_SECRET_KEY` | Required in production. Generate a fresh random secret; the old committed development key is no longer used. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames. Defaults to loopback hosts only. Set your actual production hostname. |
| `GITHUB_TOKEN` | Optional server-side token for GitHub API requests. Use the minimum access needed for public resources. |
| `GITLAB_TOKEN` | Optional server-side token for GitLab API requests. Private repository scans are still rejected. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated HTTPS origins when required by your hosting setup. |
| `DJANGO_SECURE_SSL_REDIRECT` | Set `true` when production HTTPS routing is configured. |
| `DJANGO_TRUST_PROXY` | Set `true` only if your proxy strips untrusted forwarded headers and sets `X-Forwarded-Proto` correctly. |

To generate a production secret locally:

```powershell
.\venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Store that value in the deployment environment. If the previous committed key was used in a deployment, replace it there as well. Production cookies require HTTPS.

## Validation

From `devprofile` in PowerShell:

```powershell
$env:DJANGO_DEBUG = "true"
..\venv\Scripts\python.exe manage.py check
..\venv\Scripts\python.exe manage.py collectstatic --noinput
..\venv\Scripts\python.exe manage.py test --noinput
node --check static\analyzer\app.js
node --check static\analyzer\studio.js
```

The Python suite uses mocked provider responses to cover pagination, incomplete coverage, filters/cache separation, GitLab namespaces, file inspection, API failures, public-only access, archive validation, form validation, generation, imports, exports, and CSRF protection.

Static assets use WhiteNoise's manifest storage. Run `collectstatic` before tests or production startup. Preview libraries (Marked and DOMPurify) are bundled locally, with licenses, source maps, and source URLs/SHA-256 hashes in `devprofile/static/analyzer/vendor/manifest.json`. Font loading is optional and falls back to system fonts.

## Deployment

Keep the existing Django hosting setup. Set the required environment variables, install dependencies, collect static assets, and migrate before starting the WSGI application:

```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn devprofile.wsgi --timeout 60
```

Run these commands from the inner `devprofile` directory. The application uses synchronous provider requests; set worker capacity, request limits, and proxy upload limits to suit your hosting environment. GitHub/GitLab rate limits apply. No new hosting service is required.

## Troubleshooting

- **Missing secret at startup:** use `DJANGO_DEBUG=true` locally or set `DJANGO_SECRET_KEY` in production.
- **Disallowed host:** add the real hostname to `DJANGO_ALLOWED_HOSTS`; omit the scheme and path.
- **API limit or denied access:** try later or configure an appropriate server-side token. Errors retain a human-readable explanation; file-inspection failures can leave metadata available.
- **Empty results:** check the provider/path and whether fork/archive filters excluded the project. GitLab groups require a complete group/project path.
- **Missing styles / manifest error:** run `collectstatic` from the inner Django directory.
- **No preview:** static scripts may be blocked or missing. Markdown editing and downloads remain available when the preview libraries cannot load.
- **Missing ZIP findings:** check archive limits, ignored directories, unsupported manifests, and the scan notes.

## Project structure

```text
github-profile-toolkit/
├── README.md
├── .env.example
├── LICENSE
├── devprofile/
│   ├── manage.py
│   ├── requirements.txt
│   ├── devprofile/          # Django settings, URL routing, WSGI
│   ├── analyzer/
│   │   ├── services.py      # GitHub/GitLab API adapters and public scan cache
│   │   ├── archive.py       # Bounded source ZIP inspection
│   │   ├── forms.py         # README validation and form sections
│   │   ├── readme/          # Portable Markdown templates
│   │   ├── utils/           # File evidence and README checks
│   │   ├── views/           # Analyzer, studio, preview endpoint
│   │   └── tests.py
│   ├── templates/
│   └── static/analyzer/     # Themes, interactions, bundled preview libraries
└── screenshots/            # Original version screenshots; not current UI
```

## Contributing

Open an issue describing the behavior and expected outcome. Include regression coverage for analysis or generation changes, run the validation commands, and keep credentials outside version control. New providers should share the same report format and disclose unavailable metrics.

## License

MIT. See [LICENSE](LICENSE). Third-party preview libraries retain their bundled licenses.

Created by [Pawan Kumar Sharma](https://github.com/itspksharma).

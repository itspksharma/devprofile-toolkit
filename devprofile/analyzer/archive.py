"""Read bounded source archives in memory. Never extract or execute uploaded files."""
import re
import stat
import zipfile
import zlib
from pathlib import PurePosixPath

from django.utils import timezone

from .services import AnalysisError, MAX_FILE_BYTES, import_fields
from .utils.skill_detector import MANIFESTS, audit_readme, detect_evidence

MAX_UPLOAD = 10 * 1024 * 1024
MAX_UNPACKED = 50 * 1024 * 1024
IGNORED = {"node_modules", ".git", "venv", ".venv", "vendor", "__pycache__", "dist", "build"}


def analyze_archive(upload):
    if upload.size > MAX_UPLOAD:
        raise AnalysisError("Upload a source ZIP no larger than 10 MB.")
    try:
        with zipfile.ZipFile(upload) as archive:
            entries = archive.infolist()
            if len(entries) > 5000 or sum(entry.file_size for entry in entries) > MAX_UNPACKED:
                raise AnalysisError("Archive limit exceeded: use at most 5,000 entries and 50 MB of uncompressed content.")
            selected = []
            for entry in entries:
                path = PurePosixPath(entry.filename)
                if path.is_absolute() or re.match(r"^[a-zA-Z]:", entry.filename) or ".." in path.parts or "\\" in entry.filename or stat.S_ISLNK(entry.external_attr >> 16):
                    raise AnalysisError("The archive contains unsafe paths or symbolic links.")
                if entry.flag_bits & 1:
                    raise AnalysisError("Encrypted ZIP archives are not supported.")
                if entry.is_dir() or IGNORED.intersection(path.parts):
                    continue
                if path.name in MANIFESTS or re.fullmatch(r"readme(?:\.(md|markdown|rst|txt))?", path.name, re.I):
                    selected.append(entry)
            selected.sort(key=lambda entry: (len(PurePosixPath(entry.filename).parts), not PurePosixPath(entry.filename).name.lower().startswith("readme"), entry.filename))
            files = {}
            notes = ["Uploaded files are read in memory and are not extracted or executed. Git history and hosting metrics are unavailable."]
            if len(selected) > 40:
                notes.append("Only the first 40 README and dependency files were read, prioritizing paths nearest the root.")
            for entry in selected[:40]:
                if entry.file_size > MAX_FILE_BYTES:
                    notes.append(f"Skipped oversized file: {entry.filename}")
                    continue
                with archive.open(entry) as handle:
                    raw = handle.read(MAX_FILE_BYTES + 1)
                if len(raw) <= MAX_FILE_BYTES:
                    files[entry.filename] = raw.decode("utf-8", errors="replace")
            readme_name = next((path for path in files if PurePosixPath(path).name.lower().startswith("readme")), "")
            readme = files.get(readme_name, "")
            audit = audit_readme(readme)
            name = PurePosixPath(upload.name).stem[:120]
            repo = {"name": name, "description": "Uploaded source archive", "url": "", "branch": "Uploaded snapshot"}
            # Only root-relative files supply suggested setup commands.
            base = str(PurePosixPath(readme_name).parent) if readme_name else "."
            root_files = {PurePosixPath(path).name: text for path, text in files.items() if str(PurePosixPath(path).parent) == base}
            inspection = {"repository": repo, "files": list(files), "evidence": detect_evidence(files), "audit": audit, "readme": readme, "readme_name": readme_name, "readme_score": round(sum(c["passed"] for c in audit) / len(audit) * 100), "languages": [], "notes": notes, "import_data": import_fields(repo, root_files)}
            return {"provider": "archive", "target": name, "profile": {"name": name, "bio": "Source files from any Git host", "url": ""}, "count": 1, "fetched": 1, "stars": None, "complete": True, "scanned_at": timezone.now().isoformat(), "inspection": inspection, "repositories": [], "warnings": [], "language_counts": []}
    except (zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError, NotImplementedError, OSError, EOFError, zlib.error) as exc:
        raise AnalysisError("This ZIP could not be read. Upload a valid, unencrypted source archive.") from exc

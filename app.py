from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, List

from flask import Flask, abort, render_template, request, send_file, url_for
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.middleware.proxy_fix import ProxyFix

from pull_info import (
    build_dataframe,
    export_outputs,
    filter_students,
    parse_xml,
    setup_logging,
    summarize,
)
from stix_cleaner import (
    apply_updates,
    load_issues,
    load_stats,
    parse_tree,
    prepare_review,
    pretty_print_xml,
    write_tree,
)

BASE_DIR = Path(__file__).resolve().parent
JOBS_DIR = BASE_DIR / ".stix_ui" / "jobs"
ALLOWED_EXTENSIONS = {".xml"}
ALLOWED_INPUT_ROOTS = [BASE_DIR, Path.home(), Path("/tmp")]


def _get_script_prefix(environ: dict) -> str:
    script_name = environ.get("SCRIPT_NAME")
    if script_name:
        prefix = script_name.rstrip("/")
        if prefix and not prefix.startswith("/"):
            prefix = f"/{prefix}"
        return prefix

    header_prefixes = (
        "HTTP_X_FORWARDED_PREFIX",
        "HTTP_X_PROXY_CONTEXT_PATH",
        "HTTP_X_PROXYCONTEXTPATH",
        "HTTP_X_SCRIPT_NAME",
    )
    for key in header_prefixes:
        value = environ.get(key)
        if value:
            prefix = value.rstrip("/")
            if prefix and not prefix.startswith("/"):
                prefix = f"/{prefix}"
            return prefix

    env_prefix = os.environ.get("URL_PREFIX") or os.environ.get("SCRIPT_NAME")
    if env_prefix:
        prefix = env_prefix.rstrip("/")
        if prefix and not prefix.startswith("/"):
            prefix = f"/{prefix}"
        return prefix

    vscode_proxy = os.environ.get("VSCODE_PROXY_URI")
    if vscode_proxy:
        port = os.environ.get("PORT") or environ.get("SERVER_PORT") or ""
        resolved = vscode_proxy.replace("{{port}}", port).replace("{port}", port)
        try:
            from urllib.parse import urlparse

            proxy_path = urlparse(resolved).path.rstrip("/")
            if proxy_path:
                return proxy_path
        except Exception:
            pass

    nb_prefix = os.environ.get("NB_PREFIX")
    if nb_prefix:
        prefix = nb_prefix.rstrip("/")
        if prefix and not prefix.startswith("/"):
            prefix = f"/{prefix}"
        port = os.environ.get("PORT") or environ.get("SERVER_PORT")
        if port:
            return f"{prefix}/proxy/{port}"
        return prefix

    forwarded_uri = (
        environ.get("HTTP_X_FORWARDED_URI")
        or environ.get("HTTP_X_ORIGINAL_URI")
        or environ.get("HTTP_X_REQUEST_URI")
        or environ.get("REQUEST_URI")
        or environ.get("RAW_URI")
    )
    if forwarded_uri:
        path = forwarded_uri.split("?", 1)[0]
        path_info = environ.get("PATH_INFO", "")
        if path_info and path.endswith(path_info):
            prefix = path[: -len(path_info)].rstrip("/")
            if prefix and not prefix.startswith("/"):
                prefix = f"/{prefix}"
            return prefix
    return ""


def _get_max_content_length() -> int:
    raw_bytes = os.environ.get("MAX_CONTENT_LENGTH")
    if raw_bytes:
        try:
            value = int(raw_bytes)
            if value > 0:
                return value
        except ValueError:
            pass

    raw_mb = os.environ.get("MAX_CONTENT_LENGTH_MB")
    if raw_mb:
        try:
            mb = float(raw_mb)
            if mb > 0:
                return int(mb * 1024 * 1024)
        except ValueError:
            pass

    return 200 * 1024 * 1024


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_server_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (BASE_DIR / path).resolve()
    else:
        path = path.resolve()

    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Only .xml files are supported.")

    if not path.exists() or not path.is_file():
        raise ValueError("Server file path does not exist.")

    if not any(_is_within(path, root) for root in ALLOWED_INPUT_ROOTS):
        allowed = ", ".join(str(root) for root in ALLOWED_INPUT_ROOTS)
        raise ValueError(f"File must be within: {allowed}.")

    return path


class PrefixMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        prefix = _get_script_prefix(environ)
        if prefix:
            environ["SCRIPT_NAME"] = prefix
            path_info = environ.get("PATH_INFO", "")
            if path_info.startswith(prefix):
                environ["PATH_INFO"] = path_info[len(prefix) :] or "/"
        return self.app(environ, start_response)


app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "static"),
    template_folder=str(BASE_DIR / "templates"),
)
app.wsgi_app = PrefixMiddleware(app.wsgi_app)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
app.config["MAX_CONTENT_LENGTH"] = _get_max_content_length()


@app.errorhandler(RequestEntityTooLarge)
def handle_large_upload(error):
    max_bytes = app.config.get("MAX_CONTENT_LENGTH")
    if max_bytes:
        max_mb = max_bytes / 1024 / 1024
        message = (
            f"Upload exceeds the {max_mb:.0f} MB limit for this app. "
            "Try a smaller file or raise MAX_CONTENT_LENGTH_MB."
        )
    else:
        message = "Upload exceeds the configured size limit."
    return (
        render_template(
            "result.html",
            title="Upload too large",
            error=message,
            downloads=[],
            job_id="",
        ),
        413,
    )


@app.context_processor
def inject_url_prefix():
    prefix = _get_script_prefix(request.environ)
    return {"url_prefix": prefix}


def ensure_job_dir(job_id: str) -> Path:
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def get_job_dir(job_id: str) -> Path:
    job_dir = JOBS_DIR / job_id
    if not job_dir.exists():
        abort(404)
    return job_dir


def save_upload(file_storage, job_dir: Path) -> Path:
    original_name = Path(file_storage.filename or "").name
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Only .xml files are supported.")
    input_path = job_dir / "input.xml"
    file_storage.save(str(input_path))
    return input_path


def build_downloads(job_id: str, files: List[Dict[str, str]]) -> List[Dict[str, str]]:
    downloads = []
    for entry in files:
        downloads.append(
            {
                "label": entry["label"],
                "file": entry["file"],
                "url": url_for("download", job_id=job_id, filename=entry["file"]),
            }
        )
    return downloads


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/run")
def run():
    action = request.form.get("action", "clean")
    server_path = request.form.get("server_path", "").strip()
    job_id = uuid.uuid4().hex
    job_dir = ensure_job_dir(job_id)

    if server_path:
        try:
            input_path = _resolve_server_path(server_path)
        except ValueError as exc:
            return render_template(
                "result.html",
                title="Server path rejected",
                error=str(exc),
                downloads=[],
                job_id=job_id,
            ), 400
    else:
        uploaded = request.files.get("xml_file")
        if uploaded is None or uploaded.filename == "":
            return render_template(
                "result.html",
                title="No file provided",
                error="Please upload a .xml file or provide a server file path.",
                downloads=[],
                job_id=job_id,
            ), 400

        try:
            input_path = save_upload(uploaded, job_dir)
        except ValueError as exc:
            return render_template(
                "result.html",
                title="Upload rejected",
                error=str(exc),
                downloads=[],
                job_id=job_id,
            ), 400

    try:
        if action == "clean":
            auto_only = request.form.get("auto_only") == "on"
            issues, stats, auto_path = prepare_review(input_path, job_dir)

            if issues and not auto_only:
                street_issues = [i for i in issues if i.get("type") == "street_number"]
                unit_issues = [i for i in issues if i.get("type") == "unit"]
                return render_template(
                    "review.html",
                    job_id=job_id,
                    stats=stats,
                    street_issues=street_issues,
                    unit_issues=unit_issues,
                    total_issues=len(issues),
                )

            clean_path = job_dir / "clean.xml"
            shutil.copy2(auto_path, clean_path)
            downloads = build_downloads(
                job_id, [{"label": "Cleaned XML", "file": clean_path.name}]
            )
            return render_template(
                "result.html",
                title="Cleaned XML ready",
                message="Auto-clean finished. No review steps were required.",
                stats=stats,
                downloads=downloads,
                job_id=job_id,
            )

        if action == "export":
            export_format = request.form.get("export_format", "csv")
            setup_logging(job_dir / "pull_info.log", console=False)
            students = parse_xml(input_path)
            df = build_dataframe(students)
            summaries = summarize(df)
            df_filtered = filter_students(df)
            out_base = job_dir / "stix_export"
            export_outputs(df, df_filtered, summaries, out_base, excel=export_format == "excel")

            downloads: List[Dict[str, str]] = []
            if export_format == "excel":
                out_file = out_base.with_suffix(".xlsx")
                downloads.append({"label": "Excel workbook", "file": out_file.name})
            else:
                downloads.extend(
                    [
                        {
                            "label": "All students CSV",
                            "file": f"{out_base.name}_all_students.csv",
                        },
                        {
                            "label": "Filtered students CSV",
                            "file": f"{out_base.name}_filtered_students.csv",
                        },
                        {
                            "label": "School counts CSV",
                            "file": f"{out_base.name}_school_counts.csv",
                        },
                        {
                            "label": "Grade counts CSV",
                            "file": f"{out_base.name}_grade_counts.csv",
                        },
                    ]
                )

            stats = {
                "schools": int(df["SchoolName"].nunique()) if "SchoolName" in df else 0,
                "students": int(len(df)),
                "filtered_students": int(len(df_filtered)),
            }

            return render_template(
                "result.html",
                title="Export complete",
                message="Reports are ready for download.",
                stats=stats,
                downloads=build_downloads(job_id, downloads),
                job_id=job_id,
            )

        if action == "pretty":
            output_path = job_dir / "pretty.xml"
            pretty_print_xml(input_path, output_path)
            downloads = build_downloads(
                job_id, [{"label": "Pretty printed XML", "file": output_path.name}]
            )
            return render_template(
                "result.html",
                title="Pretty XML ready",
                message="Formatting complete.",
                downloads=downloads,
                job_id=job_id,
            )
    except Exception as exc:
        return render_template(
            "result.html",
            title="Workflow failed",
            error=str(exc),
            downloads=[],
            job_id=job_id,
        ), 500

    return render_template(
        "result.html",
        title="Unknown workflow",
        error="Choose a supported workflow and try again.",
        downloads=[],
    ), 400


@app.post("/review/<job_id>")
def review(job_id: str):
    job_dir = get_job_dir(job_id)
    issues = load_issues(job_dir)
    if not issues:
        return render_template(
            "result.html",
            title="Nothing to review",
            message="No pending fixes were found for this job.",
            downloads=[],
            job_id=job_id,
        )

    auto_path = job_dir / "auto_clean.xml"
    if not auto_path.exists():
        abort(404)

    tree = parse_tree(auto_path)
    applied = apply_updates(tree, issues, request.form)
    clean_path = job_dir / "clean.xml"
    write_tree(tree, clean_path)

    stats = load_stats(job_dir)
    stats.update(applied)

    downloads = build_downloads(
        job_id, [{"label": "Cleaned XML", "file": clean_path.name}]
    )

    return render_template(
        "result.html",
        title="Cleaned XML ready",
        message="Review updates applied.",
        stats=stats,
        downloads=downloads,
        job_id=job_id,
    )


@app.post("/review/<job_id>/skip")
def review_skip(job_id: str):
    job_dir = get_job_dir(job_id)
    auto_path = job_dir / "auto_clean.xml"
    if not auto_path.exists():
        abort(404)

    clean_path = job_dir / "clean.xml"
    shutil.copy2(auto_path, clean_path)
    stats = load_stats(job_dir)

    downloads = build_downloads(
        job_id, [{"label": "Cleaned XML", "file": clean_path.name}]
    )

    return render_template(
        "result.html",
        title="Cleaned XML ready",
        message="Auto-clean finished without manual edits.",
        stats=stats,
        downloads=downloads,
        job_id=job_id,
    )


@app.get("/download/<job_id>/<path:filename>")
def download(job_id: str, filename: str):
    job_dir = get_job_dir(job_id).resolve()
    file_path = (job_dir / filename).resolve()
    if job_dir not in file_path.parents or not file_path.exists():
        abort(404)
    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=debug)

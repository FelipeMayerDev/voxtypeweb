from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

import markdown as _md

from app.aliases import apply_aliases, get_aliases, set_alias
from app.cli import VoxtypeCliError
from app.cli import export as cli_export
from app.cli import read_markdown as cli_read_markdown
from app.config_service import ConfigError, read_config, write_config
from app.health import get_health
from app.read_model import get_meeting, get_speakers, list_meetings

router = APIRouter()
templates = Jinja2Templates(directory="templates")

_EXPORT_CONTENT_TYPES = {
    "text": "text/plain",
    "markdown": "text/markdown",
    "json": "application/json",
}
_EXPORT_EXTENSIONS = {"text": "txt", "markdown": "md", "json": "json"}


def _get_meeting_or_404(meeting_id: str):
    meeting = get_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


def _transcript_html(meeting_id: str) -> str:
    try:
        body = cli_read_markdown(meeting_id)
    except VoxtypeCliError:
        return ""
    if not body:
        return ""
    return _md.markdown(apply_aliases(body, get_aliases(meeting_id)))


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"meetings": list_meetings(), "health": get_health()}
    )


def _render_meeting(request: Request, meeting_id: str):
    meeting = _get_meeting_or_404(meeting_id)
    return templates.TemplateResponse(
        request,
        "meeting.html",
        {
            "meeting": meeting,
            "health": get_health(),
            "transcript_html": _transcript_html(meeting_id),
            "speakers": get_speakers(meeting_id),
            "aliases": get_aliases(meeting_id),
        },
    )


@router.get("/meetings/{meeting_id}", response_class=HTMLResponse)
def meeting_detail(request: Request, meeting_id: str):
    return _render_meeting(request, meeting_id)


@router.post("/meetings/{meeting_id}", response_class=HTMLResponse)
def meeting_set_alias(request: Request, meeting_id: str, speaker_id: str = Form(...), label: str = Form("")):
    _get_meeting_or_404(meeting_id)
    set_alias(meeting_id, speaker_id.strip(), label.strip())
    return RedirectResponse(url=f"/meetings/{meeting_id}", status_code=303)


@router.get("/meetings/{meeting_id}/transcript", response_class=HTMLResponse)
def meeting_transcript(request: Request, meeting_id: str):
    _get_meeting_or_404(meeting_id)
    return templates.TemplateResponse(
        request, "_transcript.html", {"transcript_html": _transcript_html(meeting_id)}
    )


@router.get("/meetings/{meeting_id}/export")
def meeting_export(meeting_id: str, format: str = "text"):
    if format not in _EXPORT_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown format: {format}")
    _get_meeting_or_404(meeting_id)
    try:
        content = cli_export(meeting_id, format)
    except VoxtypeCliError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    filename = f"{meeting_id}.{_EXPORT_EXTENSIONS[format]}"
    return Response(
        content=content,
        media_type=_EXPORT_CONTENT_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/config", response_class=HTMLResponse)
def config_get(request: Request):
    return templates.TemplateResponse(
        request, "config.html", {"content": read_config(), "error": None, "saved": False}
    )


@router.post("/config", response_class=HTMLResponse)
def config_post(request: Request, content: str = Form(...)):
    try:
        write_config(content)
    except ConfigError as exc:
        return templates.TemplateResponse(
            request, "config.html", {"content": content, "error": str(exc), "saved": False}
        )
    return templates.TemplateResponse(
        request, "config.html", {"content": read_config(), "error": None, "saved": True}
    )


@router.get("/health")
def health():
    return get_health()

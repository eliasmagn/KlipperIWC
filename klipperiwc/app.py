"""Application entrypoint for KlipperIWC."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from klipperiwc.api import (
    board_assets_router,
    boards_router,
    dashboard_router,
    definitions_router,
    status_router,
)
from klipperiwc.db import Base, engine
from klipperiwc.services import purge_history_before
from klipperiwc.websocket import router as websocket_router

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(title="KlipperIWC", description="Klipper Integration Web Console")

    static_root = Path(__file__).resolve().parent / "static"
    if static_root.exists():
        app.mount("/static", StaticFiles(directory=static_root), name="static")
    else:
        logger.warning("Static directory %s not found – skipping static mount.", static_root)

    Base.metadata.create_all(engine)

    retention_days = max(0, int(os.getenv("STATUS_HISTORY_RETENTION_DAYS", "30")))
    cleanup_interval = max(60, int(os.getenv("STATUS_HISTORY_CLEANUP_INTERVAL_SECONDS", "3600")))

    async def _cleanup_loop() -> None:
        while True:
            cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
            try:
                await asyncio.to_thread(purge_history_before, cutoff)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("Failed to purge history: %s", exc)
            await asyncio.sleep(cleanup_interval)

    @app.on_event("startup")
    async def _startup_cleanup_task() -> None:
        app.state.history_cleanup_task = asyncio.create_task(_cleanup_loop())

    @app.on_event("shutdown")
    async def _shutdown_cleanup_task() -> None:
        task: asyncio.Task | None = getattr(app.state, "history_cleanup_task", None)
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    app.include_router(status_router)
    app.include_router(board_assets_router)
    app.include_router(dashboard_router)
    app.include_router(boards_router)
    app.include_router(definitions_router)
    app.include_router(websocket_router)

    @app.get("/healthz")
    async def healthcheck() -> dict[str, str]:
        """Return a basic healthcheck payload."""
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    async def landing_page() -> str:
        """Serve a lightweight landing page that links the available designers."""

        return """
        <!DOCTYPE html>
        <html lang=\"en\">
        <head>
            <meta charset=\"utf-8\" />
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
            <title>KlipperIWC – Definition Studio</title>
            <style>
                :root {
                    color-scheme: dark;
                    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: radial-gradient(circle at top, #1e3a8a, #0f172a 55%);
                    color: #e2e8f0;
                }

                body {
                    margin: 0;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    background: linear-gradient(180deg, rgba(15, 23, 42, 0.95), rgba(2, 6, 23, 0.98));
                }

                header {
                    padding: 3.5rem 1.5rem 2.5rem;
                    text-align: center;
                }

                header h1 {
                    margin: 0;
                    font-size: clamp(2.1rem, 4vw, 3.3rem);
                    letter-spacing: -0.03em;
                }

                header p {
                    margin: 1rem auto 0;
                    max-width: 720px;
                    font-size: 1.05rem;
                    color: rgba(226, 232, 240, 0.85);
                    line-height: 1.6;
                }

                .actions {
                    margin-top: 2rem;
                    display: flex;
                    justify-content: center;
                    gap: 1rem;
                    flex-wrap: wrap;
                }

                .actions a {
                    display: inline-flex;
                    align-items: center;
                    gap: 0.5rem;
                    padding: 0.85rem 1.6rem;
                    border-radius: 999px;
                    font-weight: 600;
                    text-decoration: none;
                    color: #0f172a;
                    background: linear-gradient(135deg, #38bdf8, #22d3ee);
                    box-shadow: 0 12px 30px rgba(8, 145, 178, 0.28);
                    transition: transform 0.2s ease, box-shadow 0.2s ease;
                }

                .actions a.secondary {
                    background: rgba(226, 232, 240, 0.1);
                    color: #e2e8f0;
                    box-shadow: none;
                }

                .actions a.tertiary {
                    background: rgba(226, 232, 240, 0.06);
                    color: rgba(226, 232, 240, 0.95);
                    box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.4);
                }

                .actions a:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 18px 36px rgba(56, 189, 248, 0.32);
                }

                main {
                    flex: 1;
                    padding: 0 1.5rem 4rem;
                    display: grid;
                    gap: 2rem;
                    max-width: 1080px;
                    margin: 0 auto;
                }

                .card-grid {
                    display: grid;
                    gap: 1.5rem;
                    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                }

                .flow-steps {
                    display: grid;
                    gap: 1.2rem;
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                }

                .flow-step {
                    display: grid;
                    gap: 0.6rem;
                    padding: 1.6rem;
                    border-radius: 1.2rem;
                    background: rgba(15, 23, 42, 0.72);
                    border: 1px solid rgba(148, 163, 184, 0.25);
                    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 16px 36px rgba(8, 145, 178, 0.2);
                    position: relative;
                }

                .flow-step strong {
                    font-size: 1.5rem;
                    display: inline-flex;
                    align-items: center;
                    gap: 0.6rem;
                }

                .flow-step strong span {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 2.1rem;
                    height: 2.1rem;
                    border-radius: 999px;
                    background: linear-gradient(135deg, rgba(56, 189, 248, 0.85), rgba(14, 165, 233, 0.85));
                    color: #0f172a;
                    font-weight: 700;
                }

                .flow-step p {
                    margin: 0;
                    color: rgba(226, 232, 240, 0.85);
                    line-height: 1.55;
                }

                .flow-step a {
                    margin-top: 0.4rem;
                    justify-self: start;
                    color: #38bdf8;
                    font-weight: 600;
                    text-decoration: none;
                }

                .flow-step a[aria-disabled="true"] {
                    color: rgba(148, 163, 184, 0.6);
                    pointer-events: none;
                    cursor: not-allowed;
                }

                .flow-step a:hover:not([aria-disabled="true"]) {
                    text-decoration: underline;
                }

                .card {
                    padding: 1.8rem;
                    border-radius: 1.2rem;
                    background: rgba(15, 23, 42, 0.7);
                    border: 1px solid rgba(148, 163, 184, 0.2);
                    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05), 0 18px 40px rgba(2, 132, 199, 0.18);
                    display: flex;
                    flex-direction: column;
                    gap: 0.8rem;
                }

                .card h2 {
                    margin: 0;
                    font-size: 1.35rem;
                }

                .card p {
                    margin: 0;
                    color: rgba(226, 232, 240, 0.85);
                    line-height: 1.55;
                }

                .card ul {
                    margin: 0.5rem 0 0;
                    padding-left: 1.2rem;
                    color: rgba(148, 163, 184, 0.95);
                }

                .card a {
                    margin-top: auto;
                    color: #38bdf8;
                    text-decoration: none;
                    font-weight: 600;
                }

                .card a:hover {
                    text-decoration: underline;
                }

                section h3 {
                    margin: 0 0 0.8rem;
                    font-size: 1.1rem;
                    letter-spacing: 0.08em;
                    text-transform: uppercase;
                    color: rgba(148, 163, 184, 0.75);
                }

                footer {
                    padding: 2rem 1.5rem;
                    text-align: center;
                    color: rgba(148, 163, 184, 0.75);
                    font-size: 0.9rem;
                }

                @media (max-width: 720px) {
                    header {
                        padding: 2.8rem 1rem 2rem;
                    }

                    main {
                        padding: 0 1rem 3rem;
                    }
                }
            </style>
        </head>
        <body>
            <header>
                <h1>KlipperIWC Definition Studio</h1>
                <p>
                    Erstelle wiederverwendbare Board- und Druckerdefinitionen als Grundlage für individuelle
                    <code>klipper.conf</code>-Konfigurationen. Die Designer liefern angereicherte Visualisierungen,
                    die dauerhaft in der Datenbank abgelegt werden und später vom Konfigurations-Generator
                    bezogen werden können.
                </p>
                <div class=\"actions\">
                    <a href=\"#guidedFlow\" class=\"secondary\">Geführten Ablauf starten</a>
                    <a href=\"/board-designer\">Board-Designer öffnen →</a>
                    <a class=\"tertiary\" href=\"/printer-designer\">Direkt zum Drucker-Designer</a>
                </div>
            </header>

            <main>
                <section id=\"guidedFlow\">
                    <h3>Geführter Ablauf</h3>
                    <div class=\"flow-steps\">
                        <article class=\"flow-step\">
                            <strong><span>1</span>Board auswählen oder erstellen</strong>
                            <p>
                                Lade ein bestehendes Layout oder erstelle ein neues Board mit markierten Pins und Steckplätzen.
                                Die resultierende JSON-Struktur bildet die Basis für spätere Konfigurationen.
                            </p>
                            <a href=\"/board-designer\">Zum Board-Designer</a>
                        </article>
                        <article class=\"flow-step\">
                            <strong><span>2</span>Druckerhardware definieren</strong>
                            <p>
                                Beschreibe Mechanik, Hotend, Steuerung und Sensorik deines Druckers. Nutze Bild-Upload und 3D-
                                CAD-Vorschau, um Markierungen präzise zu platzieren.
                            </p>
                            <a href=\"/printer-designer\">Drucker-Designer öffnen</a>
                        </article>
                        <article class=\"flow-step\">
                            <strong><span>3</span>Konfiguration zusammenstellen</strong>
                            <p>
                                Kombiniere Board- und Druckerdefinitionen zu vollständigen <code>klipper.conf</code>-Profilen.
                                Der Assistent ist in Arbeit und wird in Kürze freigeschaltet.
                            </p>
                            <a href=\"#\" aria-disabled=\"true\">Konfigurator in Planung</a>
                        </article>
                    </div>
                </section>
                <section>
                    <h3>Designer-Übersicht</h3>
                    <div class=\"card-grid\">
                        <article class=\"card\">
                            <h2>Board-Designer</h2>
                            <p>Annotiere Pins, Anschlüsse und Zusatzressourcen auf Basis hochgeladener Bilder.</p>
                            <ul>
                                <li>Layer für Signal-, Strom- und Kommunikationspfade</li>
                                <li>Erzeuge klickbare Pin-Definitionen samt Zusatznotizen</li>
                                <li>Exportiere die Struktur als JSON für die Registry</li>
                            </ul>
                            <a href=\"/board-designer\">Zum Board-Designer</a>
                        </article>
                        <article class=\"card\">
                            <h2>Drucker-Designer</h2>
                            <p>Skizziere Achsen, Extruder, Sensoren und Elektronik in einer visuellen Ansicht.</p>
                            <ul>
                                <li>Mehrere Kinematik-Profile für CoreXY, Delta &amp; Kartesisch</li>
                                <li>Zuweisung von Controllern, Endstops und Zusatzmodulen</li>
                                <li>Speichere Varianten für Multi-Board-Setups</li>
                            </ul>
                            <a href=\"/printer-designer\">Zum Drucker-Designer</a>
                        </article>
                        <article class=\"card\">
                            <h2>Konfigurations-Generator</h2>
                            <p>Stelle Board- und Druckerdefinitionen zusammen, um konkrete Profile abzuleiten.</p>
                            <ul>
                                <li>Vorlagen für typische Hotends, Extruder und Peripherie</li>
                                <li>Generiert vollständige <code>printer.cfg</code>-Dateien</li>
                                <li>Versioniere Ergebnisse pro Projekt oder Benutzergruppe</li>
                            </ul>
                            <a href=\"#\">Konfigurator (in Planung)</a>
                        </article>
                    </div>
                </section>

                <section>
                    <h3>Dauerhafte Ablage</h3>
                    <div class=\"card\">
                        <p>
                            Jede Definition wird inkl. Metadaten, Vorschaubild und JSON-Datenstruktur dauerhaft gespeichert.
                            Über die neue API können Frontends oder Integrationen Definitionen anlegen, aktualisieren und
                            abrufen. Die Dokumente lassen sich optional freigeben, sobald eine Benutzerverwaltung hinzugefügt ist.
                        </p>
                        <ul>
                            <li><code>POST /api/definitions/boards</code> und <code>/printers</code> zum Anlegen</li>
                            <li><code>PUT /api/definitions/&lt;typ&gt;/{slug}</code> für Aktualisierungen</li>
                            <li><code>GET /api/definitions/&lt;typ&gt;</code> für globale Listen oder eigene Sammlungen</li>
                        </ul>
                    </div>
                </section>

                <section>
                    <h3>Ausblick</h3>
                    <div class=\"card\">
                        <p>
                            Als nächstes folgen Accounts mit freigabe-basiertem Teilen, suchbare Bibliotheken und ein
                            Konfigurations-Assistent, der Board- und Druckerdefinitionen kombiniert. Klipper selbst wird nicht
                            direkt gesteuert – stattdessen erzeugen wir geprüfte Konfigurationsdateien, die sicher importiert
                            werden können.
                        </p>
                    </div>
                </section>
            </main>

            <footer>
                © KlipperIWC – Visual Definitions for custom printer setups
            </footer>
        </body>
        </html>
        """

    @app.get("/board-designer", response_class=HTMLResponse)
    async def board_designer() -> str:
        """Return an interactive board designer prototype page."""

        return """
        <!DOCTYPE html>
        <html lang=\"en\">
        <head>
            <meta charset=\"utf-8\" />
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
            <title>KlipperIWC – Board Designer</title>
            <style>
                :root {
                    color-scheme: light dark;
                    font-family: system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif;
                    background: #111827;
                    color: #f9fafb;
                }

                body {
                    margin: 0;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    background: #0f172a;
                }

                .layout {
                    flex: 1;
                    display: grid;
                    grid-template-columns: minmax(280px, 320px) 1fr;
                    gap: 1.5rem;
                    padding: 1.5rem 1.8rem 2.2rem;
                }

                header {
                    grid-column: 1 / -1;
                    padding: 1.5rem 2rem 1rem;
                    border-bottom: 1px solid rgba(148, 163, 184, 0.3);
                    background: rgba(15, 23, 42, 0.9);
                    backdrop-filter: blur(12px);
                }

                header nav {
                    display: flex;
                    gap: 1rem;
                    margin-bottom: 0.8rem;
                }

                header nav a {
                    color: #38bdf8;
                    text-decoration: none;
                    font-weight: 600;
                }

                header nav a:hover {
                    text-decoration: underline;
                }

                header h1 {
                    margin: 0;
                    font-size: 1.8rem;
                }

                header p {
                    margin: 0.3rem 0 0;
                    color: #cbd5f5;
                    font-size: 0.95rem;
                }

                aside {
                    padding: 1.5rem;
                    border-radius: 1.1rem;
                    border: 1px solid rgba(148, 163, 184, 0.28);
                    background: rgba(15, 23, 42, 0.85);
                    backdrop-filter: blur(14px);
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                    box-shadow: 0 24px 48px rgba(15, 23, 42, 0.45);
                }

                main {
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                }

                .workspace-panel {
                    display: grid;
                    gap: 1.5rem;
                }

                .workspace-toggle {
                    display: inline-flex;
                    align-items: center;
                    gap: 0.4rem;
                    padding: 0.35rem;
                    border-radius: 999px;
                    border: 1px solid rgba(148, 163, 184, 0.35);
                    background: rgba(15, 23, 42, 0.6);
                    width: fit-content;
                }

                .workspace-toggle button {
                    border-radius: 999px;
                    padding: 0.45rem 1.35rem;
                    font-weight: 600;
                    background: transparent;
                    color: rgba(226, 232, 240, 0.82);
                    border: none;
                }

                .workspace-toggle button.active {
                    background: rgba(56, 189, 248, 0.18);
                    color: #38bdf8;
                    box-shadow: inset 0 0 0 1px rgba(56, 189, 248, 0.4);
                }

                .workspace-panel .plan-view {
                    display: none;
                }

                .workspace-panel .cad-panel {
                    display: none;
                }

                .workspace-panel[data-active-view="plan"] .plan-view {
                    display: block;
                }

                .workspace-panel[data-active-view="cad"] .cad-panel {
                    display: grid;
                }

                .toolbar {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.6rem;
                }

                button, select, input {
                    background: rgba(30, 41, 59, 0.8);
                    color: #e2e8f0;
                    border: 1px solid rgba(148, 163, 184, 0.4);
                    border-radius: 0.45rem;
                    padding: 0.5rem 0.9rem;
                    font-size: 0.95rem;
                    cursor: pointer;
                    transition: transform 0.1s ease, border-color 0.2s ease;
                }

                button.active {
                    border-color: #38bdf8;
                    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25);
                }

                button:hover, select:hover {
                    transform: translateY(-1px);
                    border-color: #38bdf8;
                }

                .canvas-shell {
                    flex: 1;
                    min-height: 60vh;
                    border-radius: 0.75rem;
                    border: 1px solid rgba(148, 163, 184, 0.3);
                    background: radial-gradient(circle at top, rgba(148, 163, 184, 0.08), rgba(15, 23, 42, 0.9));
                    position: relative;
                    overflow: hidden;
                }

                svg {
                    width: 100%;
                    height: 100%;
                    display: block;
                    background: repeating-linear-gradient(0deg, rgba(148, 163, 184, 0.08) 0, rgba(148, 163, 184, 0.08) 1px, transparent 1px, transparent 32px),
                        repeating-linear-gradient(90deg, rgba(148, 163, 184, 0.08) 0, rgba(148, 163, 184, 0.08) 1px, transparent 1px, transparent 32px);
                }

                .shape-label {
                    fill: #f1f5f9;
                    font-size: 13px;
                    text-shadow: 0 1px 2px rgba(15, 23, 42, 0.8);
                    pointer-events: none;
                }

                .shape-entry {
                    border-radius: 0.6rem;
                    border: 1px solid rgba(148, 163, 184, 0.2);
                    padding: 0.75rem;
                    background: rgba(30, 41, 59, 0.65);
                }

                .shape-entry h3 {
                    margin: 0 0 0.25rem;
                    font-size: 1rem;
                    color: #e2e8f0;
                }

                .shape-entry p {
                    margin: 0;
                    color: #cbd5f5;
                    font-size: 0.85rem;
                }

                .cad-panel {
                    display: grid;
                    gap: 1rem;
                    margin-top: 1.5rem;
                    padding: 1.5rem;
                    border-radius: 1rem;
                    border: 1px solid rgba(148, 163, 184, 0.25);
                    background: rgba(15, 23, 42, 0.82);
                    box-shadow: 0 24px 48px rgba(15, 23, 42, 0.55);
                }

                .cad-panel header {
                    display: grid;
                    gap: 0.4rem;
                }

                .cad-panel h2 {
                    margin: 0;
                    font-size: 1.25rem;
                    color: #f1f5f9;
                }

                .cad-panel p {
                    margin: 0;
                    font-size: 0.9rem;
                    color: rgba(148, 163, 184, 0.85);
                    line-height: 1.5;
                }

                .cad-toolbox {
                    display: grid;
                    gap: 0.75rem;
                }

                .cad-toolbox .row {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.75rem;
                }

                .cad-toolbox label {
                    display: flex;
                    flex-direction: column;
                    gap: 0.4rem;
                    font-size: 0.85rem;
                    color: rgba(226, 232, 240, 0.85);
                }

                .cad-toolbox input[type="file"] {
                    padding: 0.45rem;
                    background: rgba(30, 41, 59, 0.72);
                    border: 1px dashed rgba(56, 189, 248, 0.35);
                    border-radius: 0.6rem;
                    color: #e2e8f0;
                    cursor: pointer;
                }

                .cad-toolbox input[type="text"],
                .cad-toolbox select {
                    background: rgba(30, 41, 59, 0.65);
                    border: 1px solid rgba(148, 163, 184, 0.35);
                    border-radius: 0.6rem;
                    padding: 0.5rem 0.75rem;
                    color: #e2e8f0;
                    font-size: 0.95rem;
                }

                .cad-toolbox button {
                    background: rgba(30, 41, 59, 0.78);
                    border: 1px solid rgba(148, 163, 184, 0.35);
                    border-radius: 0.6rem;
                    padding: 0.5rem 0.9rem;
                    color: #e2e8f0;
                    font-weight: 600;
                    cursor: pointer;
                    transition: transform 0.12s ease, border-color 0.2s ease;
                }

                .cad-toolbox button:hover,
                .cad-toolbox button.active {
                    transform: translateY(-1px);
                    border-color: #38bdf8;
                    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25);
                }

                .cad-status {
                    font-size: 0.85rem;
                    color: rgba(148, 163, 184, 0.85);
                }

                .cad-status[data-state="error"] {
                    color: #fca5a5;
                }

                .cad-status[data-state="loading"] {
                    color: #fbbf24;
                }

                .cad-viewer {
                    position: relative;
                    min-height: 420px;
                    border-radius: 0.9rem;
                    border: 1px solid rgba(148, 163, 184, 0.2);
                    background: radial-gradient(circle at top, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95));
                    overflow: hidden;
                }

                .cad-viewer.drag-active {
                    border-color: #38bdf8;
                    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.35);
                }

                .cad-annotation-list {
                    display: grid;
                    gap: 0.6rem;
                }

                .cad-annotation-entry {
                    display: grid;
                    gap: 0.35rem;
                    padding: 0.75rem;
                    border-radius: 0.8rem;
                    border: 1px solid rgba(148, 163, 184, 0.25);
                    background: rgba(30, 41, 59, 0.72);
                }

                .cad-annotation-entry header {
                    display: flex;
                    justify-content: space-between;
                    gap: 0.5rem;
                    align-items: baseline;
                }

                .cad-annotation-entry h3 {
                    margin: 0;
                    font-size: 1rem;
                    color: #f8fafc;
                }

                .cad-annotation-entry span {
                    font-size: 0.75rem;
                    letter-spacing: 0.05em;
                    text-transform: uppercase;
                    color: rgba(56, 189, 248, 0.8);
                }

                .cad-annotation-entry button {
                    justify-self: start;
                }

                .hint {
                    font-size: 0.85rem;
                    color: #94a3b8;
                    margin-top: -0.3rem;
                }

                @media (max-width: 900px) {
                    .layout {
                        grid-template-columns: 1fr;
                        padding: 1.2rem;
                        gap: 1.2rem;
                    }

                    aside {
                        flex-direction: row;
                        flex-wrap: wrap;
                        gap: 1rem;
                        margin-bottom: 0.5rem;
                    }

                    .shape-entry {
                        flex: 1 1 200px;
                    }
                }
            </style>
        </head>
        <body>
            <header>
                <nav>
                    <a href=\"/\">← Landingpage</a>
                    <a href=\"/printer-designer\">Drucker-Designer</a>
                </nav>
                <h1>Board Designer Prototype</h1>
                <p>Create annotated board overlays before the user-generated workflow is available.</p>
            </header>
            <div class=\"layout\">
                <aside>
                    <div>
                        <h2>Workflow</h2>
                        <p class=\"hint\">Select a tool, drag on the canvas, then name the connector/pin.</p>
                        <div class=\"toolbar\">
                            <button id=\"rectTool\" type=\"button\">Rectangle</button>
                            <button id=\"circleTool\" type=\"button\">Circle</button>
                            <button id=\"panTool\" type=\"button\">Pan</button>
                            <input type=\"color\" id=\"colorPicker\" value=\"#38bdf8\" title=\"Highlight color\" />
                        </div>
                    </div>
                    <section>
                        <h2>Annotated Pins</h2>
                        <div id=\"shapeList\"></div>
                    </section>
                </aside>
                <main>
                    <section class=\"workspace-panel\" id=\"boardWorkspace\" data-active-view=\"plan\">
                        <div class=\"workspace-toggle\" role=\"tablist\" aria-label=\"Darstellungsmodus wählen\">
                            <button type=\"button\" class=\"active\" data-view-target=\"plan\" role=\"tab\" aria-selected=\"true\">2D-Layout</button>
                            <button type=\"button\" data-view-target=\"cad\" role=\"tab\" aria-selected=\"false\">3D-CAD</button>
                        </div>
                        <div class=\"plan-view\" data-view=\"plan\">
                            <div class=\"canvas-shell\">
                                <svg id=\"boardCanvas\" viewBox=\"0 0 1280 720\" role=\"img\" aria-label=\"Board designer canvas\"></svg>
                            </div>
                        </div>
                        <section class=\"cad-panel\" data-view=\"cad\">
                            <header>
                                <h2>3D CAD Explorer</h2>
                                <p>
                                    Lade eine STEP-Datei, um dein Board in 3D zu inspizieren, Komponenten zu markieren und die Perspektive
                                    frei zu bewegen. Ziehe die Datei per Drag &amp; Drop oder nutze den Dateiauswahldialog.
                                </p>
                            </header>
                            <div class=\"cad-toolbox\">
                                <div class=\"row\">
                                    <label>
                                        STEP-Datei laden
                                        <input id=\"boardCadFile\" type=\"file\" accept=\".step,.stp,model/step\" />
                                    </label>
                                    <label>
                                        Marker-Kategorie
                                        <select id=\"boardCadCategory\">
                                            <option value=\"device\">Gerät / Modul</option>
                                            <option value=\"rails\">Führungen &amp; Rails</option>
                                            <option value=\"belts\">Riemen &amp; Antriebe</option>
                                            <option value=\"cables\">Kabel &amp; Looms</option>
                                            <option value=\"sensors\">Sensoren</option>
                                            <option value=\"other\">Sonstige</option>
                                        </select>
                                    </label>
                                    <label>
                                        Marker-Beschriftung
                                        <input id=\"boardCadLabel\" type=\"text\" placeholder=\"z. B. X-Limit-Switch\" />
                                    </label>
                                </div>
                                <div class=\"row\">
                                    <button id=\"boardCadMarkerMode\" type=\"button\">Marker platzieren</button>
                                    <button id=\"boardCadResetView\" type=\"button\">Kamera zurücksetzen</button>
                                    <button id=\"boardCadClearMarkers\" type=\"button\">Marker entfernen</button>
                                </div>
                                <p class=\"cad-status\" id=\"boardCadStatus\" aria-live=\"polite\">
                                    Keine STEP-Datei geladen. Ziehe eine Datei auf die Ansicht oder verwende den Button.
                                </p>
                                <p class=\"hint\">
                                    Tipp: Im Marker-Modus mit einem Klick Punkte setzen. Außerhalb des Modus lässt sich das Modell per
                                    Linksklick drehen, mit Rechtsklick verschieben und mit dem Mausrad zoomen.
                                </p>
                            </div>
                            <div
                                class=\"cad-viewer\"
                                id=\"boardCadViewport\"
                                tabindex=\"0\"
                                aria-label=\"Interaktive 3D-Ansicht des Boards\"
                                data-max-pixel-ratio=\"1.5\"
                            ></div>
                            <section>
                                <h3>3D-Markierungen</h3>
                                <div id=\"boardCadAnnotationList\" class=\"cad-annotation-list\"></div>
                            </section>
                        </section>
                    </section>
                </main>
            </div>

            <script>
                const boardCanvas = document.getElementById('boardCanvas');
                const rectTool = document.getElementById('rectTool');
                const circleTool = document.getElementById('circleTool');
                const panTool = document.getElementById('panTool');
                const colorPicker = document.getElementById('colorPicker');
                const shapeList = document.getElementById('shapeList');
                const workspacePanel = document.getElementById('boardWorkspace');
                const viewToggleButtons = workspacePanel
                    ? workspacePanel.querySelectorAll('[data-view-target]')
                    : [];

                let activeTool = null;
                let drawing = false;
                let startPoint = { x: 0, y: 0 };
                let currentShape = null;
                let currentLabel = null;
                let viewBox = { x: 0, y: 0, width: 1280, height: 720 };
                let panStart = null;

                function setActiveTool(tool) {
                    activeTool = tool;
                    for (const button of [rectTool, circleTool, panTool]) {
                        button.classList.toggle('active', button.dataset.tool === tool);
                    }
                    boardCanvas.style.cursor = tool === 'pan' ? 'grab' : 'crosshair';
                }

                function svgCursor(event) {
                    const rect = boardCanvas.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) {
                        return null;
                    }

                    const touch = 'touches' in event && event.touches.length ? event.touches[0] : null;
                    const clientX = touch ? touch.clientX : event.clientX;
                    const clientY = touch ? touch.clientY : event.clientY;

                    if (typeof clientX !== 'number' || typeof clientY !== 'number') {
                        return null;
                    }

                    const normalizedX = (clientX - rect.left) / rect.width;
                    const normalizedY = (clientY - rect.top) / rect.height;

                    return {
                        x: viewBox.x + normalizedX * viewBox.width,
                        y: viewBox.y + normalizedY * viewBox.height
                    };
                }

                function addShapeEntry(id, type, label, color, geometry) {
                    const wrapper = document.createElement('article');
                    wrapper.className = 'shape-entry';
                    wrapper.innerHTML = `
                        <h3>${label}</h3>
                        <p><strong>Type:</strong> ${type}</p>
                        <p><strong>Color:</strong> ${color}</p>
                        <p><strong>Geometry:</strong> ${geometry}</p>
                    `;
                    wrapper.dataset.shapeId = id;
                    shapeList.appendChild(wrapper);
                }

                function promptForLabel(defaultValue) {
                    const result = prompt('Pin / connector label', defaultValue ?? '');
                    if (!result) {
                        return null;
                    }
                    return result.trim();
                }

                function createLabelElement(x, y, text) {
                    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    label.setAttribute('x', x);
                    label.setAttribute('y', y);
                    label.setAttribute('class', 'shape-label');
                    label.textContent = text;
                    return label;
                }

                function createShapeId() {
                    return `shape-${Math.random().toString(36).slice(2, 9)}`;
                }

                rectTool.dataset.tool = 'rect';
                circleTool.dataset.tool = 'circle';
                panTool.dataset.tool = 'pan';

                [rectTool, circleTool, panTool].forEach((button) => {
                    button.addEventListener('click', () => {
                        setActiveTool(button.dataset.tool);
                    });
                });

                setActiveTool('rect');

                if (workspacePanel && viewToggleButtons.length) {
                    viewToggleButtons.forEach((button) => {
                        button.addEventListener('click', () => {
                            const target = button.dataset.viewTarget;
                            if (!target) {
                                return;
                            }
                            workspacePanel.dataset.activeView = target;
                            viewToggleButtons.forEach((other) => {
                                const isActive = other === button;
                                other.classList.toggle('active', isActive);
                                other.setAttribute('aria-selected', String(isActive));
                            });
                            if (target === 'cad') {
                                window.setTimeout(() => {
                                    window.dispatchEvent(new Event('resize'));
                                }, 50);
                            }
                        });
                    });
                }

                boardCanvas.addEventListener('mousedown', (event) => {
                    const cursorPoint = svgCursor(event);
                    if (!cursorPoint) {
                        return;
                    }

                    if (activeTool === 'pan') {
                        panStart = { x: cursorPoint.x, y: cursorPoint.y, viewBox: { ...viewBox } };
                        boardCanvas.style.cursor = 'grabbing';
                        return;
                    }

                    drawing = true;
                    startPoint = { x: cursorPoint.x, y: cursorPoint.y };

                    const color = colorPicker.value;

                    if (activeTool === 'rect') {
                        currentShape = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                        currentShape.setAttribute('x', startPoint.x);
                        currentShape.setAttribute('y', startPoint.y);
                        currentShape.setAttribute('width', 1);
                        currentShape.setAttribute('height', 1);
                        currentShape.setAttribute('rx', 6);
                        currentShape.setAttribute('fill', `${color}33`);
                        currentShape.setAttribute('stroke', color);
                        currentShape.setAttribute('stroke-width', 2);
                        boardCanvas.appendChild(currentShape);
                    } else if (activeTool === 'circle') {
                        currentShape = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                        currentShape.setAttribute('cx', startPoint.x);
                        currentShape.setAttribute('cy', startPoint.y);
                        currentShape.setAttribute('r', 1);
                        currentShape.setAttribute('fill', `${color}33`);
                        currentShape.setAttribute('stroke', color);
                        currentShape.setAttribute('stroke-width', 2);
                        boardCanvas.appendChild(currentShape);
                    }
                });

                boardCanvas.addEventListener('mousemove', (event) => {
                    const cursorPoint = svgCursor(event);
                    if (!cursorPoint) {
                        return;
                    }

                    if (panStart && activeTool === 'pan') {
                        const dx = cursorPoint.x - panStart.x;
                        const dy = cursorPoint.y - panStart.y;

                        viewBox.x = panStart.viewBox.x - dx;
                        viewBox.y = panStart.viewBox.y - dy;
                        boardCanvas.setAttribute('viewBox', `${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`);
                        return;
                    }

                    if (!drawing || !currentShape) {
                        return;
                    }

                    const updatedPoint = cursorPoint;

                    if (activeTool === 'rect') {
                        const width = updatedPoint.x - startPoint.x;
                        const height = updatedPoint.y - startPoint.y;
                        currentShape.setAttribute('x', Math.min(startPoint.x, updatedPoint.x));
                        currentShape.setAttribute('y', Math.min(startPoint.y, updatedPoint.y));
                        currentShape.setAttribute('width', Math.abs(width));
                        currentShape.setAttribute('height', Math.abs(height));
                    } else if (activeTool === 'circle') {
                        const dx = updatedPoint.x - startPoint.x;
                        const dy = updatedPoint.y - startPoint.y;
                        const radius = Math.sqrt(dx * dx + dy * dy);
                        currentShape.setAttribute('r', radius);
                    }
                });

                window.addEventListener('mouseup', () => {
                    if (panStart) {
                        panStart = null;
                        boardCanvas.style.cursor = 'grab';
                        return;
                    }

                    if (!drawing || !currentShape) {
                        return;
                    }

                    drawing = false;

                    const color = colorPicker.value;
                    const shapeId = createShapeId();
                    currentShape.dataset.shapeId = shapeId;

                    if (activeTool === 'rect') {
                        const width = parseFloat(currentShape.getAttribute('width'));
                        const height = parseFloat(currentShape.getAttribute('height'));
                        if (width < 10 || height < 10) {
                            currentShape.remove();
                            currentShape = null;
                            return;
                        }
                    } else if (activeTool === 'circle') {
                        const radius = parseFloat(currentShape.getAttribute('r'));
                        if (radius < 8) {
                            currentShape.remove();
                            currentShape = null;
                            return;
                        }
                    }

                    const labelText = promptForLabel();
                    if (!labelText) {
                        currentShape.remove();
                        currentShape = null;
                        return;
                    }

                    let labelElement;
                    if (activeTool === 'rect') {
                        const x = parseFloat(currentShape.getAttribute('x'));
                        const y = parseFloat(currentShape.getAttribute('y'));
                        const width = parseFloat(currentShape.getAttribute('width'));
                        const height = parseFloat(currentShape.getAttribute('height'));
                        labelElement = createLabelElement(x + width / 2, y + height / 2, labelText);
                        labelElement.setAttribute('text-anchor', 'middle');
                        labelElement.setAttribute('dominant-baseline', 'middle');
                        boardCanvas.appendChild(labelElement);
                        addShapeEntry(
                            shapeId,
                            'Rectangle',
                            labelText,
                            color,
                            `x:${x.toFixed(1)}, y:${y.toFixed(1)}, w:${width.toFixed(1)}, h:${height.toFixed(1)}`
                        );
                    } else if (activeTool === 'circle') {
                        const cx = parseFloat(currentShape.getAttribute('cx'));
                        const cy = parseFloat(currentShape.getAttribute('cy'));
                        const radius = parseFloat(currentShape.getAttribute('r'));
                        labelElement = createLabelElement(cx, cy, labelText);
                        labelElement.setAttribute('text-anchor', 'middle');
                        labelElement.setAttribute('dominant-baseline', 'middle');
                        boardCanvas.appendChild(labelElement);
                        addShapeEntry(
                            shapeId,
                            'Circle',
                            labelText,
                            color,
                            `cx:${cx.toFixed(1)}, cy:${cy.toFixed(1)}, r:${radius.toFixed(1)}`
                        );
                    }

                    currentLabel = labelElement;
                    currentShape = null;
                });
            </script>
        <script src="/static/js/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/gh/kovacsv/occt-import-js@master/dist/occt-import-js.js" crossorigin="anonymous"></script>
        <script>
            (function () {
                const viewport = document.getElementById('boardCadViewport');
                const statusElement = document.getElementById('boardCadStatus');
                if (!viewport) {
                    return;
                }
            
                if (typeof THREE === 'undefined') {
                    if (statusElement) {
                        statusElement.textContent = '3D-Viewer konnte nicht initialisiert werden (THREE.js nicht verfügbar).';
                        statusElement.dataset.state = 'error';
                    }
                    return;
                }
            
                const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
                const pixelRatioCap = (() => {
                    const rawValue = viewport ? parseFloat(viewport.dataset.maxPixelRatio || '1.5') : NaN;
                    if (!Number.isFinite(rawValue) || rawValue <= 0) {
                        return 1.5;
                    }
                    return Math.max(0.5, rawValue);
                })();

                function getEffectivePixelRatio() {
                    const ratio = window.devicePixelRatio || 1;
                    return Math.min(ratio, pixelRatioCap);
                }

                renderer.setPixelRatio(getEffectivePixelRatio());
                renderer.setSize(viewport.clientWidth, viewport.clientHeight, false);
                renderer.outputEncoding = THREE.sRGBEncoding;
                viewport.appendChild(renderer.domElement);
            
                const scene = new THREE.Scene();
                scene.background = new THREE.Color(0x0f172a);
            
                const grid = new THREE.GridHelper(800, 40, 0x1f2937, 0x1f2937);
                if (Array.isArray(grid.material)) {
                    grid.material.forEach((material) => {
                        material.opacity = 0.25;
                        material.transparent = true;
                    });
                } else {
                    grid.material.opacity = 0.25;
                    grid.material.transparent = true;
                }
                scene.add(grid);
            
                const ambient = new THREE.HemisphereLight(0xf1f5f9, 0x0f172a, 0.9);
                const directional = new THREE.DirectionalLight(0xffffff, 0.75);
                directional.position.set(200, 320, 260);
                scene.add(ambient);
                scene.add(directional);
            
                const camera = new THREE.PerspectiveCamera(50, Math.max(viewport.clientWidth / Math.max(viewport.clientHeight, 1), 1), 0.1, 10000);
                camera.position.set(320, 220, 320);
                camera.lookAt(0, 0, 0);
            
                const raycaster = new THREE.Raycaster();
                const pointer = new THREE.Vector2();
            
                const annotationList = document.getElementById('boardCadAnnotationList');
                const fileInput = document.getElementById('boardCadFile');
                const categorySelect = document.getElementById('boardCadCategory');
                const labelInput = document.getElementById('boardCadLabel');
                const markerToggle = document.getElementById('boardCadMarkerMode');
                const resetViewButton = document.getElementById('boardCadResetView');
                const clearMarkersButton = document.getElementById('boardCadClearMarkers');
            
                const categoryPalette = {
                    device: '#38bdf8',
                    rails: '#22d3ee',
                    belts: '#f97316',
                    cables: '#facc15',
                    sensors: '#a855f7',
                    other: '#94a3b8'
                };
            
                const categoryLabels = {
                    device: 'Gerät / Modul',
                    rails: 'Führungen & Rails',
                    belts: 'Riemen & Antriebe',
                    cables: 'Kabel & Looms',
                    sensors: 'Sensor',
                    other: 'Sonstige'
                };
            
                let markerMode = false;
                let currentModel = null;
                let modelScale = 300;
                const annotations = [];
            
                const occtPromise = typeof occtimportjs === 'function' ? occtimportjs() : Promise.resolve(null);
            
                function updateStatus(message, state) {
                    if (!statusElement) {
                        return;
                    }
                    statusElement.textContent = message;
                    if (state) {
                        statusElement.dataset.state = state;
                    } else {
                        statusElement.removeAttribute('data-state');
                    }
                }
            
                updateStatus('Keine STEP-Datei geladen. Ziehe eine Datei auf die Ansicht oder verwende den Button.', null);
            
                function createSimpleOrbitControls(camera, domElement, options) {
                    const shouldHandlePointer = options && options.shouldHandlePointer ? options.shouldHandlePointer : () => true;
                    const state = {
                        pointerId: null,
                        rotating: false,
                        panning: false,
                        lastPosition: new THREE.Vector2(),
                        spherical: new THREE.Spherical(),
                        target: new THREE.Vector3()
                    };
                    const tempVec = new THREE.Vector3();
                    const xAxis = new THREE.Vector3();
                    const yAxis = new THREE.Vector3();
            
                    function syncSpherical() {
                        tempVec.copy(camera.position).sub(state.target);
                        state.spherical.setFromVector3(tempVec);
                    }
            
                    function apply() {
                        tempVec.setFromSpherical(state.spherical);
                        camera.position.copy(state.target).add(tempVec);
                        camera.lookAt(state.target);
                    }
            
                    syncSpherical();
                    apply();
            
                    function onPointerDown(event) {
                        if (!shouldHandlePointer(event)) {
                            return;
                        }
                        domElement.setPointerCapture(event.pointerId);
                        state.pointerId = event.pointerId;
                        state.lastPosition.set(event.clientX, event.clientY);
                        if (event.button === 2 || event.button === 1 || event.shiftKey) {
                            state.panning = true;
                            domElement.style.cursor = 'move';
                        } else {
                            state.rotating = true;
                            domElement.style.cursor = 'grabbing';
                        }
                    }
            
                    function onPointerMove(event) {
                        if (state.pointerId !== event.pointerId) {
                            return;
                        }
                        const deltaX = event.clientX - state.lastPosition.x;
                        const deltaY = event.clientY - state.lastPosition.y;
                        state.lastPosition.set(event.clientX, event.clientY);
                        if (state.rotating) {
                            const rotateSpeed = 0.005;
                            state.spherical.theta -= deltaX * rotateSpeed;
                            state.spherical.phi -= deltaY * rotateSpeed;
                            state.spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, state.spherical.phi));
                            apply();
                        } else if (state.panning) {
                            camera.updateMatrixWorld();
                            const panSpeed = 0.0015 * state.spherical.radius;
                            const panX = -deltaX * panSpeed;
                            const panY = deltaY * panSpeed;
                            xAxis.setFromMatrixColumn(camera.matrixWorld, 0);
                            yAxis.setFromMatrixColumn(camera.matrixWorld, 1);
                            state.target.addScaledVector(xAxis, panX);
                            state.target.addScaledVector(yAxis, panY);
                            apply();
                        }
                    }
            
                    function onPointerUp(event) {
                        if (state.pointerId !== event.pointerId) {
                            return;
                        }
                        domElement.releasePointerCapture(event.pointerId);
                        state.rotating = false;
                        state.panning = false;
                        domElement.style.cursor = markerMode ? 'crosshair' : 'grab';
                        state.pointerId = null;
                    }
            
                    function onWheel(event) {
                        event.preventDefault();
                        const delta = event.deltaY;
                        const factor = 1 + Math.min(Math.abs(delta) * 0.0015, 0.25);
                        if (delta > 0) {
                            state.spherical.radius *= factor;
                        } else {
                            state.spherical.radius /= factor;
                        }
                        state.spherical.radius = Math.max(5, Math.min(5000, state.spherical.radius));
                        apply();
                    }
            
                    domElement.addEventListener('pointerdown', onPointerDown);
                    domElement.addEventListener('pointermove', onPointerMove);
                    domElement.addEventListener('pointerup', onPointerUp);
                    domElement.addEventListener('pointercancel', onPointerUp);
                    domElement.addEventListener('wheel', onWheel, { passive: false });
            
                    return {
                        setTarget(target) {
                            state.target.copy(target);
                            syncSpherical();
                            apply();
                        },
                        setRadius(distance) {
                            state.spherical.radius = Math.max(5, distance);
                            apply();
                        },
                        refresh() {
                            syncSpherical();
                            apply();
                        }
                    };
                }
            
                const controls = createSimpleOrbitControls(camera, renderer.domElement, {
                    shouldHandlePointer(event) {
                        return !(markerMode && event.button === 0);
                    }
                });
            
                controls.setTarget(new THREE.Vector3(0, 0, 0));
                controls.setRadius(480);
            
                function resizeRenderer() {
                    const width = viewport.clientWidth;
                    const height = Math.max(viewport.clientHeight, 1);
                    renderer.setPixelRatio(getEffectivePixelRatio());
                    renderer.setSize(width, height, false);
                    camera.aspect = width / height;
                    camera.updateProjectionMatrix();
                }

                window.addEventListener('resize', resizeRenderer);
                if (window.ResizeObserver) {
                    new ResizeObserver(resizeRenderer).observe(viewport);
                }

                let pixelRatioQuery = null;

                function handlePixelRatioChange() {
                    setupPixelRatioObserver();
                    resizeRenderer();
                }

                function setupPixelRatioObserver() {
                    if (!window.matchMedia) {
                        return;
                    }
                    const ratio = Math.round((window.devicePixelRatio || 1) * 100) / 100;
                    const query = window.matchMedia(`(resolution: ${ratio}dppx)`);

                    if (pixelRatioQuery) {
                        if (pixelRatioQuery.removeEventListener) {
                            pixelRatioQuery.removeEventListener('change', handlePixelRatioChange);
                        } else if (pixelRatioQuery.removeListener) {
                            pixelRatioQuery.removeListener(handlePixelRatioChange);
                        }
                    }

                    pixelRatioQuery = query;

                    if (pixelRatioQuery.addEventListener) {
                        pixelRatioQuery.addEventListener('change', handlePixelRatioChange);
                    } else if (pixelRatioQuery.addListener) {
                        pixelRatioQuery.addListener(handlePixelRatioChange);
                    }
                }

                setupPixelRatioObserver();
                resizeRenderer();
            
                function clearAnnotations() {
                    while (annotations.length) {
                        const annotation = annotations.pop();
                        scene.remove(annotation.object3d);
                    }
                    if (annotationList) {
                        annotationList.innerHTML = '';
                    }
                }
            
                function setMarkerMode(enabled) {
                    markerMode = enabled;
                    if (markerToggle) {
                        markerToggle.classList.toggle('active', enabled);
                        markerToggle.textContent = enabled ? 'Marker-Modus aktiv' : 'Marker platzieren';
                    }
                    renderer.domElement.style.cursor = enabled ? 'crosshair' : 'grab';
                }
            
                setMarkerMode(false);
            
                function colorForCategory(category) {
                    return categoryPalette[category] || categoryPalette.other;
                }
            
                function labelForCategory(category) {
                    return categoryLabels[category] || category;
                }
            
                function createTextSprite(text, color) {
                    const canvas = document.createElement('canvas');
                    const context = canvas.getContext('2d');
                    const padding = 24;
                    const fontSize = 64;
                    context.font = `${fontSize}px Inter, sans-serif`;
                    const textWidth = context.measureText(text).width;
                    canvas.width = textWidth + padding * 2;
                    canvas.height = fontSize + padding * 1.5;
                    context.fillStyle = 'rgba(15, 23, 42, 0.9)';
                    context.strokeStyle = color;
                    context.lineWidth = 8;
                    context.fillRect(0, 0, canvas.width, canvas.height);
                    context.strokeRect(0, 0, canvas.width, canvas.height);
                    context.fillStyle = '#f8fafc';
                    context.textBaseline = 'middle';
                    context.font = `${fontSize}px Inter, sans-serif`;
                    context.fillText(text, padding, canvas.height / 2);
                    const texture = new THREE.CanvasTexture(canvas);
                    texture.minFilter = THREE.LinearFilter;
                    texture.encoding = THREE.sRGBEncoding;
                    const material = new THREE.SpriteMaterial({ map: texture, depthTest: false, depthWrite: false });
                    const sprite = new THREE.Sprite(material);
                    const scale = 0.0025 * modelScale;
                    sprite.scale.set(canvas.width * scale * 0.5, canvas.height * scale * 0.5, 1);
                    return sprite;
                }
            
                function addAnnotation(point) {
                    const category = categorySelect ? categorySelect.value : 'other';
                    const label = (labelInput && labelInput.value.trim()) || `${labelForCategory(category)} ${annotations.length + 1}`;
                    const color = colorForCategory(category);
                    const markerSize = Math.max(modelScale * 0.015, 2.5);
                    const markerGeometry = new THREE.SphereGeometry(markerSize, 24, 24);
                    const markerMaterial = new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.35, metalness: 0.15, roughness: 0.45 });
                    const sphere = new THREE.Mesh(markerGeometry, markerMaterial);
                    const sprite = createTextSprite(label, color);
                    sprite.position.set(0, markerSize * 3.2, 0);
                    const group = new THREE.Group();
                    group.add(sphere);
                    group.add(sprite);
                    group.position.copy(point);
                    scene.add(group);
            
                    const annotation = {
                        id: `cad-marker-${Math.random().toString(36).slice(2, 9)}`,
                        category,
                        label,
                        position: point.clone(),
                        object3d: group
                    };
                    annotations.push(annotation);
            
                    if (annotationList) {
                        const wrapper = document.createElement('article');
                        wrapper.className = 'cad-annotation-entry';
                        wrapper.dataset.annotationId = annotation.id;
                        wrapper.innerHTML = `
                            <header>
                                <h3>${label}</h3>
                                <span>${labelForCategory(category)}</span>
                            </header>
                            <p>Position: x=${point.x.toFixed(1)}, y=${point.y.toFixed(1)}, z=${point.z.toFixed(1)}</p>
                        `;
                        const removeButton = document.createElement('button');
                        removeButton.type = 'button';
                        removeButton.textContent = 'Entfernen';
                        removeButton.addEventListener('click', () => {
                            scene.remove(group);
                            const index = annotations.findIndex((item) => item.id === annotation.id);
                            if (index >= 0) {
                                annotations.splice(index, 1);
                            }
                            wrapper.remove();
                        });
                        wrapper.appendChild(removeButton);
                        annotationList.appendChild(wrapper);
                    }
                }
            
                function handleAnnotationEvent(event) {
                    if (!markerMode || !currentModel) {
                        return;
                    }
                    const rect = renderer.domElement.getBoundingClientRect();
                    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
                    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
                    raycaster.setFromCamera(pointer, camera);
                    const intersections = raycaster.intersectObject(currentModel, true);
                    if (intersections.length === 0) {
                        updateStatus('Kein Schnittpunkt gefunden. Bitte erneut versuchen.', 'error');
                        return;
                    }
                    updateStatus('Marker hinzugefügt.', null);
                    addAnnotation(intersections[0].point);
                }
            
                renderer.domElement.addEventListener('pointerdown', (event) => {
                    if (markerMode && event.button === 0) {
                        event.preventDefault();
                        handleAnnotationEvent(event);
                    }
                });
            
                renderer.domElement.addEventListener('contextmenu', (event) => event.preventDefault());
            
                function buildMeshGroup(result) {
                    const group = new THREE.Group();
                    if (!result || !result.success || !Array.isArray(result.meshes)) {
                        return group;
                    }
                    const meshes = result.meshes.map((meshData) => {
                        const geometry = new THREE.BufferGeometry();
                        const positions = meshData?.attributes?.position?.array || [];
                        const positionData = positions instanceof Float32Array ? positions : new Float32Array(positions);
                        geometry.setAttribute('position', new THREE.Float32BufferAttribute(positionData, 3));
                        const normals = meshData?.attributes?.normal?.array;
                        if (normals && normals.length) {
                            const normalData = normals instanceof Float32Array ? normals : new Float32Array(normals);
                            geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normalData, 3));
                        }
                        const indices = meshData?.index?.array;
                        if (indices && indices.length) {
                            const indexData =
                                indices instanceof Uint32Array ||
                                indices instanceof Uint16Array ||
                                indices instanceof Uint8Array
                                    ? indices
                                    : new Uint32Array(indices);
                            geometry.setIndex(indexData);
                        }
                        if (!normals || !normals.length) {
                            geometry.computeVertexNormals();
                        }
                        const colorArray = meshData?.color;
                        const color = Array.isArray(colorArray)
                            ? new THREE.Color(colorArray[0] / 255, colorArray[1] / 255, colorArray[2] / 255)
                            : new THREE.Color('#94a3b8');
                        const material = new THREE.MeshStandardMaterial({
                            color,
                            metalness: 0.15,
                            roughness: 0.75,
                            side: THREE.DoubleSide
                        });
                        const mesh = new THREE.Mesh(geometry, material);
                        mesh.name = meshData?.name || 'STEP Mesh';
                        return mesh;
                    });
            
                    function attachNode(node) {
                        const nodeGroup = new THREE.Group();
                        nodeGroup.name = node?.name || 'StepNode';
                        if (Array.isArray(node?.meshes)) {
                            node.meshes.forEach((index) => {
                                const mesh = meshes[index];
                                if (mesh) {
                                    nodeGroup.add(mesh.clone());
                                }
                            });
                        }
                        if (Array.isArray(node?.children)) {
                            node.children.forEach((child) => {
                                nodeGroup.add(attachNode(child));
                            });
                        }
                        return nodeGroup;
                    }
            
                    group.add(attachNode(result.root));
                    return group;
                }
            
                function fitCameraToGroup(group) {
                    const box = new THREE.Box3().setFromObject(group);
                    const center = box.getCenter(new THREE.Vector3());
                    const size = box.getSize(new THREE.Vector3());
                    const maxDim = Math.max(size.x, size.y, size.z, 1);
                    group.position.set(-center.x, -center.y, -center.z);
                    modelScale = maxDim;
                    controls.setTarget(new THREE.Vector3(0, 0, 0));
                    const distance = maxDim * 1.8;
                    controls.setRadius(distance);
                    camera.position.set(distance, distance * 0.7, distance);
                    camera.near = Math.max(0.1, distance / 400);
                    camera.far = Math.max(1000, distance * 20);
                    camera.updateProjectionMatrix();
                }
            
                async function loadStepFile(file) {
                    if (!file) {
                        return;
                    }
                    updateStatus(`Lade ${file.name} ...`, 'loading');
                    const occt = await occtPromise;
                    if (!occt) {
                        updateStatus('STEP-Parser nicht verfügbar.', 'error');
                        return;
                    }
                    try {
                        const buffer = await file.arrayBuffer();
                        const result = occt.ReadStepFile(new Uint8Array(buffer), null);
                        if (!result || !result.success) {
                            updateStatus('STEP-Datei konnte nicht gelesen werden.', 'error');
                            return;
                        }
                        if (currentModel) {
                            scene.remove(currentModel);
                        }
                        clearAnnotations();
                        currentModel = buildMeshGroup(result);
                        scene.add(currentModel);
                        fitCameraToGroup(currentModel);
                        updateStatus(`${file.name} geladen. Marker-Modus aktivieren, um Punkte zu setzen.`, null);
                    } catch (error) {
                        console.error(error);
                        updateStatus('Fehler beim Lesen der STEP-Datei.', 'error');
                    }
                }
            
                if (fileInput) {
                    fileInput.addEventListener('change', (event) => {
                        const file = event.target.files && event.target.files[0];
                        if (file) {
                            loadStepFile(file);
                        }
                    });
                }
            
                if (markerToggle) {
                    markerToggle.addEventListener('click', () => {
                        setMarkerMode(!markerMode);
                    });
                }
            
                if (clearMarkersButton) {
                    clearMarkersButton.addEventListener('click', () => {
                        clearAnnotations();
                        updateStatus('Alle Marker entfernt.', null);
                    });
                }
            
                if (resetViewButton) {
                    resetViewButton.addEventListener('click', () => {
                        if (currentModel) {
                            fitCameraToGroup(currentModel);
                        } else {
                            controls.setTarget(new THREE.Vector3(0, 0, 0));
                            controls.setRadius(480);
                            camera.position.set(320, 220, 320);
                            camera.updateProjectionMatrix();
                        }
                        updateStatus('Kamera zurückgesetzt.', null);
                    });
                }
            
                ['dragenter', 'dragover'].forEach((type) => {
                    viewport.addEventListener(type, (event) => {
                        event.preventDefault();
                        viewport.classList.add('drag-active');
                    });
                });
            
                ['dragleave', 'drop'].forEach((type) => {
                    viewport.addEventListener(type, (event) => {
                        event.preventDefault();
                        if (type === 'drop') {
                            const file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
                            if (file) {
                                loadStepFile(file);
                            }
                        }
                        viewport.classList.remove('drag-active');
                    });
                });
            
                function animate() {
                    requestAnimationFrame(animate);
                    renderer.render(scene, camera);
                }
            
                animate();
            })();
        </script>
        </body>
        </html>
        """

    @app.get("/printer-designer", response_class=HTMLResponse)
    async def printer_designer() -> str:
        """Return an interactive printer designer similar to the board designer."""

        return """
        <!DOCTYPE html>
        <html lang=\"en\">
        <head>
            <meta charset=\"utf-8\" />
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
            <title>KlipperIWC – Printer Designer</title>
            <style>
                :root {
                    color-scheme: dark;
                    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: #0f172a;
                    color: #e2e8f0;
                }

                body {
                    margin: 0;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    background: radial-gradient(circle at top right, rgba(59, 130, 246, 0.35), rgba(15, 23, 42, 0.94));
                }

                header {
                    padding: 1.6rem 2rem 1.2rem;
                    border-bottom: 1px solid rgba(148, 163, 184, 0.3);
                    background: rgba(15, 23, 42, 0.86);
                    backdrop-filter: blur(16px);
                }

                header nav {
                    display: flex;
                    gap: 1rem;
                    margin-bottom: 0.8rem;
                }

                header nav a {
                    color: #38bdf8;
                    text-decoration: none;
                    font-weight: 600;
                }

                header nav a:hover {
                    text-decoration: underline;
                }

                header h1 {
                    margin: 0;
                    font-size: clamp(1.8rem, 3vw, 2.3rem);
                }

                header p {
                    margin: 0.4rem 0 0;
                    max-width: 820px;
                    color: rgba(226, 232, 240, 0.78);
                    line-height: 1.6;
                }

                .layout {
                    flex: 1;
                    display: grid;
                    grid-template-columns: minmax(320px, 360px) 1fr;
                    gap: 1.6rem;
                    padding: 1.8rem 2rem 2.4rem;
                }

                aside {
                    display: flex;
                    flex-direction: column;
                    gap: 1.4rem;
                    border-radius: 1.2rem;
                    border: 1px solid rgba(148, 163, 184, 0.22);
                    background: rgba(15, 23, 42, 0.88);
                    padding: 1.5rem;
                    box-shadow: 0 24px 48px rgba(15, 23, 42, 0.45);
                }

                aside h2 {
                    margin: 0 0 0.6rem;
                    font-size: 1.2rem;
                    color: #f1f5f9;
                }

                .control-group {
                    display: grid;
                    gap: 0.75rem;
                }

                .control {
                    display: flex;
                    flex-direction: column;
                    gap: 0.45rem;
                    background: rgba(30, 41, 59, 0.75);
                    border: 1px solid rgba(148, 163, 184, 0.2);
                    border-radius: 0.85rem;
                    padding: 0.9rem 1rem;
                }

                .control label {
                    font-size: 0.85rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    color: rgba(226, 232, 240, 0.72);
                }

                .control input,
                .control select {
                    background: rgba(15, 23, 42, 0.6);
                    color: #e2e8f0;
                    border: 1px solid rgba(148, 163, 184, 0.35);
                    border-radius: 0.6rem;
                    padding: 0.5rem 0.75rem;
                    font-size: 0.95rem;
                }

                .control input[type="color"] {
                    padding: 0.25rem;
                    height: 2.2rem;
                }

                .toolbar {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.6rem;
                }

                button {
                    background: rgba(30, 41, 59, 0.75);
                    color: #e2e8f0;
                    border: 1px solid rgba(148, 163, 184, 0.35);
                    border-radius: 0.6rem;
                    padding: 0.5rem 0.95rem;
                    font-size: 0.95rem;
                    cursor: pointer;
                    transition: transform 0.12s ease, border-color 0.2s ease;
                }

                button:hover {
                    transform: translateY(-1px);
                    border-color: #38bdf8;
                }

                button.active {
                    border-color: #38bdf8;
                    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.3);
                }

                .hint {
                    font-size: 0.85rem;
                    color: rgba(148, 163, 184, 0.78);
                    line-height: 1.5;
                }

                .control.disabled label,
                .control.disabled input,
                .control.disabled select {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                .metadata-panel {
                    display: grid;
                    gap: 1rem;
                    margin-bottom: 1.5rem;
                    padding: 1.25rem;
                    border-radius: 1rem;
                    border: 1px solid rgba(148, 163, 184, 0.2);
                    background: rgba(15, 23, 42, 0.55);
                }

                .metadata-panel h2 {
                    margin: 0;
                    font-size: 1.3rem;
                    color: #f8fafc;
                }

                .metadata-grid {
                    display: grid;
                    gap: 0.75rem;
                }

                .profile-summary {
                    margin-top: 0.75rem;
                    padding: 0.85rem;
                    border-radius: 0.75rem;
                    border: 1px solid rgba(56, 189, 248, 0.32);
                    background: rgba(30, 64, 175, 0.28);
                    display: grid;
                    gap: 0.4rem;
                }

                .profile-summary div {
                    display: flex;
                    justify-content: space-between;
                    gap: 0.5rem;
                    font-size: 0.9rem;
                }

                .profile-summary span {
                    color: rgba(226, 232, 240, 0.75);
                }

                .profile-summary strong {
                    color: #e0f2fe;
                    font-weight: 600;
                    text-align: right;
                }

                .doc-link {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 1.2rem;
                    height: 1.2rem;
                    margin-left: 0.35rem;
                    border-radius: 999px;
                    background: rgba(56, 189, 248, 0.18);
                    color: #38bdf8;
                    font-size: 0.75rem;
                    font-weight: 700;
                    text-decoration: none;
                    position: relative;
                    cursor: pointer;
                }

                .doc-link::after {
                    content: attr(data-tooltip);
                    position: absolute;
                    bottom: -0.5rem;
                    left: 50%;
                    transform: translate(-50%, 100%);
                    background: rgba(15, 23, 42, 0.95);
                    color: #e2e8f0;
                    padding: 0.4rem 0.6rem;
                    border-radius: 0.5rem;
                    font-size: 0.7rem;
                    line-height: 1.3;
                    width: max-content;
                    max-width: 220px;
                    opacity: 0;
                    pointer-events: none;
                    transition: opacity 0.15s ease;
                    box-shadow: 0 8px 20px rgba(2, 6, 23, 0.35);
                    z-index: 20;
                }

                .doc-link:hover::after,
                .doc-link:focus-visible::after {
                    opacity: 1;
                }

                .config-section {
                    margin-top: 2rem;
                    display: grid;
                    gap: 0.75rem;
                }

                .config-catalog {
                    display: grid;
                    gap: 0.75rem;
                    max-height: 260px;
                    overflow: auto;
                    padding-right: 0.25rem;
                }

                .config-catalog details {
                    border: 1px solid rgba(148, 163, 184, 0.22);
                    border-radius: 0.85rem;
                    background: rgba(15, 23, 42, 0.55);
                    padding: 0.5rem 0.75rem;
                }

                .config-catalog summary {
                    cursor: pointer;
                    font-weight: 600;
                    color: #f8fafc;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }

                .config-catalog ul {
                    list-style: none;
                    padding: 0.5rem 0 0.5rem 0;
                    margin: 0;
                    display: grid;
                    gap: 0.6rem;
                }

                .config-catalog li {
                    display: grid;
                    gap: 0.35rem;
                    font-size: 0.85rem;
                    color: rgba(226, 232, 240, 0.8);
                }

                .config-catalog li strong {
                    color: #bae6fd;
                    font-weight: 600;
                }

                .config-catalog a.inline-doc {
                    font-size: 0.75rem;
                    color: #38bdf8;
                    text-decoration: none;
                }

                .shape-list {
                    display: grid;
                    gap: 0.8rem;
                    max-height: 30vh;
                    overflow: auto;
                    padding-right: 0.2rem;
                }

                .shape-entry {
                    border-radius: 0.8rem;
                    border: 1px solid rgba(148, 163, 184, 0.2);
                    background: rgba(30, 41, 59, 0.7);
                    padding: 0.75rem 0.85rem;
                    display: grid;
                    gap: 0.35rem;
                }

                .shape-entry header {
                    display: flex;
                    justify-content: space-between;
                    align-items: baseline;
                    gap: 0.5rem;
                }

                .shape-entry h3 {
                    margin: 0;
                    font-size: 1rem;
                    color: #f8fafc;
                }

                .shape-entry span {
                    font-size: 0.75rem;
                    letter-spacing: 0.05em;
                    text-transform: uppercase;
                    color: rgba(148, 163, 184, 0.75);
                }

                .shape-entry dl {
                    display: grid;
                    grid-template-columns: max-content 1fr;
                    gap: 0.35rem 0.6rem;
                    margin: 0;
                }

                .shape-entry dt {
                    font-size: 0.78rem;
                    color: rgba(148, 163, 184, 0.8);
                }

                .shape-entry dd {
                    margin: 0;
                    font-size: 0.85rem;
                    color: rgba(226, 232, 240, 0.88);
                }

                .cad-panel {
                    margin-top: 1.8rem;
                    display: grid;
                    gap: 1rem;
                    padding: 1.5rem;
                    border-radius: 1.1rem;
                    border: 1px solid rgba(148, 163, 184, 0.25);
                    background: rgba(15, 23, 42, 0.88);
                    box-shadow: 0 32px 64px rgba(15, 23, 42, 0.6);
                }

                .cad-panel header {
                    display: grid;
                    gap: 0.45rem;
                }

                .cad-panel h2 {
                    margin: 0;
                    font-size: 1.3rem;
                    color: #f8fafc;
                }

                .cad-panel p {
                    margin: 0;
                    font-size: 0.9rem;
                    color: rgba(148, 163, 184, 0.85);
                    line-height: 1.6;
                }

                .cad-toolbox {
                    display: grid;
                    gap: 0.75rem;
                }

                .cad-toolbox .row {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.85rem;
                }

                .cad-toolbox label {
                    display: flex;
                    flex-direction: column;
                    gap: 0.4rem;
                    font-size: 0.85rem;
                    color: rgba(226, 232, 240, 0.85);
                }

                .cad-toolbox input[type="file"] {
                    padding: 0.5rem;
                    background: rgba(30, 41, 59, 0.75);
                    border: 1px dashed rgba(56, 189, 248, 0.4);
                    border-radius: 0.65rem;
                    color: #e2e8f0;
                    cursor: pointer;
                }

                .cad-toolbox input[type="text"],
                .cad-toolbox select {
                    background: rgba(30, 41, 59, 0.65);
                    border: 1px solid rgba(148, 163, 184, 0.35);
                    border-radius: 0.6rem;
                    padding: 0.5rem 0.75rem;
                    color: #e2e8f0;
                    font-size: 0.95rem;
                }

                .cad-toolbox button {
                    background: rgba(30, 41, 59, 0.78);
                    border: 1px solid rgba(148, 163, 184, 0.35);
                    border-radius: 0.7rem;
                    padding: 0.55rem 1rem;
                    color: #f8fafc;
                    font-weight: 600;
                    cursor: pointer;
                    transition: transform 0.12s ease, border-color 0.2s ease;
                }

                .cad-toolbox button:hover,
                .cad-toolbox button.active {
                    transform: translateY(-1px);
                    border-color: #38bdf8;
                    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25);
                }

                .cad-status {
                    font-size: 0.85rem;
                    color: rgba(148, 163, 184, 0.85);
                }

                .cad-status[data-state="error"] {
                    color: #fca5a5;
                }

                .cad-status[data-state="loading"] {
                    color: #fbbf24;
                }

                .cad-viewer {
                    position: relative;
                    min-height: 440px;
                    border-radius: 1rem;
                    border: 1px solid rgba(148, 163, 184, 0.2);
                    background: radial-gradient(circle at top, rgba(30, 41, 59, 0.92), rgba(15, 23, 42, 0.96));
                    overflow: hidden;
                }

                .cad-viewer.drag-active {
                    border-color: #38bdf8;
                    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.35);
                }

                .cad-annotation-list {
                    display: grid;
                    gap: 0.6rem;
                }

                .cad-annotation-entry {
                    display: grid;
                    gap: 0.35rem;
                    padding: 0.75rem;
                    border-radius: 0.85rem;
                    border: 1px solid rgba(148, 163, 184, 0.28);
                    background: rgba(30, 41, 59, 0.72);
                }

                .cad-annotation-entry header {
                    display: flex;
                    justify-content: space-between;
                    gap: 0.5rem;
                    align-items: baseline;
                }

                .cad-annotation-entry h3 {
                    margin: 0;
                    font-size: 1rem;
                    color: #f8fafc;
                }

                .cad-annotation-entry span {
                    font-size: 0.75rem;
                    letter-spacing: 0.05em;
                    text-transform: uppercase;
                    color: rgba(56, 189, 248, 0.78);
                }

                .cad-annotation-entry button {
                    justify-self: start;
                }

                .canvas-shell {
                    border-radius: 1.2rem;
                    border: 1px solid rgba(148, 163, 184, 0.25);
                    background: radial-gradient(circle at top, rgba(30, 64, 175, 0.24), rgba(15, 23, 42, 0.9));
                    min-height: 70vh;
                    position: relative;
                    overflow: hidden;
                }

                svg {
                    width: 100%;
                    height: 100%;
                    display: block;
                    background: repeating-linear-gradient(0deg, rgba(148, 163, 184, 0.08) 0, rgba(148, 163, 184, 0.08) 1px, transparent 1px, transparent 32px),
                        repeating-linear-gradient(90deg, rgba(148, 163, 184, 0.08) 0, rgba(148, 163, 184, 0.08) 1px, transparent 1px, transparent 32px);
                }

                image {
                    pointer-events: none;
                }

                .shape-label {
                    fill: #f8fafc;
                    font-size: 13px;
                    text-shadow: 0 1px 2px rgba(15, 23, 42, 0.85);
                    pointer-events: none;
                }

                .dimension-label {
                    font-size: 11px;
                    fill: rgba(226, 232, 240, 0.9);
                }

                .rotational.disabled {
                    opacity: 0.4;
                }

                @media (max-width: 980px) {
                    .layout {
                        grid-template-columns: 1fr;
                        padding: 1.5rem;
                    }

                    aside {
                        max-height: none;
                    }

                    .shape-list {
                        max-height: none;
                    }
                }
            </style>
        </head>
        <body>
            <header>
                <nav>
                    <a href=\"/\">← Landingpage</a>
                    <a href=\"/board-designer\">Board-Designer</a>
                </nav>
                <h1>Printer Designer Studio</h1>
                <p>
                    Lade ein Foto oder Rendering deines Aufbaus hoch, markiere Extruder, Motoren, Sensoren und Lüfter und ergänze
                    Maße sowie Rotationsdistanzen. Die erstellte Visualisierung bildet die Grundlage für wiederverwendbare
                    Druckerdefinitionen im geplanten Konfigurator.
                </p>
            </header>
            <div class=\"layout\">
                <aside>
                    <section class="metadata-panel" aria-labelledby="metadataHeading">
                        <h2 id="metadataHeading">Druckerprofil</h2>
                        <div class="metadata-grid">
                            <div class="control">
                                <label for="printerName">Druckername</label>
                                <input id="printerName" type="text" placeholder="z. B. Voron Trident" />
                                <p class="hint">Der Name aktiviert den Bild-Upload und wird für gespeicherte Profile verwendet.</p>
                            </div>
                            <div class="control">
                                <label for="printerType">Druckertyp<a id="printerTypeDoc" class="doc-link" href="#" target="_blank" rel="noreferrer" data-tooltip="">?</a></label>
                                <select id="printerType"></select>
                            </div>
                            <div class="control">
                                <label for="hotend">Hotend<a id="hotendDoc" class="doc-link" href="#" target="_blank" rel="noreferrer" data-tooltip="">?</a></label>
                                <select id="hotend"></select>
                            </div>
                            <div class="control">
                                <label for="controlBoard">Mainboard<a id="controlBoardDoc" class="doc-link" href="#" target="_blank" rel="noreferrer" data-tooltip="">?</a></label>
                                <select id="controlBoard"></select>
                            </div>
                            <div class="control">
                                <label for="leadScrew">Lead Screw<a id="leadScrewDoc" class="doc-link" href="#" target="_blank" rel="noreferrer" data-tooltip="">?</a></label>
                                <select id="leadScrew"></select>
                            </div>
                            <div class="control">
                                <label for="belt">Riemen<a id="beltDoc" class="doc-link" href="#" target="_blank" rel="noreferrer" data-tooltip="">?</a></label>
                                <select id="belt"></select>
                            </div>
                            <div class="control">
                                <label for="gearRatio">Getriebe / Ratio<a id="gearRatioDoc" class="doc-link" href="#" target="_blank" rel="noreferrer" data-tooltip="">?</a></label>
                                <select id="gearRatio"></select>
                            </div>
                            <div class="control">
                                <label for="heatedBed">Heizbettgröße<a id="heatedBedDoc" class="doc-link" href="#" target="_blank" rel="noreferrer" data-tooltip="">?</a></label>
                                <select id="heatedBed"></select>
                            </div>
                        </div>
                        <div class="profile-summary" id="printerProfileSummary" aria-live="polite">
                            <div><span>Name</span><strong>–</strong></div>
                            <div><span>Typ</span><strong>–</strong></div>
                            <div><span>Hotend</span><strong>–</strong></div>
                            <div><span>Mainboard</span><strong>–</strong></div>
                            <div><span>Lead Screw</span><strong>–</strong></div>
                            <div><span>Riemen</span><strong>–</strong></div>
                            <div><span>Getriebe</span><strong>–</strong></div>
                            <div><span>Heizbett</span><strong>–</strong></div>
                        </div>
                    </section>
                    <div class="control-group">
                        <div class="control disabled">
                            <label for="backgroundUpload">Hintergrundgrafik</label>
                            <input id="backgroundUpload" type="file" accept="image/*" disabled />
                            <p class="hint">Unterstützt PNG, JPG und SVG. Der Upload wird nach Benennung des Druckers aktiviert.</p>
                        </div>
                        <div class="control">
                            <label for="componentType">Komponententyp</label>
                            <select id="componentType">
                                <option value="switch">Endstop / Schalter</option>
                                <option value="extruder">Extruder / Hotend</option>
                                <option value="stepper" selected>Stepper-Motor</option>
                                <option value="lead_screw">Lead Screw / Z-Antrieb</option>
                                <option value="sensor">Sensor</option>
                                <option value="fan">Lüfter</option>
                                <option value="custom">Benutzerdefiniert</option>
                            </select>
                        </div>
                        <div class="control rotational">
                            <label for="rotationalDistance">Rotationsdistanz (mm)</label>
                            <input id="rotationalDistance" type="number" step="0.01" placeholder="z. B. 32.0" />
                            <p class="hint">Wird für Stepper- und Lead-Screw-Markierungen übernommen.</p>
                        </div>
                        <div class="control">
                            <label for="highlightColor">Farbe</label>
                            <input id="highlightColor" type="color" value="#22c55e" />
                        </div>
                        <div class="control">
                            <label>Werkzeuge</label>
                            <div class="toolbar">
                                <button id="rectTool" type="button">Rechteck</button>
                                <button id="circleTool" type="button">Kreis</button>
                                <button id="arrowTool" type="button">Maßpfeil</button>
                                <button id="panTool" type="button">Verschieben</button>
                            </div>
                            <p class="hint">Zeichne mit zwei Klicks. Pfeile benötigen Start- und Endpunkt sowie ein Maß. Vorgeschlagene Maße orientieren sich an Pixeln, eigene mm-Angaben können eingetragen werden.</p>
                        </div>
                    </div>
                    <div>
                        <h2>Markierungen</h2>
                        <div id="printerShapeList" class="shape-list"></div>
                    </div>
                    <section class="config-section">
                        <h2>Klipper-Konfiguration</h2>
                        <p class="hint">Überblick über zentrale Optionen. Die Links öffnen direkt die Referenz im Browser.</p>
                        <div id="configCatalog" class="config-catalog"></div>
                    </section>
                </aside>
                <main>
                    <section class=\"workspace-panel\" id=\"printerWorkspace\" data-active-view=\"plan\">
                        <div class=\"workspace-toggle\" role=\"tablist\" aria-label=\"Darstellungsmodus wählen\">
                            <button type=\"button\" class=\"active\" data-view-target=\"plan\" role=\"tab\" aria-selected=\"true\">2D-Layout</button>
                            <button type=\"button\" data-view-target=\"cad\" role=\"tab\" aria-selected=\"false\">3D-CAD</button>
                        </div>
                        <div class=\"plan-view\" data-view=\"plan\">
                            <div class=\"canvas-shell\">
                                <svg id=\"printerCanvas\" viewBox=\"0 0 1280 720\" role=\"img\" aria-label=\"Printer designer canvas\">
                                    <defs>
                                        <marker id=\"arrowhead-end\" markerWidth=\"10\" markerHeight=\"10\" refX=\"6\" refY=\"3\" orient=\"auto\" markerUnits=\"strokeWidth\">
                                            <path d=\"M0,0 L6,3 L0,6 z\" fill=\"currentColor\"></path>
                                        </marker>
                                        <marker id=\"arrowhead-start\" markerWidth=\"10\" markerHeight=\"10\" refX=\"4\" refY=\"3\" orient=\"auto-start-reverse\" markerUnits=\"strokeWidth\">
                                            <path d=\"M0,0 L6,3 L0,6 z\" fill=\"currentColor\"></path>
                                        </marker>
                                    </defs>
                                    <image id=\"backgroundImage\" x=\"0\" y=\"0\" width=\"1280\" height=\"720\" preserveAspectRatio=\"xMidYMid meet\"></image>
                                </svg>
                            </div>
                        </div>
                        <section class=\"cad-panel\" data-view=\"cad\">
                            <header>
                                <h2>3D-CAD-Vorschau</h2>
                                <p>
                                    Ergänze den 2D-Plan um eine echte 3D-Ansicht. Lade STEP-Modelle deines Druckers oder einzelner
                                    Baugruppen, bewege die Perspektive frei und setze Marker für Riemen, Führungen, Kabel oder
                                Sensorik.
                            </p>
                        </header>
                        <div class=\"cad-toolbox\">
                            <div class=\"row\">
                                <label>
                                    STEP-Datei
                                    <input id=\"printerCadFile\" type=\"file\" accept=\".step,.stp,model/step\" />
                                </label>
                                <label>
                                    Marker-Kategorie
                                    <select id=\"printerCadCategory\">
                                        <option value=\"device\">Baugruppe / Gerät</option>
                                        <option value=\"rails\">Linearführungen</option>
                                        <option value=\"belts\">Riemen &amp; Antriebe</option>
                                        <option value=\"cables\">Kabelwege</option>
                                        <option value=\"sensors\">Sensoren</option>
                                        <option value=\"other\">Sonstige</option>
                                    </select>
                                </label>
                                <label>
                                    Marker-Beschriftung
                                    <input id=\"printerCadLabel\" type=\"text\" placeholder=\"z. B. Filamentsensor\" />
                                </label>
                            </div>
                            <div class=\"row\">
                                <button id=\"printerCadMarkerMode\" type=\"button\">Marker platzieren</button>
                                <button id=\"printerCadResetView\" type=\"button\">Kamera zurücksetzen</button>
                                <button id=\"printerCadClearMarkers\" type=\"button\">Marker entfernen</button>
                            </div>
                            <p class=\"cad-status\" id=\"printerCadStatus\" aria-live=\"polite\">
                                Ziehe eine STEP-Datei auf die Ansicht oder verwende den Button, um die Vorschau zu starten.
                            </p>
                            <p class=\"hint\">
                                Hinweis: Im Marker-Modus setzt ein Linksklick einen Punkt. Im Navigationsmodus dreht der Linksklick,
                                Rechtsklick verschiebt die Ansicht, das Mausrad zoomt.
                            </p>
                        </div>
                        <div
                            class=\"cad-viewer\"
                            id=\"printerCadViewport\"
                            tabindex=\"0\"
                            aria-label=\"Interaktive 3D-Ansicht des Druckers\"
                            data-max-pixel-ratio=\"1.5\"
                        ></div>
                        <section>
                            <h3>3D-Markierungen</h3>
                            <div id=\"printerCadAnnotationList\" class=\"cad-annotation-list\"></div>
                        </section>
                        </section>
                    </section>
                </main>
            </div>
            <script>
                const printerCanvas = document.getElementById('printerCanvas');
                const backgroundImage = document.getElementById('backgroundImage');
                const backgroundUpload = document.getElementById('backgroundUpload');
                const rectTool = document.getElementById('rectTool');
                const circleTool = document.getElementById('circleTool');
                const arrowTool = document.getElementById('arrowTool');
                const panTool = document.getElementById('panTool');
                const componentTypeSelect = document.getElementById('componentType');
                const rotationalDistanceInput = document.getElementById('rotationalDistance');
                const highlightColorInput = document.getElementById('highlightColor');
                const shapeList = document.getElementById('printerShapeList');
                const printerNameInput = document.getElementById('printerName');
                const printerTypeSelect = document.getElementById('printerType');
                const hotendSelect = document.getElementById('hotend');
                const controlBoardSelect = document.getElementById('controlBoard');
                const leadScrewSelect = document.getElementById('leadScrew');
                const beltSelect = document.getElementById('belt');
                const gearRatioSelect = document.getElementById('gearRatio');
                const heatedBedSelect = document.getElementById('heatedBed');
                const printerProfileSummary = document.getElementById('printerProfileSummary');
                const configCatalogContainer = document.getElementById('configCatalog');
                const metadataDocAnchors = {
                    printerType: document.getElementById('printerTypeDoc'),
                    hotend: document.getElementById('hotendDoc'),
                    controlBoard: document.getElementById('controlBoardDoc'),
                    leadScrew: document.getElementById('leadScrewDoc'),
                    belt: document.getElementById('beltDoc'),
                    gearRatio: document.getElementById('gearRatioDoc'),
                    heatedBed: document.getElementById('heatedBedDoc')
                };
                const backgroundControl = backgroundUpload ? backgroundUpload.closest('.control') : null;
                const workspacePanel = document.getElementById('printerWorkspace');
                const viewToggleButtons = workspacePanel
                    ? workspacePanel.querySelectorAll('[data-view-target]')
                    : [];

                const defaultPalette = {
                    switch: '#f97316',
                    extruder: '#ef4444',
                    stepper: '#22c55e',
                    lead_screw: '#0ea5e9',
                    sensor: '#a855f7',
                    fan: '#38bdf8',
                    custom: '#fbbf24'
                };

                const componentLabels = {
                    switch: 'Endstop / Schalter',
                    extruder: 'Extruder / Hotend',
                    stepper: 'Stepper-Motor',
                    lead_screw: 'Lead Screw / Z-Antrieb',
                    sensor: 'Sensor',
                    fan: 'Lüfter',
                    custom: 'Benutzerdefiniert'
                };

                const PRINTER_CONSTANTS = Object.freeze({
                    printerTypes: [
                        {
                            id: 'corexy',
                            label: 'CoreXY',
                            description: 'Gekreuzte XY-Riemen mit stehendem Bett.',
                            docUrl: 'https://www.klipper3d.org/Config_Reference.html#printer'
                        },
                        {
                            id: 'cartesian',
                            label: 'Cartesian',
                            description: 'Klassische XYZ-Kinematik mit unabhängigen Achsen.',
                            docUrl: 'https://www.klipper3d.org/Config_Reference.html#printer'
                        },
                        {
                            id: 'delta',
                            label: 'Delta',
                            description: 'Dreieckskinematik mit vertikalen Türmen.',
                            docUrl: 'https://www.klipper3d.org/Config_Reference.html#delta-kinematics'
                        },
                        {
                            id: 'voron_switchwire',
                            label: 'CoreXZ / Switchwire',
                            description: 'Voron Switchwire bzw. CoreXZ-Aufbau.',
                            docUrl: 'https://www.klipper3d.org/Config_Reference.html#printer'
                        },
                        {
                            id: 'scara',
                            label: 'SCARA',
                            description: 'Schwenkarm-Kinematik für hohe Reichweite.',
                            docUrl: 'https://www.klipper3d.org/Config_Reference.html#scara-kinematics'
                        },
                    ],
                    hotends: [
                        {
                            id: 'e3d_revo',
                            label: 'E3D Revo',
                            description: 'Schnellwechsel-Düse mit integriertem Heizblock.',
                            docUrl: 'https://e3d-online.com/blogs/news/revo-hardware-introduction'
                        },
                        {
                            id: 'dragon',
                            label: 'Phaetus Dragon',
                            description: 'All-Metal-Hotend mit hoher Durchflussleistung.',
                            docUrl: 'https://www.phaetus.com/product/dragon-hotend/'
                        },
                        {
                            id: 'mosquito',
                            label: 'Slice Mosquito',
                            description: 'Modulares Hotend mit austauschbaren Düsen.',
                            docUrl: 'https://www.sliceengineering.com/products/mosquito-hotend'
                        },
                        {
                            id: 'rapido',
                            label: 'Rapido UHF',
                            description: 'Hochdurchfluss-Hotend für CoreXY-Systeme.',
                            docUrl: 'https://bondtech.se/product/rapido-hotend/'
                        },
                        {
                            id: 'mk8',
                            label: 'MK8 / Creality Standard',
                            description: 'Bowden-Hotend, häufig in i3-basierten Druckern.',
                            docUrl: 'https://www.klipper3d.org/Config_Reference.html#extruder'
                        },
                    ],
                    controlBoards: [
                        {
                            id: 'btt_octopus',
                            label: 'BTT Octopus',
                            description: '32-Bit STM32F446 mit 8–12 Treiber-Steckplätzen.',
                            docUrl: 'https://github.com/bigtreetech/BIGTREETECH-OCTOPUS-V1.0'
                        },
                        {
                            id: 'btt_manta_m8p',
                            label: 'BTT Manta M8P',
                            description: 'Kombiboard mit integrierter CM4-Trägerplatine.',
                            docUrl: 'https://github.com/bigtreetech/BigTreeTech-Manta-M8P'
                        },
                        {
                            id: 'fysetc_spider',
                            label: 'FYSETC Spider',
                            description: 'STM32F446-Board, ausgelegt für Voron-Drucker.',
                            docUrl: 'https://wiki.fysetc.com/Spider/'
                        },
                        {
                            id: 'duet2_wifi',
                            label: 'Duet 2 WiFi',
                            description: 'ARM-basiertes 32-Bit-Board mit Weboberfläche.',
                            docUrl: 'https://duet3d.dozuki.com/Wiki/Duet_2_Wifi_Ethernet'
                        },
                        {
                            id: 'skr_mini_e3',
                            label: 'BTT SKR Mini E3',
                            description: 'Drop-in-Board für viele Creality-Modelle.',
                            docUrl: 'https://github.com/bigtreetech/BIGTREETECH-SKR-mini-E3'
                        },
                    ],
                    leadScrews: [
                        {
                            id: 't8_2',
                            label: 'T8 P2',
                            description: 'Trapezspindel mit 2 mm Steigung pro Umdrehung.',
                            docUrl: 'https://www.klipper3d.org/Rotation_Distance.html'
                        },
                        {
                            id: 't8_4',
                            label: 'T8 P4',
                            description: '2 mm Steigung, viergängige Spindel (8 mm Hub).',
                            docUrl: 'https://www.klipper3d.org/Rotation_Distance.html'
                        },
                        {
                            id: 't12_3',
                            label: 'T12 P3',
                            description: 'Robuste Z-Achsen-Spindel für größere Formate.',
                            docUrl: 'https://www.klipper3d.org/Rotation_Distance.html'
                        },
                        {
                            id: 'ball_screw_1605',
                            label: 'Kugelgewindetrieb 1605',
                            description: 'Präziser Kugelgewindetrieb mit 5 mm Steigung.',
                            docUrl: 'https://www.klipper3d.org/Rotation_Distance.html'
                        },
                    ],
                    belts: [
                        {
                            id: 'gt2_6',
                            label: 'GT2 6 mm',
                            description: 'Standard-Riemenbreite für i3-Drucker.',
                            docUrl: 'https://www.klipper3d.org/Rotation_Distance.html#belt-driven-axes'
                        },
                        {
                            id: 'gt2_9',
                            label: 'GT2 9 mm',
                            description: 'Stärkerer Riemen für CoreXY-Systeme.',
                            docUrl: 'https://www.klipper3d.org/Rotation_Distance.html#belt-driven-axes'
                        },
                        {
                            id: 'gt2_12',
                            label: 'GT2 12 mm',
                            description: 'Verstärkte Variante für hohe Beschleunigungen.',
                            docUrl: 'https://www.klipper3d.org/Rotation_Distance.html#belt-driven-axes'
                        },
                        {
                            id: 'gates_2gt',
                            label: 'Gates 2GT',
                            description: 'Original Gates-Riemen mit hoher Lebensdauer.',
                            docUrl: 'https://www.gates.com/us/en/gg-drive-systems/powergrip-gt3-timing-belt/p/9453-00000000.html'
                        },
                    ],
                    gearRatios: [
                        {
                            id: '1_1',
                            label: 'Direktantrieb 1:1',
                            description: 'Kein Übersetzungsverhältnis.',
                            docUrl: 'https://www.klipper3d.org/Rotation_Distance.html#extruder-calibration'
                        },
                        {
                            id: '3_1',
                            label: '3:1 Getriebe',
                            description: 'Typisch für Bondtech BMG / LGX Lite.',
                            docUrl: 'https://www.klipper3d.org/Rotation_Distance.html#extruder-calibration'
                        },
                        {
                            id: '5_1',
                            label: '5:1 Getriebe',
                            description: 'Hohe Auflösung, z. B. bei E3D Hemera.',
                            docUrl: 'https://www.klipper3d.org/Rotation_Distance.html#extruder-calibration'
                        },
                        {
                            id: '7_5_1',
                            label: '7.5:1 Planetengetriebe',
                            description: 'Planetengetriebe für maximale Präzision.',
                            docUrl: 'https://www.klipper3d.org/Rotation_Distance.html#extruder-calibration'
                        },
                    ],
                    heatedBeds: [
                        {
                            id: '220x220',
                            label: '220 x 220 mm',
                            description: 'Standardgröße vieler i3-Drucker.',
                            docUrl: 'https://www.klipper3d.org/Config_Reference.html#heater_bed'
                        },
                        {
                            id: '250x250',
                            label: '250 x 250 mm',
                            description: 'Kompatibel mit Voron 2.4 (250).',
                            docUrl: 'https://www.klipper3d.org/Config_Reference.html#heater_bed'
                        },
                        {
                            id: '300x300',
                            label: '300 x 300 mm',
                            description: 'Voron 2.4 (300) oder RatRig V-Core 3.',
                            docUrl: 'https://www.klipper3d.org/Config_Reference.html#heater_bed'
                        },
                        {
                            id: '350x350',
                            label: '350 x 350 mm',
                            description: 'Großformatige CoreXY-Plattformen.',
                            docUrl: 'https://www.klipper3d.org/Config_Reference.html#heater_bed'
                        },
                        {
                            id: '400x400',
                            label: '400 x 400 mm',
                            description: 'DIY- und Industrie-Großformatdrucker.',
                            docUrl: 'https://www.klipper3d.org/Config_Reference.html#heater_bed'
                        },
                    ],
                });

                const KLIPPER_CONFIG_CATALOG = Object.freeze([
                    {
                        section: 'printer',
                        title: 'Printer',
                        docUrl: 'https://www.klipper3d.org/Config_Reference.html#printer',
                        tooltip: 'Grundlegende Kinematik und Bewegungsparameter.',
                        options: [
                            { key: 'kinematics', description: 'Legt den Achsaufbau fest (corexy, cartesian, delta, ...).' },
                            { key: 'max_velocity', description: 'Maximale Verfahrgeschwindigkeit aller Achsen.' },
                            { key: 'max_accel', description: 'Maximale Beschleunigung für Bewegungen.' },
                            { key: 'square_corner_velocity', description: 'Regelt wie aggressiv Kurven abgerundet werden.' },
                        ],
                    },
                    {
                        section: 'stepper_x',
                        title: 'Stepper X',
                        docUrl: 'https://www.klipper3d.org/Config_Reference.html#stepper_x',
                        tooltip: 'Motor- und Endstop-Definition für die X-Achse.',
                        options: [
                            { key: 'step_pin', description: 'GPIO-Pin für Schrittimpulse der X-Achse.' },
                            { key: 'dir_pin', description: 'Richtungspin (ggf. mit ! invertiert).' },
                            { key: 'rotation_distance', description: 'Weg pro Umdrehung, abhängig von Riemen oder Spindel.' },
                            { key: 'endstop_pin', description: 'Pin und Signal für den X-Endstop.' },
                        ],
                    },
                    {
                        section: 'stepper_y',
                        title: 'Stepper Y',
                        docUrl: 'https://www.klipper3d.org/Config_Reference.html#stepper_y',
                        tooltip: 'Definition der Y-Achse analog zur X-Achse.',
                        options: [
                            { key: 'step_pin', description: 'GPIO-Pin für Y-Schrittimpulse.' },
                            { key: 'rotation_distance', description: 'Riemen-/Spindelweg der Y-Achse.' },
                            { key: 'endstop_pin', description: 'Endstop oder Sensor zum Referenzieren.' },
                            { key: 'microsteps', description: 'Feinabstimmung der Treiberauflösung.' },
                        ],
                    },
                    {
                        section: 'stepper_z',
                        title: 'Stepper Z',
                        docUrl: 'https://www.klipper3d.org/Config_Reference.html#stepper_z',
                        tooltip: 'Z-Antrieb inklusive mehreren Motoren und Endstops.',
                        options: [
                            { key: 'step_pin', description: 'GPIO-Pin für den Z-Schrittimpuls.' },
                            { key: 'gear_ratio', description: 'Optionales Übersetzungsverhältnis bei Getrieben.' },
                            { key: 'position_min', description: 'Mechanischer Mindestwert (typisch 0 oder negativ).' },
                            { key: 'position_max', description: 'Maximale Bauhöhe des Druckers.' },
                        ],
                    },
                    {
                        section: 'extruder',
                        title: 'Extruder',
                        docUrl: 'https://www.klipper3d.org/Config_Reference.html#extruder',
                        tooltip: 'Konfiguration des Filamentantriebs und Hotends.',
                        options: [
                            { key: 'rotation_distance', description: 'Filamentweg pro Umdrehung (abhängig vom Getriebe).' },
                            { key: 'gear_ratio', description: 'Übersetzung für Direkt- oder Bowdenextruder.' },
                            { key: 'nozzle_diameter', description: 'Aktuelle Düsenöffnung in mm.' },
                            { key: 'max_extrude_only_velocity', description: 'Grenze für reine Extrusionsgeschwindigkeit.' },
                        ],
                    },
                    {
                        section: 'heater_bed',
                        title: 'Heater Bed',
                        docUrl: 'https://www.klipper3d.org/Config_Reference.html#heater_bed',
                        tooltip: 'Parameter für das beheizte Druckbett.',
                        options: [
                            { key: 'sensor_type', description: 'Thermistortyp oder PT100/PT1000-Konfiguration.' },
                            { key: 'control', description: 'Regler (PID, bang-bang) für das Heizbett.' },
                            { key: 'pid_Kp/Ki/Kd', description: 'PID-Werte für stabile Temperaturregelung.' },
                            { key: 'max_power', description: 'Leistungsbegrenzung zum Schutz des Netzteils.' },
                        ],
                    },
                    {
                        section: 'probe',
                        title: 'Probe / Z-Taster',
                        docUrl: 'https://www.klipper3d.org/Config_Reference.html#probe',
                        tooltip: 'Automatische Bettnivellierung und Tasterparameter.',
                        options: [
                            { key: 'pin', description: 'Signalpin für den Sensor (Induktiv, Klicky, BLTouch, ...).' },
                            { key: 'x_offset', description: 'Versatz des Sensors zur Düse auf der X-Achse.' },
                            { key: 'y_offset', description: 'Versatz auf der Y-Achse.' },
                            { key: 'speed', description: 'Antastgeschwindigkeit beim Leveling.' },
                        ],
                    },
                    {
                        section: 'bed_mesh',
                        title: 'Bed Mesh',
                        docUrl: 'https://www.klipper3d.org/Bed_Mesh.html',
                        tooltip: 'Erzeugt ein Höhenprofil für unebene Druckbetten.',
                        options: [
                            { key: 'probe_count', description: 'Rastergröße für Messpunkte (z. B. 5,5).' },
                            { key: 'speed', description: 'Geschwindigkeit der Messfahrten.' },
                            { key: 'mesh_min/max', description: 'Ausdehnung des Messbereichs relativ zur Düse.' },
                            { key: 'fade_start', description: 'Entfernungswert, ab dem die Korrektur ausgeblendet wird.' },
                        ],
                    },
                    {
                        section: 'fan',
                        title: 'Part-/Hotend-Lüfter',
                        docUrl: 'https://www.klipper3d.org/Config_Reference.html#fan',
                        tooltip: 'Lüftersteuerung für Bauteil- und Hotend-Lüfter.',
                        options: [
                            { key: 'pin', description: 'Ausgangspin für den PWM-geregelten Lüfter.' },
                            { key: 'max_power', description: 'Begrenzung der Lüfterleistung.' },
                            { key: 'kick_start_time', description: 'Startbooster für träge Lüfter.' },
                            { key: 'off_below', description: 'Schwellwert, ab dem der Lüfter vollständig deaktiviert wird.' },
                        ],
                    },
                    {
                        section: 'temperature_sensor',
                        title: 'Temperatursensor',
                        docUrl: 'https://www.klipper3d.org/Config_Reference.html#temperature-sensor',
                        tooltip: 'Allgemeine Sensoren für Elektronik- oder Raumtemperatur.',
                        options: [
                            { key: 'sensor_type', description: 'Typ des Sensors (NTC, PT100, Analog).' },
                            { key: 'sensor_pin', description: 'Eingangspin für den Sensor.' },
                            { key: 'min_temp', description: 'Untergrenze für gültige Messwerte.' },
                            { key: 'max_temp', description: 'Obere Grenze für Sicherheitsabschaltungen.' },
                        ],
                    },
                ]);

                const printerProfile = {
                    name: '',
                    type: null,
                    hotend: null,
                    controlBoard: null,
                    leadScrew: null,
                    belt: null,
                    gearRatio: null,
                    heatedBed: null,
                };

                function escapeHtml(value) {
                    let output = String(value ?? '');
                    output = output.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
                    return output;
                }

                function populateSelectFromConstants(select, entries) {
                    if (!select) {
                        return;
                    }
                    const placeholder = document.createElement('option');
                    placeholder.value = '';
                    placeholder.disabled = true;
                    placeholder.selected = true;
                    placeholder.textContent = 'Bitte wählen';
                    select.innerHTML = '';
                    select.appendChild(placeholder);
                    entries.forEach((entry) => {
                        const option = document.createElement('option');
                        option.value = entry.id;
                        option.textContent = entry.label;
                        option.dataset.description = entry.description || '';
                        option.dataset.doc = entry.docUrl || '';
                        select.appendChild(option);
                    });
                }

                function updateDocAnchor(anchor, entry) {
                    if (!anchor) {
                        return;
                    }
                    if (entry && entry.docUrl) {
                        anchor.href = entry.docUrl;
                        anchor.dataset.tooltip = entry.description || entry.tooltip || 'Dokumentation öffnen';
                        anchor.style.display = '';
                    } else {
                        anchor.href = '#';
                        anchor.dataset.tooltip = 'Keine Dokumentation verfügbar';
                        anchor.style.display = 'none';
                    }
                }

                function updateProfilePreview() {
                    if (!printerProfileSummary) {
                        return;
                    }
                    const summaryEntries = [
                        { label: 'Name', value: printerProfile.name.trim() || '–' },
                        { label: 'Typ', value: printerProfile.type ? printerProfile.type.label : '–' },
                        { label: 'Hotend', value: printerProfile.hotend ? printerProfile.hotend.label : '–' },
                        { label: 'Mainboard', value: printerProfile.controlBoard ? printerProfile.controlBoard.label : '–' },
                        { label: 'Lead Screw', value: printerProfile.leadScrew ? printerProfile.leadScrew.label : '–' },
                        { label: 'Riemen', value: printerProfile.belt ? printerProfile.belt.label : '–' },
                        { label: 'Getriebe', value: printerProfile.gearRatio ? printerProfile.gearRatio.label : '–' },
                        { label: 'Heizbett', value: printerProfile.heatedBed ? printerProfile.heatedBed.label : '–' },
                    ];
                    printerProfileSummary.innerHTML = summaryEntries
                        .map((entry) => `<div><span>${escapeHtml(entry.label)}</span><strong>${escapeHtml(entry.value)}</strong></div>`)
                        .join('');
                }

                function updateUploadAvailability() {
                    const nameProvided = printerProfile.name.trim().length > 0;
                    if (backgroundUpload) {
                        backgroundUpload.disabled = !nameProvided;
                        if (!nameProvided) {
                            backgroundUpload.value = '';
                        }
                    }
                    if (backgroundControl) {
                        backgroundControl.classList.toggle('disabled', !nameProvided);
                    }
                }

                function bindMetadataSelect(key, select, entries, anchor) {
                    if (!select) {
                        return;
                    }
                    populateSelectFromConstants(select, entries);
                    select.addEventListener('change', () => {
                        const entry = entries.find((item) => item.id === select.value) || null;
                        printerProfile[key] = entry;
                        if (entry && entry.description) {
                            select.title = entry.description;
                        } else {
                            select.removeAttribute('title');
                        }
                        updateDocAnchor(anchor, entry);
                        updateProfilePreview();
                    });
                    updateDocAnchor(anchor, null);
                }

                function renderConfigCatalog() {
                    if (!configCatalogContainer) {
                        return;
                    }
                    configCatalogContainer.innerHTML = '';
                    KLIPPER_CONFIG_CATALOG.forEach((section) => {
                        const details = document.createElement('details');
                        const summary = document.createElement('summary');
                        summary.textContent = section.title;
                        summary.title = section.tooltip || '';
                        if (section.docUrl) {
                            const docLink = document.createElement('a');
                            docLink.href = section.docUrl;
                            docLink.target = '_blank';
                            docLink.rel = 'noreferrer';
                            docLink.className = 'doc-link';
                            docLink.dataset.tooltip = 'Dokumentation öffnen';
                            docLink.textContent = '?';
                            summary.appendChild(docLink);
                        }
                        details.appendChild(summary);
                        const list = document.createElement('ul');
                        section.options.forEach((option) => {
                            const item = document.createElement('li');
                            const keyLabel = document.createElement('strong');
                            keyLabel.textContent = option.key;
                            item.appendChild(keyLabel);
                            const desc = document.createElement('span');
                            desc.textContent = option.description;
                            item.appendChild(desc);
                            const docUrl = option.docUrl || section.docUrl;
                            if (docUrl) {
                                const anchor = document.createElement('a');
                                anchor.href = docUrl;
                                anchor.target = '_blank';
                                anchor.rel = 'noreferrer';
                                anchor.className = 'inline-doc';
                                anchor.textContent = 'Referenz öffnen';
                                item.appendChild(anchor);
                            }
                            list.appendChild(item);
                        });
                        details.appendChild(list);
                        configCatalogContainer.appendChild(details);
                    });
                }

                window.PRINTER_CONSTANTS = PRINTER_CONSTANTS;
                window.KLIPPER_CONFIG_CATALOG = KLIPPER_CONFIG_CATALOG;

                if (workspacePanel && viewToggleButtons.length) {
                    viewToggleButtons.forEach((button) => {
                        button.addEventListener('click', () => {
                            const target = button.dataset.viewTarget;
                            if (!target) {
                                return;
                            }
                            workspacePanel.dataset.activeView = target;
                            viewToggleButtons.forEach((other) => {
                                const isActive = other === button;
                                other.classList.toggle('active', isActive);
                                other.setAttribute('aria-selected', String(isActive));
                            });
                        });
                    });
                }

                if (printerNameInput) {
                    printerNameInput.addEventListener('input', () => {
                        printerProfile.name = printerNameInput.value;
                        updateProfilePreview();
                        updateUploadAvailability();
                    });
                }

                bindMetadataSelect('type', printerTypeSelect, PRINTER_CONSTANTS.printerTypes, metadataDocAnchors.printerType);
                bindMetadataSelect('hotend', hotendSelect, PRINTER_CONSTANTS.hotends, metadataDocAnchors.hotend);
                bindMetadataSelect('controlBoard', controlBoardSelect, PRINTER_CONSTANTS.controlBoards, metadataDocAnchors.controlBoard);
                bindMetadataSelect('leadScrew', leadScrewSelect, PRINTER_CONSTANTS.leadScrews, metadataDocAnchors.leadScrew);
                bindMetadataSelect('belt', beltSelect, PRINTER_CONSTANTS.belts, metadataDocAnchors.belt);
                bindMetadataSelect('gearRatio', gearRatioSelect, PRINTER_CONSTANTS.gearRatios, metadataDocAnchors.gearRatio);
                bindMetadataSelect('heatedBed', heatedBedSelect, PRINTER_CONSTANTS.heatedBeds, metadataDocAnchors.heatedBed);
                updateProfilePreview();
                updateUploadAvailability();
                renderConfigCatalog();

                let activeTool = 'rect';
                let drawing = false;
                let startPoint = { x: 0, y: 0 };
                let currentShape = null;
                let viewBox = { x: 0, y: 0, width: 1280, height: 720 };
                let panStart = null;

                function setActiveTool(tool) {
                    activeTool = tool;
                    [rectTool, circleTool, arrowTool, panTool].forEach((button) => {
                        button.classList.toggle('active', button.dataset.tool === tool);
                    });
                    if (tool === 'pan') {
                        printerCanvas.style.cursor = 'grab';
                    } else {
                        printerCanvas.style.cursor = 'crosshair';
                    }
                }

                function svgCursor(event) {
                    const rect = printerCanvas.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) {
                        return null;
                    }

                    const touch = 'touches' in event && event.touches.length ? event.touches[0] : null;
                    const clientX = touch ? touch.clientX : event.clientX;
                    const clientY = touch ? touch.clientY : event.clientY;

                    if (typeof clientX !== 'number' || typeof clientY !== 'number') {
                        return null;
                    }

                    const normalizedX = (clientX - rect.left) / rect.width;
                    const normalizedY = (clientY - rect.top) / rect.height;

                    return {
                        x: viewBox.x + normalizedX * viewBox.width,
                        y: viewBox.y + normalizedY * viewBox.height
                    };
                }

                function createShapeId() {
                    return `printer-shape-${Math.random().toString(36).slice(2, 10)}`;
                }

                function createTextElement(x, y, text, extraClass) {
                    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    label.setAttribute('x', x);
                    label.setAttribute('y', y);
                    label.setAttribute('class', extraClass ? `shape-label ${extraClass}` : 'shape-label');
                    label.setAttribute('text-anchor', 'middle');
                    label.setAttribute('dominant-baseline', 'middle');
                    label.textContent = text;
                    return label;
                }

                function addShapeEntry(details) {
                    const wrapper = document.createElement('article');
                    wrapper.className = 'shape-entry';
                    wrapper.dataset.shapeId = details.id;
                    wrapper.innerHTML = `
                        <header>
                            <h3>${details.label}</h3>
                            <span>${componentLabels[details.componentType] ?? details.componentType}</span>
                        </header>
                        <dl>
                            <dt>Geometrie</dt>
                            <dd>${details.geometry}</dd>
                            <dt>Farbe</dt>
                            <dd>${details.color}</dd>
                            <dt>Maß / Notiz</dt>
                            <dd>${details.dimension || '—'}</dd>
                            <dt>Typ</dt>
                            <dd>${details.shapeType}</dd>
                            ${details.rotationalDistance ? `<dt>Rotationsdistanz</dt><dd>${details.rotationalDistance} mm</dd>` : ''}
                        </dl>
                    `;
                    shapeList.appendChild(wrapper);
                }

                function updateRotationalVisibility() {
                    const needsRotation = ['stepper', 'lead_screw'].includes(componentTypeSelect.value);
                    rotationalDistanceInput.disabled = !needsRotation;
                    rotationalDistanceInput.parentElement.classList.toggle('disabled', !needsRotation);
                    if (!needsRotation) {
                        rotationalDistanceInput.value = '';
                    }
                    if (!highlightColorInput.dataset.userChanged) {
                        const defaultColor = defaultPalette[componentTypeSelect.value] || '#38bdf8';
                        highlightColorInput.value = defaultColor;
                    }
                }

                componentTypeSelect.addEventListener('change', updateRotationalVisibility);
                highlightColorInput.addEventListener('input', () => {
                    highlightColorInput.dataset.userChanged = 'true';
                });
                updateRotationalVisibility();

                backgroundUpload.addEventListener('change', (event) => {
                    const file = event.target.files && event.target.files[0];
                    if (!file) {
                        return;
                    }
                    const reader = new FileReader();
                    reader.onload = (loadEvent) => {
                        const dataUrl = loadEvent.target?.result;
                        if (typeof dataUrl !== 'string') {
                            return;
                        }
                        const img = new Image();
                        img.onload = () => {
                            const width = img.naturalWidth || img.width || 1280;
                            const height = img.naturalHeight || img.height || 720;
                            backgroundImage.setAttribute('href', dataUrl);
                            backgroundImage.setAttribute('width', width);
                            backgroundImage.setAttribute('height', height);
                            viewBox = { x: 0, y: 0, width, height };
                            printerCanvas.setAttribute('viewBox', `0 0 ${width} ${height}`);
                        };
                        img.src = dataUrl;
                    };
                    reader.readAsDataURL(file);
                });

                rectTool.dataset.tool = 'rect';
                circleTool.dataset.tool = 'circle';
                arrowTool.dataset.tool = 'arrow';
                panTool.dataset.tool = 'pan';

                [rectTool, circleTool, arrowTool, panTool].forEach((button) => {
                    button.addEventListener('click', () => {
                        setActiveTool(button.dataset.tool);
                    });
                });

                setActiveTool('rect');

                printerCanvas.addEventListener('mousedown', (event) => {
                    const cursorPoint = svgCursor(event);
                    if (!cursorPoint) {
                        return;
                    }

                    if (activeTool === 'pan') {
                        panStart = { x: cursorPoint.x, y: cursorPoint.y, viewBox: { ...viewBox } };
                        printerCanvas.style.cursor = 'grabbing';
                        return;
                    }

                    drawing = true;
                    startPoint = { x: cursorPoint.x, y: cursorPoint.y };
                    const color = highlightColorInput.value;

                    if (activeTool === 'rect') {
                        currentShape = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                        currentShape.setAttribute('x', startPoint.x);
                        currentShape.setAttribute('y', startPoint.y);
                        currentShape.setAttribute('width', 1);
                        currentShape.setAttribute('height', 1);
                        currentShape.setAttribute('rx', 10);
                        currentShape.setAttribute('fill', `${color}33`);
                        currentShape.setAttribute('stroke', color);
                        currentShape.setAttribute('stroke-width', 2.2);
                        printerCanvas.appendChild(currentShape);
                    } else if (activeTool === 'circle') {
                        currentShape = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                        currentShape.setAttribute('cx', startPoint.x);
                        currentShape.setAttribute('cy', startPoint.y);
                        currentShape.setAttribute('r', 1);
                        currentShape.setAttribute('fill', `${color}33`);
                        currentShape.setAttribute('stroke', color);
                        currentShape.setAttribute('stroke-width', 2.2);
                        printerCanvas.appendChild(currentShape);
                    } else if (activeTool === 'arrow') {
                        currentShape = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                        currentShape.setAttribute('x1', startPoint.x);
                        currentShape.setAttribute('y1', startPoint.y);
                        currentShape.setAttribute('x2', startPoint.x);
                        currentShape.setAttribute('y2', startPoint.y);
                        currentShape.setAttribute('stroke', color);
                        currentShape.setAttribute('stroke-width', 3);
                        currentShape.setAttribute('stroke-linecap', 'round');
                        currentShape.setAttribute('marker-end', 'url(#arrowhead-end)');
                        currentShape.setAttribute('marker-start', 'url(#arrowhead-start)');
                        currentShape.style.setProperty('color', color);
                        printerCanvas.appendChild(currentShape);
                    }
                });

                printerCanvas.addEventListener('mousemove', (event) => {
                    const cursorPoint = svgCursor(event);
                    if (!cursorPoint) {
                        return;
                    }

                    if (panStart && activeTool === 'pan') {
                        const dx = cursorPoint.x - panStart.x;
                        const dy = cursorPoint.y - panStart.y;
                        viewBox.x = panStart.viewBox.x - dx;
                        viewBox.y = panStart.viewBox.y - dy;
                        printerCanvas.setAttribute('viewBox', `${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`);
                        return;
                    }

                    if (!drawing || !currentShape) {
                        return;
                    }

                    if (activeTool === 'rect') {
                        const width = cursorPoint.x - startPoint.x;
                        const height = cursorPoint.y - startPoint.y;
                        currentShape.setAttribute('x', Math.min(startPoint.x, cursorPoint.x));
                        currentShape.setAttribute('y', Math.min(startPoint.y, cursorPoint.y));
                        currentShape.setAttribute('width', Math.abs(width));
                        currentShape.setAttribute('height', Math.abs(height));
                    } else if (activeTool === 'circle') {
                        const dx = cursorPoint.x - startPoint.x;
                        const dy = cursorPoint.y - startPoint.y;
                        const radius = Math.sqrt(dx * dx + dy * dy);
                        currentShape.setAttribute('r', radius);
                    } else if (activeTool === 'arrow') {
                        currentShape.setAttribute('x2', cursorPoint.x);
                        currentShape.setAttribute('y2', cursorPoint.y);
                    }
                });

                window.addEventListener('mouseup', () => {
                    if (panStart) {
                        panStart = null;
                        printerCanvas.style.cursor = 'grab';
                        return;
                    }

                    if (!drawing || !currentShape) {
                        return;
                    }

                    drawing = false;

                    const componentType = componentTypeSelect.value;
                    const color = highlightColorInput.value;
                    const labelDefault = componentLabels[componentType]?.split(' ')[0] || 'Komponente';
                    const rawLabel = prompt('Komponentenbezeichnung', labelDefault);
                    const trimmedLabel = rawLabel ? rawLabel.trim() : '';
                    if (!trimmedLabel) {
                        currentShape.remove();
                        currentShape = null;
                        return;
                    }

                    let rotationalDistance = null;
                    if (['stepper', 'lead_screw'].includes(componentType)) {
                        const presetDistance = rotationalDistanceInput.value.trim();
                        if (presetDistance) {
                            rotationalDistance = presetDistance;
                        } else {
                            const promptDistance = prompt('Rotationsdistanz (mm pro Umdrehung)', '');
                            if (promptDistance && promptDistance.trim()) {
                                rotationalDistance = promptDistance.trim();
                            }
                        }
                    }

                    let geometry = '';
                    let dimensionSuggestion = '';
                    let labelPosition = null;
                    let dimensionPosition = null;

                    if (activeTool === 'rect') {
                        const x = parseFloat(currentShape.getAttribute('x'));
                        const y = parseFloat(currentShape.getAttribute('y'));
                        const width = parseFloat(currentShape.getAttribute('width'));
                        const height = parseFloat(currentShape.getAttribute('height'));
                        if (width < 8 || height < 8) {
                            currentShape.remove();
                            currentShape = null;
                            return;
                        }
                        geometry = `x:${x.toFixed(1)}, y:${y.toFixed(1)}, w:${width.toFixed(1)}, h:${height.toFixed(1)}`;
                        dimensionSuggestion = `${width.toFixed(1)} × ${height.toFixed(1)} px`;
                        labelPosition = { x: x + width / 2, y: y + height / 2 };
                        dimensionPosition = { x: labelPosition.x, y: labelPosition.y + 18 };
                    } else if (activeTool === 'circle') {
                        const cx = parseFloat(currentShape.getAttribute('cx'));
                        const cy = parseFloat(currentShape.getAttribute('cy'));
                        const radius = parseFloat(currentShape.getAttribute('r'));
                        if (radius < 6) {
                            currentShape.remove();
                            currentShape = null;
                            return;
                        }
                        geometry = `cx:${cx.toFixed(1)}, cy:${cy.toFixed(1)}, r:${radius.toFixed(1)}`;
                        dimensionSuggestion = `Ø ${(radius * 2).toFixed(1)} px`;
                        labelPosition = { x: cx, y: cy };
                        dimensionPosition = { x: cx, y: cy + radius + 14 };
                    } else if (activeTool === 'arrow') {
                        const x1 = parseFloat(currentShape.getAttribute('x1'));
                        const y1 = parseFloat(currentShape.getAttribute('y1'));
                        const x2 = parseFloat(currentShape.getAttribute('x2'));
                        const y2 = parseFloat(currentShape.getAttribute('y2'));
                        const dx = x2 - x1;
                        const dy = y2 - y1;
                        const length = Math.sqrt(dx * dx + dy * dy);
                        if (length < 12) {
                            currentShape.remove();
                            currentShape = null;
                            return;
                        }
                        const midX = x1 + dx / 2;
                        const midY = y1 + dy / 2;
                        geometry = `(${x1.toFixed(1)},${y1.toFixed(1)}) → (${x2.toFixed(1)},${y2.toFixed(1)})`;
                        dimensionSuggestion = `${length.toFixed(1)} px`;
                        labelPosition = { x: midX, y: midY - 10 };
                        dimensionPosition = { x: midX, y: midY + 10 };
                    }

                    const dimensionPrompt = prompt('Maß oder Notiz (optional)', dimensionSuggestion);
                    let dimensionNotes = dimensionPrompt ? dimensionPrompt.trim() : '';
                    if (activeTool === 'arrow' && !dimensionNotes) {
                        dimensionNotes = dimensionSuggestion;
                    }
                    if (activeTool === 'arrow' && !dimensionNotes) {
                        currentShape.remove();
                        currentShape = null;
                        return;
                    }

                    const shapeId = createShapeId();
                    currentShape.dataset.shapeId = shapeId;

                    if (labelPosition) {
                        const labelElement = createTextElement(labelPosition.x, labelPosition.y, trimmedLabel);
                        printerCanvas.appendChild(labelElement);
                    }
                    if (dimensionNotes && dimensionPosition) {
                        const dimensionElement = createTextElement(dimensionPosition.x, dimensionPosition.y, dimensionNotes, 'dimension-label');
                        printerCanvas.appendChild(dimensionElement);
                    }

                    addShapeEntry({
                        id: shapeId,
                        label: trimmedLabel,
                        componentType,
                        color,
                        dimension: dimensionNotes,
                        shapeType: activeTool === 'arrow' ? 'Maßpfeil' : activeTool === 'rect' ? 'Rechteck' : 'Kreis',
                        geometry,
                        rotationalDistance: rotationalDistance || null
                    });

                    currentShape = null;
                });
        <script src="/static/js/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/gh/kovacsv/occt-import-js@master/dist/occt-import-js.js" crossorigin="anonymous"></script>
        <script>
            (function () {
                const viewport = document.getElementById('printerCadViewport');
                const statusElement = document.getElementById('printerCadStatus');
                if (!viewport) {
                    return;
                }
            
                if (typeof THREE === 'undefined') {
                    if (statusElement) {
                        statusElement.textContent = '3D-Viewer konnte nicht initialisiert werden (THREE.js nicht verfügbar).';
                        statusElement.dataset.state = 'error';
                    }
                    return;
                }
            
                const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
                const pixelRatioCap = (() => {
                    const rawValue = viewport ? parseFloat(viewport.dataset.maxPixelRatio || '1.5') : NaN;
                    if (!Number.isFinite(rawValue) || rawValue <= 0) {
                        return 1.5;
                    }
                    return Math.max(0.5, rawValue);
                })();

                function getEffectivePixelRatio() {
                    const ratio = window.devicePixelRatio || 1;
                    return Math.min(ratio, pixelRatioCap);
                }

                renderer.setPixelRatio(getEffectivePixelRatio());
                renderer.setSize(viewport.clientWidth, viewport.clientHeight, false);
                renderer.outputEncoding = THREE.sRGBEncoding;
                viewport.appendChild(renderer.domElement);
            
                const scene = new THREE.Scene();
                scene.background = new THREE.Color(0x0f172a);
            
                const grid = new THREE.GridHelper(1000, 50, 0x1f2937, 0x1f2937);
                if (Array.isArray(grid.material)) {
                    grid.material.forEach((material) => {
                        material.opacity = 0.2;
                        material.transparent = true;
                    });
                } else {
                    grid.material.opacity = 0.2;
                    grid.material.transparent = true;
                }
                scene.add(grid);
            
                const ambient = new THREE.HemisphereLight(0xf1f5f9, 0x0f172a, 0.9);
                const directional = new THREE.DirectionalLight(0xffffff, 0.8);
                directional.position.set(320, 420, 320);
                scene.add(ambient);
                scene.add(directional);
            
                const camera = new THREE.PerspectiveCamera(50, Math.max(viewport.clientWidth / Math.max(viewport.clientHeight, 1), 1), 0.1, 15000);
                camera.position.set(420, 260, 420);
                camera.lookAt(0, 0, 0);
            
                const raycaster = new THREE.Raycaster();
                const pointer = new THREE.Vector2();
            
                const annotationList = document.getElementById('printerCadAnnotationList');
                const fileInput = document.getElementById('printerCadFile');
                const categorySelect = document.getElementById('printerCadCategory');
                const labelInput = document.getElementById('printerCadLabel');
                const markerToggle = document.getElementById('printerCadMarkerMode');
                const resetViewButton = document.getElementById('printerCadResetView');
                const clearMarkersButton = document.getElementById('printerCadClearMarkers');
            
                const categoryPalette = {
                    device: '#38bdf8',
                    rails: '#22d3ee',
                    belts: '#f97316',
                    cables: '#facc15',
                    sensors: '#a855f7',
                    other: '#94a3b8'
                };
            
                const categoryLabels = {
                    device: 'Baugruppe / Gerät',
                    rails: 'Linearführungen',
                    belts: 'Riemen & Antriebe',
                    cables: 'Kabelwege',
                    sensors: 'Sensor',
                    other: 'Sonstige'
                };
            
                let markerMode = false;
                let currentModel = null;
                let modelScale = 400;
                const annotations = [];
            
                const occtPromise = typeof occtimportjs === 'function' ? occtimportjs() : Promise.resolve(null);
            
                function updateStatus(message, state) {
                    if (!statusElement) {
                        return;
                    }
                    statusElement.textContent = message;
                    if (state) {
                        statusElement.dataset.state = state;
                    } else {
                        statusElement.removeAttribute('data-state');
                    }
                }
            
                updateStatus('Ziehe eine STEP-Datei auf die Ansicht oder verwende den Button, um zu starten.', null);
            
                function createSimpleOrbitControls(camera, domElement, options) {
                    const shouldHandlePointer = options && options.shouldHandlePointer ? options.shouldHandlePointer : () => true;
                    const state = {
                        pointerId: null,
                        rotating: false,
                        panning: false,
                        lastPosition: new THREE.Vector2(),
                        spherical: new THREE.Spherical(),
                        target: new THREE.Vector3()
                    };
                    const tempVec = new THREE.Vector3();
                    const xAxis = new THREE.Vector3();
                    const yAxis = new THREE.Vector3();
            
                    function syncSpherical() {
                        tempVec.copy(camera.position).sub(state.target);
                        state.spherical.setFromVector3(tempVec);
                    }
            
                    function apply() {
                        tempVec.setFromSpherical(state.spherical);
                        camera.position.copy(state.target).add(tempVec);
                        camera.lookAt(state.target);
                    }
            
                    syncSpherical();
                    apply();
            
                    function onPointerDown(event) {
                        if (!shouldHandlePointer(event)) {
                            return;
                        }
                        domElement.setPointerCapture(event.pointerId);
                        state.pointerId = event.pointerId;
                        state.lastPosition.set(event.clientX, event.clientY);
                        if (event.button === 2 || event.button === 1 || event.shiftKey) {
                            state.panning = true;
                            domElement.style.cursor = 'move';
                        } else {
                            state.rotating = true;
                            domElement.style.cursor = 'grabbing';
                        }
                    }
            
                    function onPointerMove(event) {
                        if (state.pointerId !== event.pointerId) {
                            return;
                        }
                        const deltaX = event.clientX - state.lastPosition.x;
                        const deltaY = event.clientY - state.lastPosition.y;
                        state.lastPosition.set(event.clientX, event.clientY);
                        if (state.rotating) {
                            const rotateSpeed = 0.005;
                            state.spherical.theta -= deltaX * rotateSpeed;
                            state.spherical.phi -= deltaY * rotateSpeed;
                            state.spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, state.spherical.phi));
                            apply();
                        } else if (state.panning) {
                            camera.updateMatrixWorld();
                            const panSpeed = 0.0015 * state.spherical.radius;
                            const panX = -deltaX * panSpeed;
                            const panY = deltaY * panSpeed;
                            xAxis.setFromMatrixColumn(camera.matrixWorld, 0);
                            yAxis.setFromMatrixColumn(camera.matrixWorld, 1);
                            state.target.addScaledVector(xAxis, panX);
                            state.target.addScaledVector(yAxis, panY);
                            apply();
                        }
                    }
            
                    function onPointerUp(event) {
                        if (state.pointerId !== event.pointerId) {
                            return;
                        }
                        domElement.releasePointerCapture(event.pointerId);
                        state.rotating = false;
                        state.panning = false;
                        domElement.style.cursor = markerMode ? 'crosshair' : 'grab';
                        state.pointerId = null;
                    }
            
                    function onWheel(event) {
                        event.preventDefault();
                        const delta = event.deltaY;
                        const factor = 1 + Math.min(Math.abs(delta) * 0.0015, 0.25);
                        if (delta > 0) {
                            state.spherical.radius *= factor;
                        } else {
                            state.spherical.radius /= factor;
                        }
                        state.spherical.radius = Math.max(5, Math.min(8000, state.spherical.radius));
                        apply();
                    }
            
                    domElement.addEventListener('pointerdown', onPointerDown);
                    domElement.addEventListener('pointermove', onPointerMove);
                    domElement.addEventListener('pointerup', onPointerUp);
                    domElement.addEventListener('pointercancel', onPointerUp);
                    domElement.addEventListener('wheel', onWheel, { passive: false });
            
                    return {
                        setTarget(target) {
                            state.target.copy(target);
                            syncSpherical();
                            apply();
                        },
                        setRadius(distance) {
                            state.spherical.radius = Math.max(5, distance);
                            apply();
                        },
                        refresh() {
                            syncSpherical();
                            apply();
                        }
                    };
                }
            
                const controls = createSimpleOrbitControls(camera, renderer.domElement, {
                    shouldHandlePointer(event) {
                        return !(markerMode && event.button === 0);
                    }
                });
            
                controls.setTarget(new THREE.Vector3(0, 0, 0));
                controls.setRadius(620);
            
                function resizeRenderer() {
                    const width = viewport.clientWidth;
                    const height = Math.max(viewport.clientHeight, 1);
                    renderer.setPixelRatio(getEffectivePixelRatio());
                    renderer.setSize(width, height, false);
                    camera.aspect = width / height;
                    camera.updateProjectionMatrix();
                }

                window.addEventListener('resize', resizeRenderer);
                if (window.ResizeObserver) {
                    new ResizeObserver(resizeRenderer).observe(viewport);
                }

                let pixelRatioQuery = null;

                function handlePixelRatioChange() {
                    setupPixelRatioObserver();
                    resizeRenderer();
                }

                function setupPixelRatioObserver() {
                    if (!window.matchMedia) {
                        return;
                    }
                    const ratio = Math.round((window.devicePixelRatio || 1) * 100) / 100;
                    const query = window.matchMedia(`(resolution: ${ratio}dppx)`);

                    if (pixelRatioQuery) {
                        if (pixelRatioQuery.removeEventListener) {
                            pixelRatioQuery.removeEventListener('change', handlePixelRatioChange);
                        } else if (pixelRatioQuery.removeListener) {
                            pixelRatioQuery.removeListener(handlePixelRatioChange);
                        }
                    }

                    pixelRatioQuery = query;

                    if (pixelRatioQuery.addEventListener) {
                        pixelRatioQuery.addEventListener('change', handlePixelRatioChange);
                    } else if (pixelRatioQuery.addListener) {
                        pixelRatioQuery.addListener(handlePixelRatioChange);
                    }
                }

                setupPixelRatioObserver();
                resizeRenderer();
            
                function clearAnnotations() {
                    while (annotations.length) {
                        const annotation = annotations.pop();
                        scene.remove(annotation.object3d);
                    }
                    if (annotationList) {
                        annotationList.innerHTML = '';
                    }
                }
            
                function setMarkerMode(enabled) {
                    markerMode = enabled;
                    if (markerToggle) {
                        markerToggle.classList.toggle('active', enabled);
                        markerToggle.textContent = enabled ? 'Marker-Modus aktiv' : 'Marker platzieren';
                    }
                    renderer.domElement.style.cursor = enabled ? 'crosshair' : 'grab';
                }
            
                setMarkerMode(false);
            
                function colorForCategory(category) {
                    return categoryPalette[category] || categoryPalette.other;
                }
            
                function labelForCategory(category) {
                    return categoryLabels[category] || category;
                }
            
                function createTextSprite(text, color) {
                    const canvas = document.createElement('canvas');
                    const context = canvas.getContext('2d');
                    const padding = 26;
                    const fontSize = 64;
                    context.font = `${fontSize}px Inter, sans-serif`;
                    const textWidth = context.measureText(text).width;
                    canvas.width = textWidth + padding * 2;
                    canvas.height = fontSize + padding * 1.6;
                    context.fillStyle = 'rgba(15, 23, 42, 0.9)';
                    context.strokeStyle = color;
                    context.lineWidth = 8;
                    context.fillRect(0, 0, canvas.width, canvas.height);
                    context.strokeRect(0, 0, canvas.width, canvas.height);
                    context.fillStyle = '#f8fafc';
                    context.textBaseline = 'middle';
                    context.font = `${fontSize}px Inter, sans-serif`;
                    context.fillText(text, padding, canvas.height / 2);
                    const texture = new THREE.CanvasTexture(canvas);
                    texture.minFilter = THREE.LinearFilter;
                    texture.encoding = THREE.sRGBEncoding;
                    const material = new THREE.SpriteMaterial({ map: texture, depthTest: false, depthWrite: false });
                    const sprite = new THREE.Sprite(material);
                    const scale = 0.0023 * modelScale;
                    sprite.scale.set(canvas.width * scale * 0.5, canvas.height * scale * 0.5, 1);
                    return sprite;
                }
            
                function addAnnotation(point) {
                    const category = categorySelect ? categorySelect.value : 'other';
                    const label = (labelInput && labelInput.value.trim()) || `${labelForCategory(category)} ${annotations.length + 1}`;
                    const color = colorForCategory(category);
                    const markerSize = Math.max(modelScale * 0.014, 2.5);
                    const markerGeometry = new THREE.SphereGeometry(markerSize, 24, 24);
                    const markerMaterial = new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.3, metalness: 0.15, roughness: 0.45 });
                    const sphere = new THREE.Mesh(markerGeometry, markerMaterial);
                    const sprite = createTextSprite(label, color);
                    sprite.position.set(0, markerSize * 3.4, 0);
                    const group = new THREE.Group();
                    group.add(sphere);
                    group.add(sprite);
                    group.position.copy(point);
                    scene.add(group);
            
                    const annotation = {
                        id: `printer-marker-${Math.random().toString(36).slice(2, 9)}`,
                        category,
                        label,
                        position: point.clone(),
                        object3d: group
                    };
                    annotations.push(annotation);
            
                    if (annotationList) {
                        const wrapper = document.createElement('article');
                        wrapper.className = 'cad-annotation-entry';
                        wrapper.dataset.annotationId = annotation.id;
                        wrapper.innerHTML = `
                            <header>
                                <h3>${label}</h3>
                                <span>${labelForCategory(category)}</span>
                            </header>
                            <p>Position: x=${point.x.toFixed(1)}, y=${point.y.toFixed(1)}, z=${point.z.toFixed(1)}</p>
                        `;
                        const removeButton = document.createElement('button');
                        removeButton.type = 'button';
                        removeButton.textContent = 'Entfernen';
                        removeButton.addEventListener('click', () => {
                            scene.remove(group);
                            const index = annotations.findIndex((item) => item.id === annotation.id);
                            if (index >= 0) {
                                annotations.splice(index, 1);
                            }
                            wrapper.remove();
                        });
                        wrapper.appendChild(removeButton);
                        annotationList.appendChild(wrapper);
                    }
                }
            
                function handleAnnotationEvent(event) {
                    if (!markerMode || !currentModel) {
                        return;
                    }
                    const rect = renderer.domElement.getBoundingClientRect();
                    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
                    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
                    raycaster.setFromCamera(pointer, camera);
                    const intersections = raycaster.intersectObject(currentModel, true);
                    if (intersections.length === 0) {
                        updateStatus('Kein Schnittpunkt gefunden. Bitte erneut versuchen.', 'error');
                        return;
                    }
                    updateStatus('Marker hinzugefügt.', null);
                    addAnnotation(intersections[0].point);
                }
            
                renderer.domElement.addEventListener('pointerdown', (event) => {
                    if (markerMode && event.button === 0) {
                        event.preventDefault();
                        handleAnnotationEvent(event);
                    }
                });
            
                renderer.domElement.addEventListener('contextmenu', (event) => event.preventDefault());
            
                function buildMeshGroup(result) {
                    const group = new THREE.Group();
                    if (!result || !result.success || !Array.isArray(result.meshes)) {
                        return group;
                    }
                    const meshes = result.meshes.map((meshData) => {
                        const geometry = new THREE.BufferGeometry();
                        const positions = meshData?.attributes?.position?.array || [];
                        const positionData = positions instanceof Float32Array ? positions : new Float32Array(positions);
                        geometry.setAttribute('position', new THREE.Float32BufferAttribute(positionData, 3));
                        const normals = meshData?.attributes?.normal?.array;
                        if (normals && normals.length) {
                            const normalData = normals instanceof Float32Array ? normals : new Float32Array(normals);
                            geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normalData, 3));
                        }
                        const indices = meshData?.index?.array;
                        if (indices && indices.length) {
                            const indexData =
                                indices instanceof Uint32Array ||
                                indices instanceof Uint16Array ||
                                indices instanceof Uint8Array
                                    ? indices
                                    : new Uint32Array(indices);
                            geometry.setIndex(indexData);
                        }
                        if (!normals || !normals.length) {
                            geometry.computeVertexNormals();
                        }
                        const colorArray = meshData?.color;
                        const color = Array.isArray(colorArray)
                            ? new THREE.Color(colorArray[0] / 255, colorArray[1] / 255, colorArray[2] / 255)
                            : new THREE.Color('#94a3b8');
                        const material = new THREE.MeshStandardMaterial({
                            color,
                            metalness: 0.15,
                            roughness: 0.75,
                            side: THREE.DoubleSide
                        });
                        const mesh = new THREE.Mesh(geometry, material);
                        mesh.name = meshData?.name || 'STEP Mesh';
                        return mesh;
                    });
            
                    function attachNode(node) {
                        const nodeGroup = new THREE.Group();
                        nodeGroup.name = node?.name || 'StepNode';
                        if (Array.isArray(node?.meshes)) {
                            node.meshes.forEach((index) => {
                                const mesh = meshes[index];
                                if (mesh) {
                                    nodeGroup.add(mesh.clone());
                                }
                            });
                        }
                        if (Array.isArray(node?.children)) {
                            node.children.forEach((child) => {
                                nodeGroup.add(attachNode(child));
                            });
                        }
                        return nodeGroup;
                    }
            
                    group.add(attachNode(result.root));
                    return group;
                }
            
                function fitCameraToGroup(group) {
                    const box = new THREE.Box3().setFromObject(group);
                    const center = box.getCenter(new THREE.Vector3());
                    const size = box.getSize(new THREE.Vector3());
                    const maxDim = Math.max(size.x, size.y, size.z, 1);
                    group.position.set(-center.x, -center.y, -center.z);
                    modelScale = maxDim;
                    controls.setTarget(new THREE.Vector3(0, 0, 0));
                    const distance = maxDim * 1.9;
                    controls.setRadius(distance);
                    camera.position.set(distance, distance * 0.75, distance);
                    camera.near = Math.max(0.1, distance / 500);
                    camera.far = Math.max(1200, distance * 25);
                    camera.updateProjectionMatrix();
                }
            
                async function loadStepFile(file) {
                    if (!file) {
                        return;
                    }
                    updateStatus(`Lade ${file.name} ...`, 'loading');
                    const occt = await occtPromise;
                    if (!occt) {
                        updateStatus('STEP-Parser nicht verfügbar.', 'error');
                        return;
                    }
                    try {
                        const buffer = await file.arrayBuffer();
                        const result = occt.ReadStepFile(new Uint8Array(buffer), null);
                        if (!result || !result.success) {
                            updateStatus('STEP-Datei konnte nicht gelesen werden.', 'error');
                            return;
                        }
                        if (currentModel) {
                            scene.remove(currentModel);
                        }
                        clearAnnotations();
                        currentModel = buildMeshGroup(result);
                        scene.add(currentModel);
                        fitCameraToGroup(currentModel);
                        updateStatus(`${file.name} geladen. Aktiviere den Marker-Modus, um Punkte zu setzen.`, null);
                    } catch (error) {
                        console.error(error);
                        updateStatus('Fehler beim Lesen der STEP-Datei.', 'error');
                    }
                }
            
                if (fileInput) {
                    fileInput.addEventListener('change', (event) => {
                        const file = event.target.files && event.target.files[0];
                        if (file) {
                            loadStepFile(file);
                        }
                    });
                }
            
                if (markerToggle) {
                    markerToggle.addEventListener('click', () => {
                        setMarkerMode(!markerMode);
                    });
                }
            
                if (clearMarkersButton) {
                    clearMarkersButton.addEventListener('click', () => {
                        clearAnnotations();
                        updateStatus('Alle Marker entfernt.', null);
                    });
                }
            
                if (resetViewButton) {
                    resetViewButton.addEventListener('click', () => {
                        if (currentModel) {
                            fitCameraToGroup(currentModel);
                        } else {
                            controls.setTarget(new THREE.Vector3(0, 0, 0));
                            controls.setRadius(620);
                            camera.position.set(420, 260, 420);
                            camera.updateProjectionMatrix();
                        }
                        updateStatus('Kamera zurückgesetzt.', null);
                    });
                }
            
                ['dragenter', 'dragover'].forEach((type) => {
                    viewport.addEventListener(type, (event) => {
                        event.preventDefault();
                        viewport.classList.add('drag-active');
                    });
                });
            
                ['dragleave', 'drop'].forEach((type) => {
                    viewport.addEventListener(type, (event) => {
                        event.preventDefault();
                        if (type === 'drop') {
                            const file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
                            if (file) {
                                loadStepFile(file);
                            }
                        }
                        viewport.classList.remove('drag-active');
                    });
                });
            
                function animate() {
                    requestAnimationFrame(animate);
                    renderer.render(scene, camera);
                }
            
                animate();
            })();
        </script>
        </script>
        </body>
        </html>
        """

    return app


def main() -> None:
    """Launch the ASGI server using uvicorn."""
    import uvicorn

    app_env = os.getenv("APP_ENV", "development")
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = app_env != "production"

    uvicorn.run(
        "klipperiwc.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
        log_level=os.getenv("LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()

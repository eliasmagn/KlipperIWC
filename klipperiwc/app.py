"""Application entrypoint for KlipperIWC."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

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
                    <a href=\"/board-designer\">Board-Designer öffnen →</a>
                    <a class=\"secondary\" href=\"/printer-designer\">Drucker-Designer entdecken</a>
                </div>
            </header>

            <main>
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
                    display: grid;
                    grid-template-columns: minmax(260px, 320px) 1fr;
                    background: #0f172a;
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
                    border-right: 1px solid rgba(148, 163, 184, 0.3);
                    background: rgba(15, 23, 42, 0.85);
                    backdrop-filter: blur(14px);
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                }

                main {
                    padding: 1.5rem;
                    display: flex;
                    flex-direction: column;
                    gap: 1rem;
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

                .hint {
                    font-size: 0.85rem;
                    color: #94a3b8;
                    margin-top: -0.3rem;
                }

                @media (max-width: 900px) {
                    body {
                        display: flex;
                        flex-direction: column;
                    }

                    aside {
                        border-right: none;
                        border-bottom: 1px solid rgba(148, 163, 184, 0.3);
                        flex-direction: row;
                        flex-wrap: wrap;
                        gap: 1rem;
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
                <div class=\"canvas-shell\">
                    <svg id=\"boardCanvas\" viewBox=\"0 0 1280 720\" role=\"img\" aria-label=\"Board designer canvas\"></svg>
                </div>
            </main>

            <script>
                const boardCanvas = document.getElementById('boardCanvas');
                const rectTool = document.getElementById('rectTool');
                const circleTool = document.getElementById('circleTool');
                const panTool = document.getElementById('panTool');
                const colorPicker = document.getElementById('colorPicker');
                const shapeList = document.getElementById('shapeList');

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
                    <div class=\"control-group\">
                        <div class=\"control\">
                            <label for=\"backgroundUpload\">Hintergrundgrafik</label>
                            <input id=\"backgroundUpload\" type=\"file\" accept=\"image/*\" />
                            <p class=\"hint\">Unterstützt PNG, JPG und SVG. Das Bild legt die Dimension der Zeichenfläche fest.</p>
                        </div>
                        <div class=\"control\">
                            <label for=\"componentType\">Komponententyp</label>
                            <select id=\"componentType\">
                                <option value=\"switch\">Endstop / Schalter</option>
                                <option value=\"extruder\">Extruder / Hotend</option>
                                <option value=\"stepper\" selected>Stepper-Motor</option>
                                <option value=\"lead_screw\">Lead Screw / Z-Antrieb</option>
                                <option value=\"sensor\">Sensor</option>
                                <option value=\"fan\">Lüfter</option>
                                <option value=\"custom\">Benutzerdefiniert</option>
                            </select>
                        </div>
                        <div class=\"control rotational\">
                            <label for=\"rotationalDistance\">Rotationsdistanz (mm)</label>
                            <input id=\"rotationalDistance\" type=\"number\" step=\"0.01\" placeholder=\"z. B. 32.0\" />
                            <p class=\"hint\">Wird für Stepper- und Lead-Screw-Markierungen übernommen.</p>
                        </div>
                        <div class=\"control\">
                            <label for=\"highlightColor\">Farbe</label>
                            <input id=\"highlightColor\" type=\"color\" value=\"#22c55e\" />
                        </div>
                        <div class=\"control\">
                            <label>Werkzeuge</label>
                            <div class=\"toolbar\">
                                <button id=\"rectTool\" type=\"button\">Rechteck</button>
                                <button id=\"circleTool\" type=\"button\">Kreis</button>
                                <button id=\"arrowTool\" type=\"button\">Maßpfeil</button>
                                <button id=\"panTool\" type=\"button\">Verschieben</button>
                            </div>
                            <p class=\"hint\">Zeichne mit zwei Klicks. Pfeile benötigen Start- und Endpunkt sowie ein Maß. Vorgeschlagene Maße orientieren sich an Pixeln, eigene mm-Angaben können eingetragen werden.</p>
                        </div>
                    </div>
                    <div>
                        <h2>Markierungen</h2>
                        <div id=\"printerShapeList\" class=\"shape-list\"></div>
                    </div>
                </aside>
                <main>
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

# KlipperIWC

KlipperIWC ist eine FastAPI-basierte Backend-Anwendung, die als Grundlage für eine Integrations- und Steueroberfläche von Klipper-3D-Druckerinstallationen dient. Dieses Repository enthält alle Skripte, um die Software lokal, auf einem Server oder innerhalb eines Containers zu betreiben.

> **Hinweis:** Eine Benutzerverwaltung bzw. ein Login ist derzeit nicht vorgesehen und wird erst in einer späteren Phase ergänzt.

## Voraussetzungen

- Python 3.11 oder neuer
- Optional: Docker 24+

## Installation und Betrieb

### Produktionsdeployment

Das Skript `deploy.sh` richtet eine virtuelle Umgebung ein, installiert alle Abhängigkeiten und startet den Service als Daemon.

```bash
./deploy.sh
```

Logs werden im Verzeichnis `logs/app.log` geschrieben und die Prozess-ID liegt in `logs/app.pid`.

### Entwicklungsumgebung

Für lokale Entwicklung steht `deploy_dev.sh` bereit. Das Skript installiert alle Abhängigkeiten und gibt anschließend das Kommando aus, um den Server mit Live-Reload und Debug-Logging zu starten.

```bash
./deploy_dev.sh
# Hinweis aus dem Skript folgen, z. B.:
. .venv/bin/activate
export APP_ENV=development
export LOG_LEVEL=debug
uvicorn klipperiwc.app:create_app --factory --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### Docker

Ein containerisiertes Deployment ist über das bereitgestellte `Dockerfile` möglich.

```bash
docker build -t klipperiwc .
docker run -p 8000:8000 --env APP_ENV=production klipperiwc
```

## Projektstruktur

```
klipperiwc/          # FastAPI-Anwendung
├── __init__.py
└── app.py
requirements.txt     # Python-Abhängigkeiten
deploy.sh            # Produktionsdeployment
deploy_dev.sh        # Entwicklungssetup
Dockerfile           # Container-Build
```

## Weiterführende Schritte

Siehe `roadmap.md` für geplante Erweiterungen und `checklist.md` für den aktuellen Arbeitsfortschritt.

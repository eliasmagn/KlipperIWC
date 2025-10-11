# Roadmap

## Phase 1 – Basisdienst (aktuell)
- [x] Projektgrundstruktur und FastAPI-Basisdienst erstellen
- [x] Deployment-Skripte und Docker-Unterstützung bereitstellen
- [x] Board-Designer-Prototyp für Pin-Annotationen veröffentlichen
- [ ] API-Spezifikation und Pydantic-Modelle für Status-/Jobdaten bereitstellen
- [x] Klipper-Service-Layer für Status-/Jobdaten bereitstellen
- [ ] Persistente Statushistorie (SQLite) mit Migrationen und Aufbewahrungslogik implementieren

## Phase 2 – Beobachtung und Steuerung
- [ ] Websocket-Streaming für Echtzeit-Updates inklusive Gateway und Autorisierung integrieren
- [ ] Dashboard-Layout mit Navigation, Live-Widgets und Temperatur-/Jobvisualisierungen entwickeln
- [ ] Steuerbefehle (Start/Stop/Notaus) mit Sicherheitsmechanismen versehen
- [ ] Alarm- und Benachrichtigungssystem für kritische Ereignisse hinzufügen

## Phase 3 – Hardware- und Board-Definitionen
- [ ] JSON-Schema und Versionsverwaltung für Board-Definitionen etablieren
- [ ] Upload-Workflow für Board-Bilder inkl. Storage-Adapter und Moderation ergänzen
- [ ] Validierungslogik gegen MCU- und Pin-Datenbanken implementieren
- [ ] Öffentliche Bibliothek mit Board-Definitionen und Suchfunktion bereitstellen
- [ ] Vorbereitung für GitHub-zu-UI-Synchronisation der Definitionen treffen

## Phase 4 – Benutzeroberfläche
- [ ] Web-Frontend mit Dashboard, Verlaufsgrafiken und Konfigurationsseiten entwickeln
- [ ] Responsive Layout und dunkler Modus
- [ ] Internationalisierung der Oberfläche vorbereiten

## Phase 5 – Qualitätssicherung
- [ ] Automatisierte Tests (Unit, Integration) einführen
- [ ] Linting und Formatierung automatisieren
- [ ] CI/CD-Pipeline mit Deployment auf Testumgebung konfigurieren

## Phase 6 – Erweiterte Sicherheit und Benutzerverwaltung (später)
- [ ] Zugriffskonzepte und Benutzerrollen definieren
- [ ] Login- und Session-Management implementieren
- [ ] Erweiterte Audit- und Logging-Funktionen bereitstellen

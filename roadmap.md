# Roadmap

## Phase 1 – Basisdienst (aktuell)
- [x] Projektgrundstruktur und FastAPI-Basisdienst erstellen
- [x] Deployment-Skripte und Docker-Unterstützung bereitstellen
- [x] Board-Designer-Prototyp für Pin-Annotationen veröffentlichen
- [x] Datenbankbasis mit SQLite und Alembic vorbereiten
- [x] API-Spezifikation und Pydantic-Modelle für Status-/Jobdaten bereitstellen
- [x] Persistente Statushistorie (SQLite) inklusive Service-Layer und konfigurierbarer Aufbewahrungslogik (`STATUS_HISTORY_RETENTION_DAYS`) implementieren
- [x] Dashboard-Metrikservice und API-Routen für aggregierte Kennzahlen veröffentlichen
- [ ] Klipper-Service-Layer für Status-/Jobdaten mit realem Backend anbinden

## Phase 2 – Beobachtung und Steuerung
- [x] Websocket-Streaming für Echtzeit-Updates inklusive Gateway und Autorisierung integrieren (Auth & Rate-Limits folgen)
- [ ] Dashboard-Layout mit Navigation, Live-Widgets und Temperatur-/Jobvisualisierungen entwickeln
- [ ] Steuerbefehle (Start/Stop/Notaus) mit Sicherheitsmechanismen versehen
- [ ] Alarm- und Benachrichtigungssystem für kritische Ereignisse hinzufügen

## Phase 3 – Hardware- und Board-Definitionen
- [x] JSON-Schema und Versionsverwaltung für Board-Definitionen etablieren
- [x] API-Endpunkte zum Listen, Validieren und Aggregieren von Board-Revisionen bereitstellen
- [x] Upload-Workflow für Board-Bilder inkl. Storage-Adapter und Moderation ergänzen
- [x] API-Token-gestützte Moderationsfreigabe und Sichtbarkeitsfilter für Board-Assets etablieren
- [x] Persistente Registry-Tabellen und CRUD-API für Board- und Druckerdefinitionen schaffen
- [ ] Moderations-Dashboard mit Benachrichtigungskette entwerfen
- [ ] Validierungslogik gegen MCU- und Pin-Datenbanken implementieren
- [ ] Öffentliche Bibliothek mit Board-Definitionen und Suchfunktion bereitstellen
- [ ] Vorbereitung für GitHub-zu-UI-Synchronisation der Definitionen treffen

## Phase 4 – Benutzeroberfläche
- [x] Landingpage mit Einstieg in Board- und Drucker-Designer bereitstellen
- [x] Drucker-Designer mit Upload-, Markierungs- und Maßwerkzeugen bereitstellen
- [x] ViewBox-korrigierte Cursorzuordnung für Board- und Drucker-Designer herstellen
- [x] 3D-CAD-Ansichten mit STEP-Import und Markerunterstützung in Board- und Drucker-Designer integrieren
- [x] Drucker-Designer um Profil-Erfassung und Klipper-Konfigurationskatalog mit Dokumentationslinks erweitern
- [ ] Web-Frontend mit Dashboard, Verlaufsgrafiken und Konfigurationsseiten entwickeln
- [ ] Bearbeitungsfunktionen (Bewegen/Löschen) in Board- und Drucker-Designer ergänzen
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
- [ ] Freigabe-Workflows und Einladungen für gemeinsam genutzte Definitionen entwickeln

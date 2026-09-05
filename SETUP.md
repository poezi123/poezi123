# Setup – poezi123 GitHub Profile

## 1. Repository erstellen

Erstelle auf GitHub ein **öffentliches** Repository mit exakt diesem Namen:

`poezi123`

Der Repository-Name muss exakt deinem GitHub-Username entsprechen.

## 2. Dateien hochladen

Lade den kompletten Inhalt dieses Pakets in das Repository hoch:

- `README.md`
- `assets/github-stats.svg`
- `scripts/generate_stats.py`
- `.github/workflows/update-stats.yml`
- `.github/workflows/snake.yml`

## 3. GitHub Actions Schreibrechte geben

Öffne:

**Settings → Actions → General → Workflow permissions**

Wähle **Read and write permissions** und speichere.

## 4. Workflows einmal manuell starten

Unter **Actions**:

1. `Update profile stats` → **Run workflow**
2. `Generate contribution snake` → **Run workflow**

Der Stats-Workflow ersetzt danach automatisch die Platzhalter-SVG mit deinen echten Daten.
Der Snake-Workflow erzeugt den Branch `output`.

## 5. Profil ansehen

Öffne danach dein GitHub-Profil. Die `README.md` des Repositories `poezi123` erscheint automatisch auf deiner Profilseite.

## Automatische Aktualisierung

- Engineering Stats: täglich
- Contribution Snake: täglich

## Farben ändern

In `scripts/generate_stats.py`:

- Hintergrund: `#0d1117`
- Cyan: `#22d3ee`
- Blau: `#2f81f7`
- GitHub-Grün: `#3fb950`

## Hinweis

Dein Alter ist absichtlich nicht in der öffentlichen README enthalten. Für ein Developer-/Security-Profil sind Projekte, Skills und Interessen relevanter.

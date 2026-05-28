# Generador de Horarios Evolutivo — PRD

## Original Problem Statement
"A mi me toco la del horario, ayudame hacer la pagina web" — Tarea universitaria de Computación Evolutiva (Proyecto 2: Generador de Horarios Escolares). Crear una aplicación web funcional que utilice un algoritmo genético para generar horarios escolares cumpliendo restricciones duras y minimizando huecos (dead time).

## Architecture
- **Frontend**: React 19 + TailwindCSS + shadcn/ui + Phosphor Icons + Recharts. Single dashboard page (`/app/frontend/src/pages/Dashboard.jsx`).
- **Backend**: FastAPI + Motor (async MongoDB). All routes under `/api`.
- **DB**: MongoDB collections: `profesores`, `grupos`, `materias`, `config`, `schedule`.
- **Algoritmo Genético**: `/app/backend/genetic.py` (selección por torneo, crossover uniforme, mutación uniforme, elitismo 2).
- **Idioma UI**: Español.

## User Personas
- **Estudiante**: presenta la tarea con la app funcional.
- **Profesor evaluador**: revisa que cumpla los requisitos del PDF (calendario, CSV upload, sliders, métricas, convergencia, filtros).

## Core Requirements (static)
1. Carga de datos: CSV/Excel uploader + formularios manuales para Profesores, Grupos, Materias.
2. Configuración: días de la semana, hora_inicio, hora_fin.
3. Parámetros del algoritmo (sliders): tamaño de población (10–200), generaciones (10–500), probabilidad de mutación (0.01–1.0).
4. Botón "Generar Horarios".
5. Calendario semanal (grid) con bloques de colores pastel por materia. Filtros por Grupo y Profesor.
6. Gráfica de convergencia (fitness vs generaciones).
7. Panel de métricas: choques de profesor, choques de grupo, horas sin asignar, total reglas rotas.
8. Datos de ejemplo precargados (auto-seed en primera carga).

## What's been implemented (2026-02-28)
- [x] Backend: 12 endpoints REST (`/api/seed`, `/api/clear`, `/api/data`, `/api/profesores`, `/api/grupos`, `/api/materias`, `/api/config`, `/api/upload-csv`, `/api/generate`, `/api/last-schedule`).
- [x] Algoritmo genético funcional: convergió de fitness 2031 → 0 sin conflictos en datos de ejemplo.
- [x] Dashboard React completo con sidebar y main content (sticky).
- [x] Auto-seed de datos de ejemplo (4 profesores, 3 grupos, 9 materias) en la primera visita.
- [x] CSV/Excel upload con upsert por nombre de profesor/grupo.
- [x] Diálogos para agregar profesores/grupos/materias manualmente.
- [x] Calendario semanal con bloques de colores pastel; detección visual de conflictos reales (mismo profesor o grupo en mismo slot → borde rojo).
- [x] Gráfica de convergencia con Recharts (AreaChart).
- [x] Panel de métricas con tarjetas codificadas por color (success/warning/error).
- [x] Filtros por grupo y profesor.
- [x] Tipografía Outfit (headings) + Work Sans (body) según design guidelines.
- [x] Toaster (sonner) para feedback.
- [x] Testing backend: 16/16 pytest tests passed.

## Prioritized Backlog
### P1
- [ ] Exportar horario a PDF/Excel/imagen.
- [ ] Restricciones por profesor (días/horarios no disponibles).
- [ ] Materias deduplicadas en upload CSV (upsert por nombre+prof+grupo).

### P2
- [ ] Sistema multi-escuela (workspaces).
- [ ] Comparar varias corridas del algoritmo lado a lado.
- [ ] Modo "comparar parámetros" (grid search).
- [ ] Historial de horarios generados.
- [ ] DELETE endpoints que devuelvan 404 si no existe.

## Notes
- El backend usa `@app.on_event` (deprecado pero funcional).
- CORS abierto a `*` para simplicidad académica.

"""Sample data preloaded for quick demo."""

SAMPLE_PROFESORES = [
    {"id": "prof-1", "nombre": "Dra. Ana García"},
    {"id": "prof-2", "nombre": "Mtro. Luis Torres"},
    {"id": "prof-3", "nombre": "Ing. Carmen Ruiz"},
    {"id": "prof-4", "nombre": "Dr. Roberto Méndez"},
]

SAMPLE_GRUPOS = [
    {"id": "grp-A", "nombre": "1° A"},
    {"id": "grp-B", "nombre": "1° B"},
    {"id": "grp-C", "nombre": "2° A"},
]

SAMPLE_MATERIAS = [
    {"id": "mat-1", "nombre": "Matemáticas", "profesor_id": "prof-1", "grupo_id": "grp-A", "horas_semanales": 4},
    {"id": "mat-2", "nombre": "Física",      "profesor_id": "prof-2", "grupo_id": "grp-A", "horas_semanales": 3},
    {"id": "mat-3", "nombre": "Química",     "profesor_id": "prof-3", "grupo_id": "grp-A", "horas_semanales": 3},
    {"id": "mat-4", "nombre": "Matemáticas", "profesor_id": "prof-1", "grupo_id": "grp-B", "horas_semanales": 4},
    {"id": "mat-5", "nombre": "Historia",    "profesor_id": "prof-4", "grupo_id": "grp-B", "horas_semanales": 3},
    {"id": "mat-6", "nombre": "Biología",    "profesor_id": "prof-3", "grupo_id": "grp-B", "horas_semanales": 3},
    {"id": "mat-7", "nombre": "Cálculo",     "profesor_id": "prof-1", "grupo_id": "grp-C", "horas_semanales": 4},
    {"id": "mat-8", "nombre": "Programación","profesor_id": "prof-2", "grupo_id": "grp-C", "horas_semanales": 4},
    {"id": "mat-9", "nombre": "Inglés",      "profesor_id": "prof-4", "grupo_id": "grp-C", "horas_semanales": 3},
]

SAMPLE_CONFIG = {
    "dias": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
    "hora_inicio": 7,
    "hora_fin": 14,
}

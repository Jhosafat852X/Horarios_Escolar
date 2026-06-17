from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import io
import uuid
import logging
import re
import unicodedata
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pandas as pd

try:
    from .genetic import run_genetic_algorithm
except ImportError:
    from genetic import run_genetic_algorithm
try:
    import pdfplumber
except Exception:
    pdfplumber = None
try:
    from .schedule_parser import parse_schedule_sections
except ImportError:
    from schedule_parser import parse_schedule_sections
try:
    from .sample_data import SAMPLE_PROFESORES, SAMPLE_GRUPOS, SAMPLE_MATERIAS, SAMPLE_CARRERAS, SAMPLE_CONFIG
except ImportError:
    from sample_data import SAMPLE_PROFESORES, SAMPLE_GRUPOS, SAMPLE_MATERIAS, SAMPLE_CARRERAS, SAMPLE_CONFIG

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="Generador de Horarios Evolutivo")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Models ----------
class Profesor(BaseModel):
    id: str = Field(default_factory=lambda: f"prof-{uuid.uuid4().hex[:6]}")
    nombre: str

class Carrera(BaseModel):
    id: str = Field(default_factory=lambda: f"car-{uuid.uuid4().hex[:6]}")
    nombre: str

class Grupo(BaseModel):
    id: str = Field(default_factory=lambda: f"grp-{uuid.uuid4().hex[:6]}")
    nombre: str
    carrera_id: Optional[str] = None
    semestre: Optional[int] = None
    seccion: Optional[str] = None
    codigo: Optional[str] = None

class Materia(BaseModel):
    id: str = Field(default_factory=lambda: f"mat-{uuid.uuid4().hex[:6]}")
    nombre: str
    profesor_id: str
    grupo_id: str
    horas_semanales: int
    carrera_id: Optional[str] = None
    preferred_slots: Optional[List[Dict[str, int]]] = None

class Config(BaseModel):
    dias: List[str]
    hora_inicio: int
    hora_fin: int

class GenerateRequest(BaseModel):
    pop_size: int = 500
    generations: int = 150
    mutation_rate: float = 0.05
    crossover_rate: float = 0.5
    dias: Optional[List[str]] = None
    hora_inicio: Optional[int] = None
    hora_fin: Optional[int] = None

class ParseScheduleRequest(BaseModel):
    text: str

# ---------- Helpers ----------
def strip_id(doc):
    if doc and "_id" in doc:
        doc.pop("_id", None)
    return doc

def normalize_cell(value):
    if value is None:
        return ""
    return " ".join(str(value).replace("\n", " ").split()).strip()

def normalize_key(value):
    text = normalize_cell(value).upper()
    text = "".join(
        char for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return " ".join(text.split())

def professor_for_subject(subject, professor_map):
    subject_key = normalize_key(subject)
    if subject_key in professor_map:
        return professor_map[subject_key]
    singular_key = re.sub(r"\bTECNOLOGIAS\b", "TECNOLOGIA", subject_key)
    if singular_key in professor_map:
        return professor_map[singular_key]
    for key, professor in professor_map.items():
        if subject_key and (subject_key in key or key in subject_key):
            return professor
    return "SIN ASIGNAR"

def is_english_subject(subject):
    return normalize_key(subject) == "INGLES"

def group_does_not_take_english(group_name, semester_text=None, semester=None):
    group_key = normalize_key(group_name)
    semester_key = normalize_key(semester_text)
    if group_key == "1008":
        return True
    if semester_key in {"DECIMO", "10", "10O"}:
        return True
    if semester is not None:
        try:
            return int(semester) >= 10
        except Exception:
            return False
    return False

def parse_page_metadata(text):
    metadata = {}
    carrera_match = re.search(r"CICLO ESCOLAR\s+[^\n]+\n(.+?)\nAULA:", text, re.IGNORECASE)
    if carrera_match:
        metadata["carrera"] = normalize_cell(carrera_match.group(1))
    aula_match = re.search(r"AULA:\s*(.+)", text, re.IGNORECASE)
    if aula_match:
        metadata["aula"] = normalize_cell(aula_match.group(1))
    grupo_match = re.search(r"GRUPO:\s*([^\s]+)", text, re.IGNORECASE)
    if grupo_match:
        metadata["grupo"] = normalize_cell(grupo_match.group(1))
    semestre_match = re.search(r"SEMESTRE:\s*([^\n]+)", text, re.IGNORECASE)
    if semestre_match:
        metadata["semestre_texto"] = normalize_cell(semestre_match.group(1))
    return metadata

def parse_professor_map_from_text(text):
    if "ASIGNATURA" not in text.upper() or "PROFESOR" not in text.upper():
        return {}
    _, professor_block = re.split(r"ASIGNATURA\s+PROFESOR", text, maxsplit=1, flags=re.IGNORECASE)
    professor_map = {}
    professor_markers = r"(?:DR\.|DRA\.|M\.I\.|M\.C\.|M\.\s*EN\s*C\.|ING\.|L\.I\.|LIC\.|M\.A\.)"
    for raw_line in professor_block.splitlines():
        line = normalize_cell(raw_line)
        if not line:
            continue
        match = re.search(professor_markers, line, re.IGNORECASE)
        if not match:
            continue
        subject = normalize_cell(line[:match.start()])
        professor = normalize_cell(line[match.start():])
        if subject and professor:
            professor_map[normalize_key(subject)] = professor
    return professor_map

def parse_hour(value):
    match = re.search(r"(\d{1,2})(?::\d{2})?", normalize_cell(value))
    if not match:
        return None
    return int(match.group(1))

def split_slot_subjects(value):
    cell = normalize_cell(value)
    if not cell:
        return []
    ignored = {
        "BIBLIOTECA",
        "ASESORÍA",
        "ASESORIA",
        "TUTORÍA",
        "TUTORIA",
        "SALA DE CÓMPUTO",
        "SALA DE COMPUTO",
    }
    ignored_keys = {normalize_key(item) for item in ignored}
    ignored_keys.update({
        "BIBBLIOTECA",
        "ASESORIA",
        "TUTORIA",
        "TUTORIAS",
        "SALA DE COMPUTO",
    })
    subjects = []
    for part in re.split(r"\s*/\s*", cell):
        subject = normalize_cell(part)
        if subject and normalize_key(subject) not in ignored_keys:
            subjects.append(subject)
    return subjects

def parse_university_schedule_pdf(content):
    if pdfplumber is None:
        raise HTTPException(
            status_code=500,
            detail="Soporte para PDF no está instalado en el servidor. Instala 'pdfplumber' en requirements.txt",
        )

    sections = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            tables = page.extract_tables() or []
            metadata = parse_page_metadata(text)
            schedule_table = None
            professor_map = parse_professor_map_from_text(text)

            for table in tables:
                if not table:
                    continue
                first_row = [normalize_cell(cell).upper() for cell in table[0]]
                if len(first_row) >= 4 and first_row[0] == "CARRERA" and first_row[2] == "GRUPO":
                    metadata["carrera"] = normalize_cell(table[0][1])
                    metadata["grupo"] = normalize_cell(table[0][3])
                    if len(table) > 1 and len(table[1]) >= 4:
                        metadata["aula"] = normalize_cell(table[1][1])
                        metadata["semestre_texto"] = normalize_cell(table[1][3])
                elif first_row and first_row[0] == "HORA":
                    schedule_table = table
                elif len(table) >= 2 and any("ASIGNATURA" in cell for cell in first_row):
                    for row in table[2:]:
                        if len(row) < 2:
                            continue
                        subject = normalize_cell(row[0])
                        professor = normalize_cell(row[1])
                        if subject and professor:
                            professor_map[normalize_key(subject)] = professor

            if not metadata.get("grupo") or not schedule_table:
                continue

            subject_hours = {}
            subject_slots = {}
            for row in schedule_table[1:]:
                if not row:
                    continue
                hour = parse_hour(row[0])
                if hour is None:
                    continue
                for day_idx, cell in enumerate(row[1:]):
                    for subject in split_slot_subjects(cell):
                        subject_hours[subject] = subject_hours.get(subject, 0) + 1
                        subject_slots.setdefault(subject, []).append({
                            "day": day_idx,
                            "hour": hour,
                        })

            sections.append({
                "carrera": metadata.get("carrera"),
                "grupo": metadata.get("grupo"),
                "semestre_texto": metadata.get("semestre_texto"),
                "aula": metadata.get("aula"),
                "materias": [
                    {
                        "materia": subject,
                        "profesor": professor_for_subject(subject, professor_map),
                        "horas_semanales": hours,
                        "preferred_slots": subject_slots.get(subject, []),
                    }
                    for subject, hours in sorted(subject_hours.items())
                ],
            })

    return sections

async def import_schedule_sections(sections):
    prof_map = {}
    grup_map = {}
    carrera_map = {}
    existing_profs = await db.profesores.find({}, {"_id": 0}).to_list(1000)
    existing_grupos = await db.grupos.find({}, {"_id": 0}).to_list(1000)
    existing_carreras = await db.carreras.find({}, {"_id": 0}).to_list(1000)
    for p in existing_profs:
        prof_map[normalize_key(p["nombre"])] = p["id"]
    for g in existing_grupos:
        grup_map[normalize_key(g["nombre"])] = g["id"]
    for c in existing_carreras:
        carrera_map[normalize_key(c["nombre"])] = c["id"]

    new_materias = []
    grupos_creados = 0
    profesores_creados = 0
    carreras_creadas = 0

    for section in sections:
        carrera_name = section.get("carrera") or "SIN CARRERA"
        carrera_key = normalize_key(carrera_name)
        if carrera_key not in carrera_map:
            carrera = Carrera(nombre=carrera_name)
            await db.carreras.insert_one(carrera.model_dump())
            carrera_map[carrera_key] = carrera.id
            carreras_creadas += 1

        grupo_name = section.get("grupo") or "SIN GRUPO"
        grupo_key = normalize_key(grupo_name)
        if grupo_key not in grup_map:
            grupo = Grupo(
                nombre=grupo_name,
                carrera_id=carrera_map[carrera_key],
                seccion=grupo_name,
                codigo=grupo_name,
            )
            await db.grupos.insert_one(grupo.model_dump())
            grup_map[grupo_key] = grupo.id
            grupos_creados += 1

        for item in section.get("materias", []):
            if is_english_subject(item.get("materia")) and group_does_not_take_english(
                grupo_name,
                section.get("semestre_texto"),
            ):
                continue
            prof_name = item.get("profesor") or "SIN ASIGNAR"
            if normalize_key(prof_name) == "SIN ASIGNAR":
                prof_name = f"SIN ASIGNAR - {grupo_name} - {item.get('materia')}"
            prof_key = normalize_key(prof_name)
            if prof_key not in prof_map:
                profesor = Profesor(nombre=prof_name)
                await db.profesores.insert_one(profesor.model_dump())
                prof_map[prof_key] = profesor.id
                profesores_creados += 1
            materia = Materia(
                nombre=item["materia"],
                profesor_id=prof_map[prof_key],
                grupo_id=grup_map[grupo_key],
                horas_semanales=int(item["horas_semanales"]),
                carrera_id=carrera_map[carrera_key],
                preferred_slots=item.get("preferred_slots") or None,
            )
            new_materias.append(materia.model_dump())

    if new_materias:
        await db.materias.insert_many(new_materias)

    return {
        "ok": True,
        "modo": "pdf_horario_cuadricula",
        "grupos_creados": grupos_creados,
        "profesores_creados": profesores_creados,
        "carreras_creadas": carreras_creadas,
        "materias_creadas": len(new_materias),
    }

async def get_config_doc():
    cfg = await db.config.find_one({"_id": "main"}, {"_id": 0})
    if not cfg:
        cfg = dict(SAMPLE_CONFIG)
    return cfg

# ---------- Routes ----------
@api_router.get("/")
async def root():
    return {"status": "ok", "service": "Generador de Horarios Evolutivo"}

@api_router.get("/data")
async def get_all_data():
    profesores = await db.profesores.find({}, {"_id": 0}).to_list(1000)
    grupos = await db.grupos.find({}, {"_id": 0}).to_list(1000)
    materias = await db.materias.find({}, {"_id": 0}).to_list(1000)
    carreras = await db.carreras.find({}, {"_id": 0}).to_list(1000)
    config = await get_config_doc()
    return {
        "profesores": profesores,
        "grupos": grupos,
        "materias": materias,
        "carreras": carreras,
        "config": config,
    }

@api_router.post("/seed")
async def seed_sample_data():
    await db.profesores.delete_many({})
    await db.grupos.delete_many({})
    await db.materias.delete_many({})
    await db.carreras.delete_many({})
    if SAMPLE_PROFESORES:
        await db.profesores.insert_many([dict(p) for p in SAMPLE_PROFESORES])
    if SAMPLE_CARRERAS:
        await db.carreras.insert_many([dict(c) for c in SAMPLE_CARRERAS])
    if SAMPLE_GRUPOS:
        await db.grupos.insert_many([dict(g) for g in SAMPLE_GRUPOS])
    if SAMPLE_MATERIAS:
        await db.materias.insert_many([dict(m) for m in SAMPLE_MATERIAS])
    await db.config.update_one(
        {"_id": "main"},
        {"$set": {**SAMPLE_CONFIG}},
        upsert=True,
    )
    return {"ok": True, "message": "Datos de ejemplo cargados."}

@api_router.delete("/clear")
async def clear_all():
    await db.profesores.delete_many({})
    await db.grupos.delete_many({})
    await db.materias.delete_many({})
    await db.carreras.delete_many({})
    await db.schedule.delete_many({})
    return {"ok": True}

# Profesores
@api_router.post("/profesores", response_model=Profesor)
async def create_profesor(p: Profesor):
    await db.profesores.insert_one(p.model_dump())
    return p

@api_router.delete("/profesores/{prof_id}")
async def delete_profesor(prof_id: str):
    await db.profesores.delete_one({"id": prof_id})
    # also remove materias that reference it
    await db.materias.delete_many({"profesor_id": prof_id})
    return {"ok": True}

# Grupos
@api_router.post("/grupos", response_model=Grupo)
async def create_grupo(g: Grupo):
    await db.grupos.insert_one(g.model_dump())
    return g

@api_router.delete("/grupos/{grp_id}")
async def delete_grupo(grp_id: str):
    await db.grupos.delete_one({"id": grp_id})
    await db.materias.delete_many({"grupo_id": grp_id})
    return {"ok": True}

# Carreras
@api_router.get("/carreras")
async def get_carreras():
    carreras = await db.carreras.find({}, {"_id": 0}).to_list(1000)
    return {"carreras": carreras}

@api_router.post("/carreras", response_model=Carrera)
async def create_carrera(c: Carrera):
    await db.carreras.insert_one(c.model_dump())
    return c

@api_router.delete("/carreras/{carrera_id}")
async def delete_carrera(carrera_id: str):
    await db.carreras.delete_one({"id": carrera_id})
    await db.grupos.update_many({"carrera_id": carrera_id}, {"$set": {"carrera_id": None}})
    return {"ok": True}

# Materias
@api_router.post("/materias", response_model=Materia)
async def create_materia(m: Materia):
    await db.materias.insert_one(m.model_dump())
    return m

@api_router.delete("/materias/{mat_id}")
async def delete_materia(mat_id: str):
    await db.materias.delete_one({"id": mat_id})
    return {"ok": True}

# Config
@api_router.put("/config")
async def update_config(cfg: Config):
    await db.config.update_one(
        {"_id": "main"},
        {"$set": cfg.model_dump()},
        upsert=True,
    )
    return {"ok": True, "config": cfg.model_dump()}

# CSV upload
@api_router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """Accepts CSV/Excel with columns: profesor, grupo, materia, horas_semanales.
    Will create/upsert profesores, grupos and materias.
    """
    content = await file.read()
    name = (file.filename or "").lower()
    try:
        if name.endswith(".pdf"):
            if pdfplumber is None:
                raise HTTPException(
                    status_code=500,
                    detail="Soporte para PDF no está instalado en el servidor. Instala 'pdfplumber' en requirements.txt",
                )
            sections = parse_university_schedule_pdf(content)
            if sections:
                return await import_schedule_sections(sections)

            tables = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    try:
                        tbl = page.extract_table()
                    except Exception:
                        tbl = None
                    if tbl and len(tbl) > 1:
                        df_page = pd.DataFrame(tbl[1:], columns=tbl[0])
                        tables.append(df_page)
                if tables:
                    df = pd.concat(tables, ignore_index=True)
                else:
                    # fallback: try extract text and parse CSV-like content
                    text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                    try:
                        df = pd.read_csv(io.StringIO(text))
                    except Exception:
                        raise HTTPException(
                            status_code=400,
                            detail=(
                                "PDF no contiene una tabla importable con columnas "
                                "profesor, grupo, materia, horas_semanales. "
                                "Asegúrate de subir un PDF con tabla estructurada o usa el endpoint "
                                "/api/parse-schedule-text para analizar horarios en formato de cuadrícula."
                            ),
                        )
        elif name.endswith(".xlsx") or name.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo: {e}")

    df.columns = [c.strip().lower() for c in df.columns]
    required = {"profesor", "grupo", "materia", "horas_semanales"}
    if not required.issubset(set(df.columns)):
        if name.endswith(".pdf"):
            sections = parse_university_schedule_pdf(content)
            if sections:
                return await import_schedule_sections(sections)
        message = f"Faltan columnas. Requeridas: {sorted(required)}"
        if name.endswith(".pdf"):
            message = (
                "PDF no contiene las columnas requeridas. "
                f"Necesitas: {sorted(required)}. "
                "Si tu archivo es un horario en formato de cuadricula, usa /api/parse-schedule-text."
            )
        raise HTTPException(status_code=400, detail=message)

    optional_columns = set(df.columns) & {"carrera", "semestre", "seccion", "codigo"}

    # Build/upsert profesores, carreras and grupos by nombre
    prof_map = {}
    grup_map = {}
    carrera_map = {}
    existing_profs = await db.profesores.find({}, {"_id": 0}).to_list(1000)
    existing_grupos = await db.grupos.find({}, {"_id": 0}).to_list(1000)
    existing_carreras = await db.carreras.find({}, {"_id": 0}).to_list(1000)
    for p in existing_profs:
        prof_map[p["nombre"].strip().lower()] = p["id"]
    for g in existing_grupos:
        grup_map[g["nombre"].strip().lower()] = g["id"]
    for c in existing_carreras:
        carrera_map[c["nombre"].strip().lower()] = c["id"]

    new_materias = []
    for _, row in df.iterrows():
        prof_name = str(row["profesor"]).strip()
        grp_name = str(row["grupo"]).strip()
        mat_name = str(row["materia"]).strip()
        carrera_name = str(row["carrera"]).strip() if "carrera" in df.columns and pd.notna(row["carrera"]) else None
        semestre = None
        if "semestre" in df.columns and pd.notna(row["semestre"]):
            try:
                semestre = int(row["semestre"])
            except Exception:
                semestre = None
        seccion = str(row["seccion"]).strip() if "seccion" in df.columns and pd.notna(row["seccion"]) else None
        codigo = str(row["codigo"]).strip() if "codigo" in df.columns and pd.notna(row["codigo"]) else None
        try:
            horas = int(row["horas_semanales"])
        except Exception:
            continue
        key_p = prof_name.lower()
        key_g = grp_name.lower()
        if is_english_subject(mat_name) and group_does_not_take_english(
            grp_name,
            semester=semestre,
        ):
            continue
        carrera_id = None
        if carrera_name:
            key_c = carrera_name.lower()
            if key_c not in carrera_map:
                c = Carrera(nombre=carrera_name)
                await db.carreras.insert_one(c.model_dump())
                carrera_map[key_c] = c.id
            carrera_id = carrera_map[key_c]
        if key_p not in prof_map:
            p = Profesor(nombre=prof_name)
            await db.profesores.insert_one(p.model_dump())
            prof_map[key_p] = p.id
        if key_g not in grup_map:
            if not codigo:
                codigo = grp_name
            g = Grupo(
                nombre=grp_name,
                carrera_id=carrera_id,
                semestre=semestre,
                seccion=seccion,
                codigo=codigo,
            )
            await db.grupos.insert_one(g.model_dump())
            grup_map[key_g] = g.id
        m = Materia(
            nombre=mat_name,
            profesor_id=prof_map[key_p],
            grupo_id=grup_map[key_g],
            horas_semanales=horas,
            carrera_id=carrera_id,
        )
        new_materias.append(m.model_dump())

    if new_materias:
        await db.materias.insert_many(new_materias)

    return {"ok": True, "materias_creadas": len(new_materias)}

@api_router.post("/parse-schedule-text")
async def parse_schedule_text(req: ParseScheduleRequest):
    sections = parse_schedule_sections(req.text)
    if not sections:
        raise HTTPException(status_code=400, detail="No se encontró texto válido de horario.")
    return {"ok": True, "sections": sections}

# Generate
@api_router.post("/generate")
async def generate_schedule(req: GenerateRequest):
    materias = await db.materias.find({}, {"_id": 0}).to_list(1000)
    if not materias:
        raise HTTPException(status_code=400, detail="No hay materias para programar.")
    cfg = await get_config_doc()
    dias = req.dias or cfg["dias"]
    hora_inicio = req.hora_inicio if req.hora_inicio is not None else cfg["hora_inicio"]
    hora_fin = req.hora_fin if req.hora_fin is not None else cfg["hora_fin"]

    if hora_fin <= hora_inicio:
        raise HTTPException(status_code=400, detail="hora_fin debe ser mayor que hora_inicio")

    result = run_genetic_algorithm(
        materias=materias,
        dias=dias,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        pop_size=req.pop_size,
        generations=req.generations,
        mutation_rate=req.mutation_rate,
        crossover_rate=req.crossover_rate,
    )

    # store last schedule
    await db.schedule.update_one(
        {"_id": "last"},
        {"$set": {**result, "params": req.model_dump(), "dias": dias,
                  "hora_inicio": hora_inicio, "hora_fin": hora_fin}},
        upsert=True,
    )

    return {
        **result,
        "dias": dias,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
    }

@api_router.get("/last-schedule")
async def get_last_schedule():
    doc = await db.schedule.find_one({"_id": "last"}, {"_id": 0})
    return doc or {}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import io
import uuid
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import pandas as pd

from genetic import run_genetic_algorithm
from sample_data import SAMPLE_PROFESORES, SAMPLE_GRUPOS, SAMPLE_MATERIAS, SAMPLE_CONFIG

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

class Grupo(BaseModel):
    id: str = Field(default_factory=lambda: f"grp-{uuid.uuid4().hex[:6]}")
    nombre: str

class Materia(BaseModel):
    id: str = Field(default_factory=lambda: f"mat-{uuid.uuid4().hex[:6]}")
    nombre: str
    profesor_id: str
    grupo_id: str
    horas_semanales: int

class Config(BaseModel):
    dias: List[str]
    hora_inicio: int
    hora_fin: int

class GenerateRequest(BaseModel):
    pop_size: int = 60
    generations: int = 150
    mutation_rate: float = 0.05
    dias: Optional[List[str]] = None
    hora_inicio: Optional[int] = None
    hora_fin: Optional[int] = None

# ---------- Helpers ----------
def strip_id(doc):
    if doc and "_id" in doc:
        doc.pop("_id", None)
    return doc

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
    config = await get_config_doc()
    return {
        "profesores": profesores,
        "grupos": grupos,
        "materias": materias,
        "config": config,
    }

@api_router.post("/seed")
async def seed_sample_data():
    await db.profesores.delete_many({})
    await db.grupos.delete_many({})
    await db.materias.delete_many({})
    if SAMPLE_PROFESORES:
        await db.profesores.insert_many([dict(p) for p in SAMPLE_PROFESORES])
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
        if name.endswith(".xlsx") or name.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo: {e}")

    df.columns = [c.strip().lower() for c in df.columns]
    required = {"profesor", "grupo", "materia", "horas_semanales"}
    if not required.issubset(set(df.columns)):
        raise HTTPException(
            status_code=400,
            detail=f"Faltan columnas. Requeridas: {sorted(required)}",
        )

    # Build/upsert profesores and grupos by nombre
    prof_map = {}
    grup_map = {}
    existing_profs = await db.profesores.find({}, {"_id": 0}).to_list(1000)
    existing_grupos = await db.grupos.find({}, {"_id": 0}).to_list(1000)
    for p in existing_profs:
        prof_map[p["nombre"].strip().lower()] = p["id"]
    for g in existing_grupos:
        grup_map[g["nombre"].strip().lower()] = g["id"]

    new_materias = []
    for _, row in df.iterrows():
        prof_name = str(row["profesor"]).strip()
        grp_name = str(row["grupo"]).strip()
        mat_name = str(row["materia"]).strip()
        try:
            horas = int(row["horas_semanales"])
        except Exception:
            continue
        key_p = prof_name.lower()
        key_g = grp_name.lower()
        if key_p not in prof_map:
            p = Profesor(nombre=prof_name)
            await db.profesores.insert_one(p.model_dump())
            prof_map[key_p] = p.id
        if key_g not in grup_map:
            g = Grupo(nombre=grp_name)
            await db.grupos.insert_one(g.model_dump())
            grup_map[key_g] = g.id
        m = Materia(
            nombre=mat_name,
            profesor_id=prof_map[key_p],
            grupo_id=grup_map[key_g],
            horas_semanales=horas,
        )
        new_materias.append(m.model_dump())

    if new_materias:
        await db.materias.insert_many(new_materias)

    return {"ok": True, "materias_creadas": len(new_materias)}

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

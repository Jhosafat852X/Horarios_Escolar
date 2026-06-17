"""Backend tests for Generador de Horarios Escolares (Evolutive Computation)."""
import io
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    # fallback to reading frontend/.env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().strip('"')
                break
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="session")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session", autouse=True)
def _reset_state(client):
    # Ensure clean known state at start
    client.delete(f"{API}/clear", timeout=30)
    yield


# ---------- Health ----------
class TestHealth:
    def test_root(self, client):
        r = client.get(f"{API}/", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"
        assert "service" in data


# ---------- Seed + Data ----------
class TestSeedAndData:
    def test_seed(self, client):
        r = client.post(f"{API}/seed", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("ok") is True

    def test_get_data_after_seed(self, client):
        r = client.get(f"{API}/data", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert len(data["profesores"]) == 4
        assert len(data["grupos"]) == 3
        assert len(data["materias"]) == 9
        cfg = data["config"]
        assert cfg["hora_inicio"] == 7
        assert cfg["hora_fin"] == 14
        assert isinstance(cfg["dias"], list) and len(cfg["dias"]) == 5
        # Ensure _id is excluded
        for p in data["profesores"]:
            assert "_id" not in p
        for g in data["grupos"]:
            assert "_id" not in g
        for m in data["materias"]:
            assert "_id" not in m


# ---------- Profesor CRUD ----------
class TestProfesor:
    def test_create_profesor_and_persist(self, client):
        payload = {"nombre": "TEST_Profesor_X"}
        r = client.post(f"{API}/profesores", json=payload, timeout=30)
        assert r.status_code == 200
        prof = r.json()
        assert prof["nombre"] == "TEST_Profesor_X"
        assert prof["id"].startswith("prof-")

        # verify via /data
        r = client.get(f"{API}/data", timeout=30)
        ids = [p["id"] for p in r.json()["profesores"]]
        assert prof["id"] in ids

        # save for later
        pytest.profesor_test_id = prof["id"]

    def test_delete_profesor_cascades_materias(self, client):
        # create a profesor + grupo + materia, then delete profesor and verify materia removed
        prof = client.post(f"{API}/profesores", json={"nombre": "TEST_Casc_Prof"}, timeout=30).json()
        grp = client.post(f"{API}/grupos", json={"nombre": "TEST_Casc_Grp_P"}, timeout=30).json()
        mat = client.post(
            f"{API}/materias",
            json={"nombre": "TEST_M_P", "profesor_id": prof["id"], "grupo_id": grp["id"], "horas_semanales": 2},
            timeout=30,
        ).json()

        # delete profesor
        r = client.delete(f"{API}/profesores/{prof['id']}", timeout=30)
        assert r.status_code == 200
        assert r.json().get("ok") is True

        data = client.get(f"{API}/data", timeout=30).json()
        assert prof["id"] not in [p["id"] for p in data["profesores"]]
        assert mat["id"] not in [m["id"] for m in data["materias"]]


# ---------- Grupo CRUD ----------
class TestGrupo:
    def test_create_grupo(self, client):
        r = client.post(f"{API}/grupos", json={"nombre": "TEST_Grupo_Y"}, timeout=30)
        assert r.status_code == 200
        g = r.json()
        assert g["nombre"] == "TEST_Grupo_Y"
        assert g["id"].startswith("grp-")

    def test_delete_grupo_cascades_materias(self, client):
        prof = client.post(f"{API}/profesores", json={"nombre": "TEST_GC_Prof"}, timeout=30).json()
        grp = client.post(f"{API}/grupos", json={"nombre": "TEST_GC_Grp"}, timeout=30).json()
        mat = client.post(
            f"{API}/materias",
            json={"nombre": "TEST_M_G", "profesor_id": prof["id"], "grupo_id": grp["id"], "horas_semanales": 2},
            timeout=30,
        ).json()

        r = client.delete(f"{API}/grupos/{grp['id']}", timeout=30)
        assert r.status_code == 200

        data = client.get(f"{API}/data", timeout=30).json()
        assert grp["id"] not in [g["id"] for g in data["grupos"]]
        assert mat["id"] not in [m["id"] for m in data["materias"]]


# ---------- Materia CRUD ----------
class TestMateria:
    def test_create_and_delete_materia(self, client):
        prof = client.post(f"{API}/profesores", json={"nombre": "TEST_M_Prof"}, timeout=30).json()
        grp = client.post(f"{API}/grupos", json={"nombre": "TEST_M_Grp"}, timeout=30).json()
        payload = {
            "nombre": "TEST_Materia",
            "profesor_id": prof["id"],
            "grupo_id": grp["id"],
            "horas_semanales": 5,
        }
        r = client.post(f"{API}/materias", json=payload, timeout=30)
        assert r.status_code == 200
        mat = r.json()
        assert mat["nombre"] == "TEST_Materia"
        assert mat["horas_semanales"] == 5
        assert mat["id"].startswith("mat-")

        # verify present
        data = client.get(f"{API}/data", timeout=30).json()
        assert mat["id"] in [m["id"] for m in data["materias"]]

        # delete materia (only)
        r = client.delete(f"{API}/materias/{mat['id']}", timeout=30)
        assert r.status_code == 200
        data = client.get(f"{API}/data", timeout=30).json()
        assert mat["id"] not in [m["id"] for m in data["materias"]]


# ---------- Config ----------
class TestConfig:
    def test_update_config(self, client):
        payload = {"dias": ["Lunes", "Martes", "Miércoles"], "hora_inicio": 8, "hora_fin": 13}
        r = client.put(f"{API}/config", json=payload, timeout=30)
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["config"]["hora_inicio"] == 8
        assert body["config"]["hora_fin"] == 13
        # verify persistence
        data = client.get(f"{API}/data", timeout=30).json()
        assert data["config"]["dias"] == ["Lunes", "Martes", "Miércoles"]
        assert data["config"]["hora_inicio"] == 8
        assert data["config"]["hora_fin"] == 13

        # restore default
        client.put(
            f"{API}/config",
            json={"dias": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"], "hora_inicio": 7, "hora_fin": 14},
            timeout=30,
        )


# ---------- CSV upload ----------
class TestCSVUpload:
    def test_upload_csv_idempotent(self, client):
        # First, clear so counts are clean
        client.delete(f"{API}/clear", timeout=30)
        csv_content = (
            "profesor,grupo,materia,horas_semanales\n"
            "Juan Pérez,1° A,Matemáticas,3\n"
            "Juan Pérez,1° A,Física,2\n"
            "Ana López,1° B,Historia,3\n"
        )
        # multipart upload (do not send JSON content-type)
        s = requests.Session()
        files = {"file": ("clases.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        r = s.post(f"{API}/upload-csv", files=files, timeout=60)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is True
        assert body["materias_creadas"] == 3

        # verify counts
        data = client.get(f"{API}/data", timeout=30).json()
        assert len(data["profesores"]) == 2  # Juan, Ana
        assert len(data["grupos"]) == 2  # 1° A, 1° B
        assert len(data["materias"]) == 3

        # upsert behavior: re-upload same CSV — profesores/grupos should NOT duplicate
        r2 = s.post(f"{API}/upload-csv", files={"file": ("clases.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}, timeout=60)
        assert r2.status_code == 200
        data2 = client.get(f"{API}/data", timeout=30).json()
        # profesores/grupos must remain 2 each (upsert by name)
        assert len(data2["profesores"]) == 2
        assert len(data2["grupos"]) == 2
        # materias are appended (no name-key upsert per spec)
        assert len(data2["materias"]) == 6

    def test_upload_csv_missing_columns(self, client):
        bad = "foo,bar\n1,2\n"
        files = {"file": ("bad.csv", io.BytesIO(bad.encode("utf-8")), "text/csv")}
        r = requests.post(f"{API}/upload-csv", files=files, timeout=30)
        assert r.status_code == 400


class TestScheduleParsing:
    def test_parse_schedule_text_basic(self, client):
        text = (
            "GRUPO: 608\n"
            "HORA LUNES MARTES MIÉRCOLES JUEVES VIERNES\n"
            "08:00 PROGRAMACIÓN VISUAL PROGRAMACIÓN VISUAL PROGRAMACIÓN VISUAL INGENIERÍA DE SOFTWARE II PROGRAMACIÓN VISUAL\n"
            "09:00 INGENIERÍA DE SOFTWARE II PROGRAMACIÓN VISUAL INGENIERÍA DE SOFTWARE II PROGRAMACIÓN VISUAL INGENIERÍA DE SOFTWARE II\n"
            "ASIGNATURA PROFESOR\n"
            "PROGRAMACIÓN VISUAL M.I. CARLOS EDGARDO CRUZ PÉREZ\n"
            "INGENIERÍA DE SOFTWARE II DR. COSIJOPII GARCÍA GARCÍA\n"
            "SEMESTRE: SEXTO\n"
        )
        r = client.post(f"{API}/parse-schedule-text", json={"text": text}, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is True
        sections = body["sections"]
        assert isinstance(sections, list) and len(sections) == 1
        section = sections[0]
        assert section["group"] == "608"
        assert section["semester"] == "SEXTO"
        assert section["schedule"]
        assert section["schedule"][0]["time"] == "08:00"
        assert section["schedule"][1]["time"] == "09:00"


# ---------- Generate ----------
class TestGenerate:
    def test_generate_400_when_no_materias(self, client):
        client.delete(f"{API}/clear", timeout=30)
        r = client.post(f"{API}/generate", json={"pop_size": 10, "generations": 5, "mutation_rate": 0.05}, timeout=60)
        assert r.status_code == 400

    def test_generate_400_invalid_horas(self, client):
        # reseed then call with invalid hours
        client.post(f"{API}/seed", timeout=30)
        r = client.post(
            f"{API}/generate",
            json={"pop_size": 10, "generations": 5, "mutation_rate": 0.05, "hora_inicio": 14, "hora_fin": 10},
            timeout=60,
        )
        assert r.status_code == 400

    def test_generate_success_and_counts(self, client):
        # Ensure seed data
        client.post(f"{API}/seed", timeout=30)
        data = client.get(f"{API}/data", timeout=30).json()
        total_hours = sum(int(m["horas_semanales"]) for m in data["materias"])

        r = client.post(
            f"{API}/generate",
            json={"pop_size": 30, "generations": 20, "mutation_rate": 0.05},
            timeout=120,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "assignments" in body
        assert "fitness_history" in body
        assert "broken_rules" in body
        assert "best_fitness" in body
        assert "dias" in body and "hora_inicio" in body and "hora_fin" in body

        assert len(body["assignments"]) == total_hours
        for a in body["assignments"]:
            for k in ["materia_id", "materia_nombre", "profesor_id", "grupo_id", "day", "hour"]:
                assert k in a
            assert 0 <= a["day"] < len(body["dias"])
            assert body["hora_inicio"] <= a["hour"] < body["hora_fin"]

        br = body["broken_rules"]
        for k in ["choques_profesor", "choques_grupo", "horas_sin_asignar", "total"]:
            assert k in br
        assert len(body["fitness_history"]) == 20


# ---------- last-schedule ----------
class TestLastSchedule:
    def test_last_schedule_returns_after_generate(self, client):
        r = client.get(f"{API}/last-schedule", timeout=30)
        assert r.status_code == 200
        body = r.json()
        assert "assignments" in body
        assert "best_fitness" in body


# ---------- clear ----------
class TestClear:
    def test_clear_empties_collections(self, client):
        r = client.delete(f"{API}/clear", timeout=30)
        assert r.status_code == 200
        data = client.get(f"{API}/data", timeout=30).json()
        assert data["profesores"] == []
        assert data["grupos"] == []
        assert data["materias"] == []

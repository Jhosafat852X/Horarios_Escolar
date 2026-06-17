# Generador de Horarios Evolutivo

Sistema web para generar horarios escolares usando un algoritmo genetico. Permite registrar profesores, grupos y materias, importar datos desde CSV/Excel/PDF, configurar el rango de horas y generar una propuesta de horario evaluando conflictos de profesor y grupo.

## Tecnologias

- Backend: FastAPI, Uvicorn, MongoDB, Motor, Pandas y pdfplumber.
- Frontend: React, CRACO, Tailwind CSS, Axios y Recharts.
- Base de datos: MongoDB local.

## Requisitos

Antes de ejecutar el sistema, asegurate de tener instalado:

- Python 3.10 o superior.
- Node.js y npm.
- MongoDB ejecutandose en `localhost:27017`.

En este proyecto ya existe un entorno virtual en `.venv` y las dependencias del frontend estan instaladas en `frontend/node_modules`.

## Configuracion

El backend usa el archivo [backend/.env](backend/.env):

```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=horarios_db
CORS_ORIGINS=*
```

El frontend usa el archivo [frontend/.env](frontend/.env):

```env
REACT_APP_BACKEND_URL=http://127.0.0.1:8000
```

Esa URL debe coincidir con el puerto donde se levanta FastAPI.

## Como ejecutar el sistema

Abre dos terminales.

### 1. Levantar el backend

Desde la raiz del proyecto:

```powershell
cd D:\IA\HorarioUnistmo\Horarios_Escolar
.\.venv\Scripts\python.exe -m uvicorn backend.server:app --host 127.0.0.1 --port 8000
```

El backend queda disponible en:

```text
http://127.0.0.1:8000
```

Puedes revisar la API en:

```text
http://127.0.0.1:8000/docs
```

### 2. Levantar el frontend

En otra terminal:

```powershell
cd D:\IA\HorarioUnistmo\Horarios_Escolar\frontend
npm start
```

La aplicacion queda disponible en:

```text
http://localhost:3000
```

## Flujo de uso

1. Abrir `http://localhost:3000`.
2. Cargar datos de ejemplo o registrar datos manualmente.
3. Tambien se puede importar un archivo CSV, Excel o PDF estructurado.
4. Revisar profesores, grupos y materias.
5. Configurar el horario. Para este conjunto de datos se recomienda usar de `07:00` a `19:00`.
6. Ejecutar la generacion del horario.
7. Revisar las metricas:
   - `Choques de Profesor`
   - `Choques de Grupo`
   - `Horas Sin Asignar`
   - `Reglas Rotas`
   - `Mejor Fitness`

El objetivo principal es que los choques de profesor, choques de grupo y horas sin asignar queden en `0`.

## Formato de importacion

Para CSV o Excel, las columnas principales son:

```csv
profesor,grupo,materia,horas_semanales,carrera,semestre,seccion,codigo
```

Las columnas obligatorias son:

```text
profesor, grupo, materia, horas_semanales
```

Las columnas `carrera`, `semestre`, `seccion` y `codigo` son opcionales.

## Endpoints principales

- `GET /api/`: verifica que el backend esta activo.
- `GET /api/data`: obtiene profesores, grupos, materias, carreras y configuracion.
- `POST /api/seed`: carga datos de ejemplo.
- `DELETE /api/clear`: limpia la base de datos.
- `POST /api/upload-csv`: importa CSV, Excel o PDF.
- `PUT /api/config`: guarda dias y rango de horas.
- `POST /api/generate`: genera el horario.
- `GET /api/last-schedule`: obtiene el ultimo horario generado.

## Parametros del algoritmo

El sistema permite ajustar:

- `pop_size`: tamano de la poblacion.
- `generations`: numero de generaciones.
- `mutation_rate`: probabilidad de mutacion.
- `crossover_rate`: probabilidad de cruza.
- `hora_inicio` y `hora_fin`: rango de horas disponibles.
- `dias`: dias considerados para programar clases.

La funcion de evaluacion penaliza principalmente los conflictos. Un horario puede tener todas las sesiones programadas y aun asi no ser bueno si tiene choques; por eso las metricas son mas importantes que solo ver el total de sesiones.

## Solucion de problemas

### Error: `AxiosError: Network Error`

Significa que el frontend abrio, pero no pudo conectarse con el backend.

Verifica que FastAPI este encendido:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/
```

Si falla, vuelve a levantar el backend:

```powershell
cd D:\IA\HorarioUnistmo\Horarios_Escolar
.\.venv\Scripts\python.exe -m uvicorn backend.server:app --host 127.0.0.1 --port 8000
```

### Error de MongoDB

Si el backend no arranca o no guarda datos, revisa que MongoDB este activo en `localhost:27017`.

Prueba:

```powershell
Test-NetConnection -ComputerName localhost -Port 27017
```

Debe aparecer:

```text
TcpTestSucceeded : True
```

### Horarios con muchos choques

Si aparecen muchos conflictos aunque todas las sesiones esten programadas, revisa el rango de horas. Para los datos usados en este proyecto, `07:00` a `14:00` puede ser demasiado estrecho; se recomienda `07:00` a `19:00`.

## Pruebas rapidas

Verificar dependencias de Python:

```powershell
.\.venv\Scripts\python.exe -c "import fastapi, uvicorn, motor, pdfplumber; print('ok')"
```

Verificar backend:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/
```

Generar build del frontend:

```powershell
cd frontend
npm run build
```

## Estructura del proyecto

```text
Horarios_Escolar/
+-- backend/
|   +-- server.py
|   +-- genetic.py
|   +-- schedule_parser.py
|   +-- sample_data.py
|   +-- requirements.txt
+-- frontend/
|   +-- src/
|   |   +-- pages/
|   |   +-- components/
|   |   +-- lib/
|   +-- package.json
+-- tests/
+-- test_reports/
+-- README.md
```

## Estado esperado

Para considerar que el sistema esta funcionando:

- MongoDB responde en `localhost:27017`.
- Backend responde en `http://127.0.0.1:8000/api/`.
- Frontend abre en `http://localhost:3000`.
- La pantalla carga profesores, grupos y materias.
- El boton de generar horario produce metricas y una vista de calendario.

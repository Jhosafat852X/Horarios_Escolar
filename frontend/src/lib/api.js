import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API });

export const fetchData = () => api.get("/data").then((r) => r.data);
export const seedSample = () => api.post("/seed").then((r) => r.data);
export const clearAll = () => api.delete("/clear").then((r) => r.data);

export const createProfesor = (nombre) =>
  api.post("/profesores", { nombre }).then((r) => r.data);
export const deleteProfesor = (id) =>
  api.delete(`/profesores/${id}`).then((r) => r.data);

export const createGrupo = (grupo) =>
  api.post("/grupos", grupo).then((r) => r.data);
export const deleteGrupo = (id) =>
  api.delete(`/grupos/${id}`).then((r) => r.data);

export const createMateria = (payload) =>
  api.post("/materias", payload).then((r) => r.data);
export const deleteMateria = (id) =>
  api.delete(`/materias/${id}`).then((r) => r.data);

export const updateConfig = (cfg) =>
  api.put("/config", cfg).then((r) => r.data);

export const uploadCSV = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return api
    .post("/upload-csv", fd, { headers: { "Content-Type": "multipart/form-data" } })
    .then((r) => r.data);
};

export const generateSchedule = (params) =>
  api.post("/generate", params).then((r) => r.data);

export const parseScheduleText = (text) =>
  api.post("/parse-schedule-text", { text }).then((r) => r.data);

export const getLastSchedule = () => api.get("/last-schedule").then((r) => r.data);

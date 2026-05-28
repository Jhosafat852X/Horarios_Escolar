import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import {
  ChartLineUp,
  CalendarBlank,
  SlidersHorizontal,
  UploadSimple,
  Users,
  BookOpen,
  GraduationCap,
  Sparkle,
  ArrowsClockwise,
  Database,
  Trash,
  Plus,
  ListBullets,
} from "@phosphor-icons/react";

import {
  fetchData,
  seedSample,
  clearAll,
  generateSchedule,
  uploadCSV,
  updateConfig,
  createProfesor,
  deleteProfesor,
  createGrupo,
  deleteGrupo,
  createMateria,
  deleteMateria,
} from "@/lib/api";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

import ScheduleCalendar from "@/components/ScheduleCalendar";
import ConvergenceChart from "@/components/ConvergenceChart";
import MetricsPanel from "@/components/MetricsPanel";
import ManualDataDialogs from "@/components/ManualDataDialogs";

const DEFAULT_DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"];

export default function Dashboard() {
  const [data, setData] = useState({
    profesores: [],
    grupos: [],
    materias: [],
    config: { dias: DEFAULT_DIAS, hora_inicio: 7, hora_fin: 14 },
  });

  const [popSize, setPopSize] = useState(60);
  const [generations, setGenerations] = useState(150);
  const [mutationRate, setMutationRate] = useState(0.05);
  const [horaInicio, setHoraInicio] = useState(7);
  const [horaFin, setHoraFin] = useState(14);

  const [filtroGrupo, setFiltroGrupo] = useState("todos");
  const [filtroProfesor, setFiltroProfesor] = useState("todos");

  const [running, setRunning] = useState(false);
  const [schedule, setSchedule] = useState(null);

  const reload = async () => {
    const d = await fetchData();
    setData(d);
    setHoraInicio(d.config.hora_inicio);
    setHoraFin(d.config.hora_fin);
  };

  useEffect(() => {
    (async () => {
      const d = await fetchData();
      // If no data, auto-seed
      if (!d.materias?.length && !d.profesores?.length) {
        await seedSample();
        toast.success("Datos de ejemplo cargados automáticamente");
        await reload();
      } else {
        setData(d);
        setHoraInicio(d.config.hora_inicio);
        setHoraFin(d.config.hora_fin);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totalSesiones = useMemo(
    () => (data.materias || []).reduce((acc, m) => acc + (m.horas_semanales || 0), 0),
    [data.materias]
  );

  const handleGenerate = async () => {
    if (!data.materias?.length) {
      toast.error("Agrega materias antes de generar el horario.");
      return;
    }
    setRunning(true);
    try {
      // save current config
      await updateConfig({
        dias: data.config.dias,
        hora_inicio: horaInicio,
        hora_fin: horaFin,
      });
      const result = await generateSchedule({
        pop_size: popSize,
        generations,
        mutation_rate: mutationRate,
        dias: data.config.dias,
        hora_inicio: horaInicio,
        hora_fin: horaFin,
      });
      setSchedule(result);
      toast.success(
        result.broken_rules.total === 0
          ? "¡Horario óptimo generado sin conflictos!"
          : `Horario generado con ${result.broken_rules.total} reglas rotas.`
      );
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Error al generar horario");
    } finally {
      setRunning(false);
    }
  };

  const handleSeed = async () => {
    await seedSample();
    toast.success("Datos de ejemplo recargados");
    await reload();
  };

  const handleClear = async () => {
    await clearAll();
    setSchedule(null);
    toast.message("Base de datos vacía");
    await reload();
  };

  const handleUpload = async (file) => {
    try {
      const r = await uploadCSV(file);
      toast.success(`Archivo procesado: ${r.materias_creadas} materias importadas`);
      await reload();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Error al subir archivo");
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC]" data-testid="dashboard-root">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white">
        <div className="max-w-[1600px] mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center shadow-sm">
              <GraduationCap weight="bold" className="text-white" size={22} />
            </div>
            <div>
              <h1 className="font-outfit text-xl font-bold text-slate-900 tracking-tight">
                Generador de Horarios Evolutivo
              </h1>
              <p className="text-xs text-slate-500 font-worksans">
                Algoritmo Genético · Optimización de Horarios Escolares
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSeed}
              data-testid="seed-data-btn"
              className="gap-2"
            >
              <Database size={16} /> Cargar Ejemplo
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleClear}
              data-testid="clear-data-btn"
              className="gap-2"
            >
              <Trash size={16} /> Limpiar
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Sidebar */}
          <aside className="lg:col-span-4 xl:col-span-3 space-y-6">
            {/* Data entry */}
            <Card className="p-6 rounded-xl border border-slate-200 shadow-none">
              <div className="flex items-center gap-2 mb-4">
                <Database weight="duotone" size={20} className="text-indigo-600" />
                <h2 className="font-outfit font-semibold text-slate-900">Base de Datos</h2>
              </div>
              <Tabs defaultValue="manual">
                <TabsList className="grid grid-cols-2 w-full">
                  <TabsTrigger value="manual" data-testid="tab-manual">
                    Manual
                  </TabsTrigger>
                  <TabsTrigger value="csv" data-testid="tab-csv">
                    CSV/Excel
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="manual" className="mt-4">
                  <ManualDataDialogs data={data} onChange={reload}
                    onCreateProfesor={createProfesor}
                    onDeleteProfesor={deleteProfesor}
                    onCreateGrupo={createGrupo}
                    onDeleteGrupo={deleteGrupo}
                    onCreateMateria={createMateria}
                    onDeleteMateria={deleteMateria}
                  />
                </TabsContent>

                <TabsContent value="csv" className="mt-4">
                  <label
                    htmlFor="csv-input"
                    className="block border-2 border-dashed border-slate-300 rounded-lg p-6 text-center cursor-pointer hover:border-indigo-400 hover:bg-indigo-50/30 transition-colors"
                    data-testid="csv-dropzone"
                  >
                    <UploadSimple size={28} className="mx-auto text-slate-400 mb-2" />
                    <p className="text-sm font-medium text-slate-700">
                      Sube tu archivo CSV/Excel
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      Columnas: profesor, grupo, materia, horas_semanales
                    </p>
                    <input
                      id="csv-input"
                      data-testid="csv-input"
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) handleUpload(f);
                        e.target.value = "";
                      }}
                    />
                  </label>
                </TabsContent>
              </Tabs>

              <Separator className="my-4" />
              <div className="grid grid-cols-3 gap-3 text-center">
                <div data-testid="count-profesores">
                  <p className="text-2xl font-outfit font-bold text-slate-900 tabular-nums">
                    {data.profesores.length}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">Profesores</p>
                </div>
                <div data-testid="count-grupos">
                  <p className="text-2xl font-outfit font-bold text-slate-900 tabular-nums">
                    {data.grupos.length}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">Grupos</p>
                </div>
                <div data-testid="count-materias">
                  <p className="text-2xl font-outfit font-bold text-slate-900 tabular-nums">
                    {data.materias.length}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">Materias</p>
                </div>
              </div>
            </Card>

            {/* Configuration */}
            <Card className="p-6 rounded-xl border border-slate-200 shadow-none">
              <div className="flex items-center gap-2 mb-4">
                <CalendarBlank weight="duotone" size={20} className="text-indigo-600" />
                <h2 className="font-outfit font-semibold text-slate-900">Configuración</h2>
              </div>
              <div className="space-y-4">
                <div>
                  <Label className="text-xs text-slate-600">Días de la semana</Label>
                  <p className="text-sm text-slate-800 mt-1">
                    {data.config.dias?.join(" · ") || DEFAULT_DIAS.join(" · ")}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs text-slate-600" htmlFor="hora-inicio">
                      Hora inicio
                    </Label>
                    <Input
                      id="hora-inicio"
                      data-testid="input-hora-inicio"
                      type="number"
                      min="0"
                      max="23"
                      value={horaInicio}
                      onChange={(e) => setHoraInicio(parseInt(e.target.value) || 0)}
                      className="mt-1 tabular-nums"
                    />
                  </div>
                  <div>
                    <Label className="text-xs text-slate-600" htmlFor="hora-fin">
                      Hora fin
                    </Label>
                    <Input
                      id="hora-fin"
                      data-testid="input-hora-fin"
                      type="number"
                      min="1"
                      max="24"
                      value={horaFin}
                      onChange={(e) => setHoraFin(parseInt(e.target.value) || 0)}
                      className="mt-1 tabular-nums"
                    />
                  </div>
                </div>
              </div>
            </Card>

            {/* Algorithm parameters */}
            <Card className="p-6 rounded-xl border border-slate-200 shadow-none">
              <div className="flex items-center gap-2 mb-4">
                <SlidersHorizontal weight="duotone" size={20} className="text-indigo-600" />
                <h2 className="font-outfit font-semibold text-slate-900">
                  Parámetros del Algoritmo
                </h2>
              </div>
              <div className="space-y-5">
                <div>
                  <div className="flex justify-between mb-2">
                    <Label className="text-xs text-slate-600">Tamaño de Población</Label>
                    <span className="text-xs font-semibold text-indigo-600 tabular-nums">
                      {popSize}
                    </span>
                  </div>
                  <Slider
                    data-testid="slider-pop-size"
                    value={[popSize]}
                    min={10}
                    max={200}
                    step={5}
                    onValueChange={(v) => setPopSize(v[0])}
                  />
                </div>
                <div>
                  <div className="flex justify-between mb-2">
                    <Label className="text-xs text-slate-600">Generaciones</Label>
                    <span className="text-xs font-semibold text-indigo-600 tabular-nums">
                      {generations}
                    </span>
                  </div>
                  <Slider
                    data-testid="slider-generations"
                    value={[generations]}
                    min={10}
                    max={500}
                    step={10}
                    onValueChange={(v) => setGenerations(v[0])}
                  />
                </div>
                <div>
                  <div className="flex justify-between mb-2">
                    <Label className="text-xs text-slate-600">Probabilidad de Mutación</Label>
                    <span className="text-xs font-semibold text-indigo-600 tabular-nums">
                      {mutationRate.toFixed(2)}
                    </span>
                  </div>
                  <Slider
                    data-testid="slider-mutation"
                    value={[mutationRate * 100]}
                    min={1}
                    max={100}
                    step={1}
                    onValueChange={(v) => setMutationRate(v[0] / 100)}
                  />
                </div>
              </div>

              <Button
                onClick={handleGenerate}
                disabled={running}
                className="w-full mt-6 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-6 rounded-lg gap-2"
                data-testid="generate-schedule-btn"
              >
                {running ? (
                  <>
                    <ArrowsClockwise size={18} className="animate-spin" />
                    Evolucionando...
                  </>
                ) : (
                  <>
                    <Sparkle size={18} weight="fill" />
                    Generar Horarios
                  </>
                )}
              </Button>
              <p className="text-[11px] text-slate-500 text-center mt-2 tabular-nums">
                {totalSesiones} sesiones · {(horaFin - horaInicio) * (data.config.dias?.length || 5)} bloques disponibles
              </p>
            </Card>
          </aside>

          {/* Main content */}
          <section className="lg:col-span-8 xl:col-span-9 space-y-6">
            {/* Filters */}
            <Card className="p-4 rounded-xl border border-slate-200 shadow-none">
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2 mr-auto">
                  <CalendarBlank weight="duotone" size={20} className="text-indigo-600" />
                  <h2 className="font-outfit font-semibold text-slate-900">Vista del Horario</h2>
                  {schedule && (
                    <Badge variant="secondary" className="ml-2" data-testid="best-fitness-badge">
                      Fitness: <span className="tabular-nums ml-1">{schedule.best_fitness}</span>
                    </Badge>
                  )}
                </div>
                <Select value={filtroGrupo} onValueChange={setFiltroGrupo}>
                  <SelectTrigger className="w-[200px]" data-testid="filter-grupo">
                    <Users size={16} className="mr-1 text-slate-500" />
                    <SelectValue placeholder="Filtrar por Grupo" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="todos">Todos los grupos</SelectItem>
                    {data.grupos.map((g) => (
                      <SelectItem key={g.id} value={g.id}>
                        {g.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={filtroProfesor} onValueChange={setFiltroProfesor}>
                  <SelectTrigger className="w-[220px]" data-testid="filter-profesor">
                    <BookOpen size={16} className="mr-1 text-slate-500" />
                    <SelectValue placeholder="Filtrar por Profesor" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="todos">Todos los profesores</SelectItem>
                    {data.profesores.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </Card>

            {/* Calendar */}
            <ScheduleCalendar
              schedule={schedule}
              data={data}
              filtroGrupo={filtroGrupo}
              filtroProfesor={filtroProfesor}
              horaInicio={horaInicio}
              horaFin={horaFin}
            />

            {/* Bottom split: convergence + metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <ConvergenceChart history={schedule?.fitness_history || []} />
              <MetricsPanel schedule={schedule} totalSesiones={totalSesiones} />
            </div>

            {/* Materias list */}
            <Card className="p-6 rounded-xl border border-slate-200 shadow-none">
              <div className="flex items-center gap-2 mb-4">
                <ListBullets weight="duotone" size={20} className="text-indigo-600" />
                <h2 className="font-outfit font-semibold text-slate-900">Materias Cargadas</h2>
                <Badge variant="secondary" className="ml-auto tabular-nums">
                  {data.materias.length}
                </Badge>
              </div>
              {data.materias.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-6">
                  Aún no hay materias. Carga datos de ejemplo o agrégalas manualmente.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-slate-500 border-b border-slate-200">
                        <th className="py-2 font-medium">Materia</th>
                        <th className="py-2 font-medium">Profesor</th>
                        <th className="py-2 font-medium">Grupo</th>
                        <th className="py-2 font-medium text-right">Horas/sem</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.materias.map((m) => {
                        const prof = data.profesores.find((p) => p.id === m.profesor_id);
                        const grp = data.grupos.find((g) => g.id === m.grupo_id);
                        return (
                          <tr key={m.id} className="border-b border-slate-100" data-testid={`materia-row-${m.id}`}>
                            <td className="py-2 font-medium text-slate-800">{m.nombre}</td>
                            <td className="py-2 text-slate-600">{prof?.nombre || "—"}</td>
                            <td className="py-2 text-slate-600">{grp?.nombre || "—"}</td>
                            <td className="py-2 text-right tabular-nums">{m.horas_semanales}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </section>
        </div>
      </main>
    </div>
  );
}

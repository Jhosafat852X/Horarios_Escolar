import { useMemo, Fragment } from "react";
import { Card } from "@/components/ui/card";
import { colorForKey } from "@/lib/colors";
import { CalendarBlank } from "@phosphor-icons/react";

const EMPTY_IMG =
  "https://static.prod-images.emergentagent.com/jobs/e2b6f467-1abc-42cb-a03c-36c5c7b588a1/images/205f7144674266e711a2d864aa5b3fec5656fb06eec63b1affaedc0d6589b582.png";

export default function ScheduleCalendar({
  schedule,
  data,
  filtroGrupo,
  filtroProfesor,
  horaInicio,
  horaFin,
}) {
  const dias = schedule?.dias || data.config?.dias || ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"];
  const hi = schedule?.hora_inicio ?? horaInicio;
  const hf = schedule?.hora_fin ?? horaFin;
  const horas = [];
  for (let h = hi; h < hf; h++) horas.push(h);

  const filtered = useMemo(() => {
    if (!schedule?.assignments) return [];
    return schedule.assignments.filter((a) => {
      if (filtroGrupo !== "todos" && a.grupo_id !== filtroGrupo) return false;
      if (filtroProfesor !== "todos" && a.profesor_id !== filtroProfesor) return false;
      return true;
    });
  }, [schedule, filtroGrupo, filtroProfesor]);

  // group assignments by slot (day, hour)
  const grid = useMemo(() => {
    const g = {};
    for (const a of filtered) {
      const key = `${a.day}-${a.hour}`;
      if (!g[key]) g[key] = [];
      g[key].push(a);
    }
    return g;
  }, [filtered]);

  if (!schedule) {
    return (
      <Card
        className="p-12 rounded-xl border border-slate-200 shadow-none flex flex-col items-center justify-center min-h-[480px]"
        data-testid="empty-schedule"
      >
        <img
          src={EMPTY_IMG}
          alt="Horario vacío"
          className="max-w-md w-full opacity-90 mb-4"
        />
        <h3 className="font-outfit text-2xl font-semibold text-slate-900 tracking-tight mb-2">
          Aún no se ha generado un horario
        </h3>
        <p className="text-sm text-slate-500 text-center max-w-md font-worksans">
          Configura los parámetros del algoritmo genético en el panel izquierdo y presiona{" "}
          <span className="font-semibold text-indigo-600">"Generar Horarios"</span> para evolucionar
          la mejor distribución posible.
        </p>
      </Card>
    );
  }

  const findProfesor = (id) => data.profesores.find((p) => p.id === id);
  const findGrupo = (id) => data.grupos.find((g) => g.id === id);

  return (
    <Card className="p-4 rounded-xl border border-slate-200 shadow-none overflow-x-auto" data-testid="schedule-calendar">
      <div
        className="grid gap-1 min-w-[800px]"
        style={{
          gridTemplateColumns: `80px repeat(${dias.length}, minmax(140px, 1fr))`,
        }}
      >
        {/* Header */}
        <div></div>
        {dias.map((d) => (
          <div
            key={d}
            className="text-center font-outfit font-semibold text-sm text-slate-700 py-2 border-b-2 border-slate-200"
          >
            {d}
          </div>
        ))}

        {/* Rows */}
        {horas.map((h) => (
          <Fragment key={`hour-row-${h}`}>
            <div
              key={`hour-${h}`}
              className="text-xs text-slate-500 font-medium text-right pr-3 py-2 tabular-nums border-r border-slate-100 flex items-start justify-end"
            >
              {String(h).padStart(2, "0")}:00
            </div>
            {dias.map((_, dayIdx) => {
              const key = `${dayIdx}-${h}`;
              const items = grid[key] || [];
              return (
                <div
                  key={`cell-${dayIdx}-${h}`}
                  className="min-h-[60px] border border-slate-100 rounded-md p-1 space-y-1"
                  data-testid={`cell-${dayIdx}-${h}`}
                >
                  {items.map((a, i) => {
                    const c = colorForKey(a.materia_nombre);
                    const prof = findProfesor(a.profesor_id);
                    const grp = findGrupo(a.grupo_id);
                    // Real conflict = same professor or same group in same slot
                    const isClash = items.some(
                      (o, j) =>
                        j !== i &&
                        (o.profesor_id === a.profesor_id || o.grupo_id === a.grupo_id)
                    );
                    return (
                      <div
                        key={`${a.materia_id}-${i}`}
                        className="rounded-md px-2 py-1 text-[11px] leading-tight border"
                        style={{
                          backgroundColor: c.bg,
                          color: c.text,
                          borderColor: isClash ? "#EF4444" : c.border,
                          borderWidth: isClash ? 2 : 1,
                        }}
                        title={`${a.materia_nombre} · ${prof?.nombre || ""} · ${grp?.nombre || ""}`}
                      >
                        <div className="font-semibold truncate">{a.materia_nombre}</div>
                        <div className="opacity-80 truncate">{grp?.nombre}</div>
                        <div className="opacity-70 truncate">{prof?.nombre}</div>
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </Fragment>
        ))}
      </div>
    </Card>
  );
}

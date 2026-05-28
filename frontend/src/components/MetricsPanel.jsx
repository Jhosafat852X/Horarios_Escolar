import { Card } from "@/components/ui/card";
import { CheckCircle, Warning, XCircle, Target } from "@phosphor-icons/react";

function Metric({ label, value, icon: Icon, tone, testid }) {
  const tones = {
    success: "bg-emerald-50 text-emerald-700 border-emerald-200",
    warning: "bg-amber-50 text-amber-700 border-amber-200",
    error: "bg-rose-50 text-rose-700 border-rose-200",
    neutral: "bg-slate-50 text-slate-700 border-slate-200",
  };
  return (
    <div
      className={`rounded-lg border p-4 flex items-center gap-3 ${tones[tone]}`}
      data-testid={testid}
    >
      <Icon size={28} weight="duotone" />
      <div>
        <p className="text-2xl font-outfit font-bold tabular-nums leading-none">{value}</p>
        <p className="text-xs mt-1 opacity-80">{label}</p>
      </div>
    </div>
  );
}

export default function MetricsPanel({ schedule, totalSesiones }) {
  const br = schedule?.broken_rules;
  const profClashes = br?.choques_profesor ?? 0;
  const grpClashes = br?.choques_grupo ?? 0;
  const sinAsignar = br?.horas_sin_asignar ?? 0;
  const total = br?.total ?? 0;
  const fitness = schedule?.best_fitness ?? "—";

  return (
    <Card className="p-6 rounded-xl border border-slate-200 shadow-none" data-testid="metrics-panel">
      <div className="flex items-center gap-2 mb-4">
        <Target weight="duotone" size={20} className="text-indigo-600" />
        <h2 className="font-outfit font-semibold text-slate-900">Reglas y Métricas</h2>
      </div>

      {!schedule ? (
        <div className="text-sm text-slate-400 py-8 text-center">
          Genera un horario para ver las métricas.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          <Metric
            label="Choques de Profesor"
            value={profClashes}
            icon={XCircle}
            tone={profClashes === 0 ? "success" : "error"}
            testid="metric-prof-clashes"
          />
          <Metric
            label="Choques de Grupo"
            value={grpClashes}
            icon={XCircle}
            tone={grpClashes === 0 ? "success" : "error"}
            testid="metric-grp-clashes"
          />
          <Metric
            label="Horas Sin Asignar"
            value={sinAsignar}
            icon={Warning}
            tone={sinAsignar === 0 ? "success" : "warning"}
            testid="metric-unassigned"
          />
          <Metric
            label="Reglas Rotas (Total)"
            value={total}
            icon={total === 0 ? CheckCircle : Warning}
            tone={total === 0 ? "success" : "error"}
            testid="metric-total-broken"
          />
          <div className="col-span-2 rounded-lg border border-indigo-200 bg-indigo-50 p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-indigo-700 font-medium">Mejor Fitness</p>
              <p className="text-3xl font-outfit font-bold tabular-nums text-indigo-900 leading-tight">
                {fitness}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-indigo-700">Sesiones programadas</p>
              <p className="text-xl font-outfit font-bold tabular-nums text-indigo-900">
                {schedule.assignments?.length || 0} / {totalSesiones}
              </p>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

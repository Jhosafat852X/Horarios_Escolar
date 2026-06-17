import { Card } from "@/components/ui/card";
import { ChartLineUp } from "@phosphor-icons/react";
import {
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function ConvergenceChart({ history }) {
  const data = history.map((v, i) => ({ gen: i + 1, fitness: v }));

  return (
    <Card className="min-w-0 p-6 rounded-xl border border-slate-200 shadow-none" data-testid="convergence-chart">
      <div className="flex items-center gap-2 mb-4">
        <ChartLineUp weight="duotone" size={20} className="text-indigo-600" />
        <h2 className="font-outfit font-semibold text-slate-900">Evolución del Fitness</h2>
      </div>
      {data.length === 0 ? (
        <div className="h-[200px] flex items-center justify-center text-sm text-slate-400">
          Aún no hay datos. Genera un horario para ver la convergencia.
        </div>
      ) : (
        <div className="h-[220px] w-full min-w-0" style={{ minHeight: 220 }}>
          <ResponsiveContainer width="100%" height={220} minWidth={0} minHeight={220}>
            <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="fillFitness" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#818CF8" stopOpacity={0.6} />
                  <stop offset="100%" stopColor="#818CF8" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis
                dataKey="gen"
                stroke="#64748B"
                fontSize={11}
                label={{ value: "Generación", position: "insideBottom", offset: -2, fontSize: 11, fill: "#64748B" }}
              />
              <YAxis stroke="#64748B" fontSize={11} />
              <Tooltip
                contentStyle={{
                  background: "#fff",
                  border: "1px solid #E2E8F0",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Area
                type="monotone"
                dataKey="fitness"
                stroke="#4F46E5"
                strokeWidth={2}
                fill="url(#fillFitness)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  );
}

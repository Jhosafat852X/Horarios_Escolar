import { useState } from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Users, BookOpen, GraduationCap, Plus, X } from "@phosphor-icons/react";

export default function ManualDataDialogs({
  data,
  onChange,
  onCreateProfesor,
  onDeleteProfesor,
  onCreateGrupo,
  onDeleteGrupo,
  onCreateMateria,
  onDeleteMateria,
}) {
  const [profOpen, setProfOpen] = useState(false);
  const [grpOpen, setGrpOpen] = useState(false);
  const [matOpen, setMatOpen] = useState(false);

  const [profNombre, setProfNombre] = useState("");
  const [grpNombre, setGrpNombre] = useState("");
  const [grpSemestre, setGrpSemestre] = useState(1);
  const [grpSeccion, setGrpSeccion] = useState("A");
  const [grpCodigo, setGrpCodigo] = useState("");
  const [matForm, setMatForm] = useState({
    nombre: "",
    profesor_id: "",
    grupo_id: "",
    horas_semanales: 3,
  });

  const handleAddProf = async () => {
    if (!profNombre.trim()) return;
    await onCreateProfesor(profNombre.trim());
    setProfNombre("");
    setProfOpen(false);
    toast.success("Profesor agregado");
    await onChange();
  };
  const handleAddGrp = async () => {
    if (!grpNombre.trim()) return;
    await onCreateGrupo({
      nombre: grpNombre.trim(),
      semestre: parseInt(grpSemestre, 10) || 1,
      seccion: grpSeccion.trim().toUpperCase() || "A",
      codigo: grpCodigo.trim() || `${grpSemestre}${grpSeccion.trim().toUpperCase()}`,
    });
    setGrpNombre("");
    setGrpSemestre(1);
    setGrpSeccion("A");
    setGrpCodigo("");
    setGrpOpen(false);
    toast.success("Grupo agregado");
    await onChange();
  };
  const handleAddMat = async () => {
    if (!matForm.nombre.trim() || !matForm.profesor_id || !matForm.grupo_id) {
      toast.error("Completa todos los campos");
      return;
    }
    await onCreateMateria({
      ...matForm,
      horas_semanales: parseInt(matForm.horas_semanales) || 1,
    });
    setMatForm({ nombre: "", profesor_id: "", grupo_id: "", horas_semanales: 3 });
    setMatOpen(false);
    toast.success("Materia agregada");
    await onChange();
  };

  return (
    <div className="space-y-3">
      {/* Profesores */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-600 flex items-center gap-1">
          <Users size={14} /> Profesores
        </span>
        <Dialog open={profOpen} onOpenChange={setProfOpen}>
          <DialogTrigger asChild>
            <Button size="sm" variant="outline" className="h-7 px-2 text-xs gap-1" data-testid="btn-add-profesor">
              <Plus size={12} /> Agregar
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Agregar Profesor</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              <Label htmlFor="prof-nombre">Nombre del profesor</Label>
              <Input
                id="prof-nombre"
                data-testid="input-prof-nombre"
                value={profNombre}
                onChange={(e) => setProfNombre(e.target.value)}
                placeholder="Ej. Dra. María López"
              />
            </div>
            <DialogFooter>
              <Button onClick={handleAddProf} data-testid="btn-save-profesor" className="bg-indigo-600 hover:bg-indigo-700">
                Guardar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
      <ChipList
        items={data.profesores}
        onDelete={async (id) => {
          await onDeleteProfesor(id);
          toast.message("Profesor eliminado");
          await onChange();
        }}
        emptyText="Sin profesores"
        testid="list-profesores"
      />

      {/* Grupos */}
      <div className="flex items-center justify-between pt-2">
        <span className="text-xs font-medium text-slate-600 flex items-center gap-1">
          <GraduationCap size={14} /> Grupos
        </span>
        <Dialog open={grpOpen} onOpenChange={setGrpOpen}>
          <DialogTrigger asChild>
            <Button size="sm" variant="outline" className="h-7 px-2 text-xs gap-1" data-testid="btn-add-grupo">
              <Plus size={12} /> Agregar
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Agregar Grupo</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              <Label htmlFor="grp-nombre">Nombre del grupo (letra o etiqueta)</Label>
              <Input
                id="grp-nombre"
                data-testid="input-grp-nombre"
                value={grpNombre}
                onChange={(e) => setGrpNombre(e.target.value)}
                placeholder="Ej. A"
              />
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <Label htmlFor="grp-semestre">Semestre</Label>
                  <Input
                    id="grp-semestre"
                    data-testid="input-grp-semestre"
                    type="number"
                    min="1"
                    max="10"
                    value={grpSemestre}
                    onChange={(e) => setGrpSemestre(e.target.value)}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="grp-seccion">Sección</Label>
                  <Input
                    id="grp-seccion"
                    data-testid="input-grp-seccion"
                    value={grpSeccion}
                    onChange={(e) => setGrpSeccion(e.target.value)}
                    placeholder="A"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="grp-codigo">Código</Label>
                  <Input
                    id="grp-codigo"
                    data-testid="input-grp-codigo"
                    value={grpCodigo}
                    onChange={(e) => setGrpCodigo(e.target.value)}
                    placeholder="108A"
                    className="mt-1"
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleAddGrp} data-testid="btn-save-grupo" className="bg-indigo-600 hover:bg-indigo-700">
                Guardar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
      <ChipList
        items={data.grupos}
        onDelete={async (id) => {
          await onDeleteGrupo(id);
          toast.message("Grupo eliminado");
          await onChange();
        }}
        emptyText="Sin grupos"
        testid="list-grupos"
      />

      {/* Materias */}
      <div className="flex items-center justify-between pt-2">
        <span className="text-xs font-medium text-slate-600 flex items-center gap-1">
          <BookOpen size={14} /> Materias
        </span>
        <Dialog open={matOpen} onOpenChange={setMatOpen}>
          <DialogTrigger asChild>
            <Button
              size="sm"
              variant="outline"
              className="h-7 px-2 text-xs gap-1"
              disabled={!data.profesores.length || !data.grupos.length}
              data-testid="btn-add-materia"
            >
              <Plus size={12} /> Agregar
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Agregar Materia</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              <div>
                <Label htmlFor="mat-nombre">Nombre</Label>
                <Input
                  id="mat-nombre"
                  data-testid="input-mat-nombre"
                  value={matForm.nombre}
                  onChange={(e) => setMatForm({ ...matForm, nombre: e.target.value })}
                  placeholder="Ej. Algoritmos"
                />
              </div>
              <div>
                <Label>Profesor</Label>
                <Select
                  value={matForm.profesor_id}
                  onValueChange={(v) => setMatForm({ ...matForm, profesor_id: v })}
                >
                  <SelectTrigger data-testid="select-mat-profesor">
                    <SelectValue placeholder="Selecciona un profesor" />
                  </SelectTrigger>
                  <SelectContent>
                    {data.profesores.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Grupo</Label>
                <Select
                  value={matForm.grupo_id}
                  onValueChange={(v) => setMatForm({ ...matForm, grupo_id: v })}
                >
                  <SelectTrigger data-testid="select-mat-grupo">
                    <SelectValue placeholder="Selecciona un grupo" />
                  </SelectTrigger>
                  <SelectContent>
                    {data.grupos.map((g) => (
                      <SelectItem key={g.id} value={g.id}>
                        {g.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="mat-horas">Horas semanales</Label>
                <Input
                  id="mat-horas"
                  data-testid="input-mat-horas"
                  type="number"
                  min="1"
                  max="20"
                  value={matForm.horas_semanales}
                  onChange={(e) =>
                    setMatForm({ ...matForm, horas_semanales: e.target.value })
                  }
                />
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleAddMat} data-testid="btn-save-materia" className="bg-indigo-600 hover:bg-indigo-700">
                Guardar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
      <div className="text-xs text-slate-500" data-testid="materias-count">
        {data.materias.length} materia(s) cargada(s)
      </div>
    </div>
  );
}

function ChipList({ items, onDelete, emptyText, testid }) {
  if (!items?.length) {
    return <p className="text-xs text-slate-400 italic">{emptyText}</p>;
  }
  return (
    <div className="flex flex-wrap gap-1.5" data-testid={testid}>
      {items.map((it) => (
        <span
          key={it.id}
          className="inline-flex items-center gap-1 text-[11px] bg-slate-100 text-slate-700 rounded-full pl-2 pr-1 py-0.5"
        >
          {it.codigo || it.nombre}
          <button
            onClick={() => onDelete(it.id)}
            className="hover:bg-rose-200 hover:text-rose-700 rounded-full p-0.5 transition-colors"
            data-testid={`delete-${it.id}`}
          >
            <X size={10} />
          </button>
        </span>
      ))}
    </div>
  );
}

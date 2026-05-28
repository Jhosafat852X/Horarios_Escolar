"""Genetic Algorithm for School Schedule Generation."""
import random
from collections import defaultdict
from typing import List, Dict, Any


def run_genetic_algorithm(
    materias: List[Dict[str, Any]],
    dias: List[str],
    hora_inicio: int,
    hora_fin: int,
    pop_size: int = 60,
    generations: int = 150,
    mutation_rate: float = 0.05,
):
    """Run a genetic algorithm to generate a school schedule.

    Chromosome: list of slot indices (one per session). slot = day * n_hours + hour.
    Fitness (lower is better): hard conflicts * 1000 + total gaps (dead time).
    """
    # Expand materias into individual sessions
    sessions = []
    for m in materias:
        for _ in range(int(m.get("horas_semanales", 1))):
            sessions.append(m)

    if not sessions:
        return {
            "assignments": [],
            "fitness_history": [],
            "broken_rules": {
                "choques_profesor": 0,
                "choques_grupo": 0,
                "horas_sin_asignar": 0,
                "total": 0,
            },
            "best_fitness": 0,
        }

    n_days = len(dias)
    n_hours = hora_fin - hora_inicio
    n_slots = n_days * n_hours

    if n_slots <= 0:
        raise ValueError("Configuración inválida: horas/dias deben ser > 0")

    if n_slots < len(sessions):
        # Not enough slots, still try but conflicts will be inevitable
        pass

    def random_chromosome():
        return [random.randint(0, n_slots - 1) for _ in sessions]

    def evaluate(chrom):
        slot_assignments = defaultdict(list)
        for i, slot in enumerate(chrom):
            s = sessions[i]
            slot_assignments[slot].append((s["profesor_id"], s["grupo_id"]))

        prof_clashes = 0
        grup_clashes = 0
        for lst in slot_assignments.values():
            profs = [x[0] for x in lst]
            grps = [x[1] for x in lst]
            prof_clashes += len(profs) - len(set(profs))
            grup_clashes += len(grps) - len(set(grps))

        # dead time per prof/group per day
        prof_day_hours = defaultdict(list)
        grup_day_hours = defaultdict(list)
        for i, slot in enumerate(chrom):
            day = slot // n_hours
            hour = slot % n_hours
            s = sessions[i]
            prof_day_hours[(s["profesor_id"], day)].append(hour)
            grup_day_hours[(s["grupo_id"], day)].append(hour)

        gaps = 0
        for hours_list in list(prof_day_hours.values()) + list(grup_day_hours.values()):
            unique = sorted(set(hours_list))
            if len(unique) > 1:
                gaps += (unique[-1] - unique[0] + 1) - len(unique)

        conflicts = prof_clashes + grup_clashes
        fitness = conflicts * 1000 + gaps
        return fitness, prof_clashes, grup_clashes

    def tournament(pop_with_fit, k=3):
        sample = random.sample(pop_with_fit, min(k, len(pop_with_fit)))
        return min(sample, key=lambda x: x[1])[0]

    population = [random_chromosome() for _ in range(pop_size)]
    fitness_history = []
    best_overall = None
    best_overall_fitness = float("inf")

    for _gen in range(generations):
        pop_with_fit = [(c, evaluate(c)[0]) for c in population]
        pop_with_fit.sort(key=lambda x: x[1])
        best_fit = pop_with_fit[0][1]
        fitness_history.append(best_fit)

        if best_fit < best_overall_fitness:
            best_overall_fitness = best_fit
            best_overall = pop_with_fit[0][0][:]

        # elitism: keep top 2
        new_pop = [pop_with_fit[0][0], pop_with_fit[1][0] if len(pop_with_fit) > 1 else pop_with_fit[0][0]]

        while len(new_pop) < pop_size:
            p1 = tournament(pop_with_fit)
            p2 = tournament(pop_with_fit)
            # uniform crossover
            child = [p1[i] if random.random() < 0.5 else p2[i] for i in range(len(sessions))]
            # mutation
            for i in range(len(child)):
                if random.random() < mutation_rate:
                    child[i] = random.randint(0, n_slots - 1)
            new_pop.append(child)

        population = new_pop

    # final evaluation of best_overall
    final_fitness, prof_clashes, grup_clashes = evaluate(best_overall)

    assignments = []
    for i, slot in enumerate(best_overall):
        s = sessions[i]
        day = slot // n_hours
        hour = slot % n_hours + hora_inicio
        assignments.append({
            "materia_id": s["id"],
            "materia_nombre": s["nombre"],
            "profesor_id": s["profesor_id"],
            "grupo_id": s["grupo_id"],
            "day": day,
            "hour": hour,
        })

    return {
        "assignments": assignments,
        "fitness_history": fitness_history,
        "broken_rules": {
            "choques_profesor": prof_clashes,
            "choques_grupo": grup_clashes,
            "horas_sin_asignar": 0,
            "total": prof_clashes + grup_clashes,
        },
        "best_fitness": final_fitness,
    }

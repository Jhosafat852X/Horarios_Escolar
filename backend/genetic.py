"""Genetic Algorithm for School Schedule Generation.

Representation:
    X[group_id][day][hour] = session_index | None

Each chromosome is a timetable matrix grouped by school group. This matches the
natural interpretation of the problem: every group has a days x hours calendar.
"""
import copy
import random
import unicodedata
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple


def run_genetic_algorithm(
    materias: List[Dict[str, Any]],
    dias: List[str],
    hora_inicio: int,
    hora_fin: int,
    pop_size: int = 500,
    generations: int = 150,
    mutation_rate: float = 0.05,
    crossover_rate: float = 0.5,
):
    """Run a genetic algorithm to generate a school schedule.

    Chromosome:
        A three-index matrix X[group][day][hour] where each cell stores the
        session assigned to that group at that day-hour block.

    Fitness (lower is better):
        hard conflicts * 1000 + dead-time gaps + preference penalty +
        unassigned sessions * 1000.
    """
    sessions = []
    for materia in materias:
        preferred_slots = materia.get("preferred_slots") or []
        for idx in range(int(materia.get("horas_semanales", 1))):
            session = dict(materia)
            if idx < len(preferred_slots):
                session["preferred_slot"] = preferred_slots[idx]
            sessions.append(session)

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
    if n_days <= 0 or n_hours <= 0:
        raise ValueError("Configuracion invalida: horas/dias deben ser > 0")

    group_ids = sorted({session["grupo_id"] for session in sessions})
    sessions_by_group = defaultdict(list)
    for idx, session in enumerate(sessions):
        sessions_by_group[session["grupo_id"]].append(idx)

    def normalize_subject(value):
        text = str(value or "").upper()
        text = "".join(
            char for char in unicodedata.normalize("NFD", text)
            if unicodedata.category(char) != "Mn"
        )
        return " ".join(text.split())

    def empty_chromosome():
        return {
            group_id: [[None for _ in range(n_hours)] for _ in range(n_days)]
            for group_id in group_ids
        }

    def clone_chromosome(chrom):
        return copy.deepcopy(chrom)

    def slot_from_preferred(preferred) -> Optional[Tuple[int, int]]:
        if not preferred:
            return None
        day = preferred.get("day")
        hour = preferred.get("hour")
        if day is None or hour is None:
            return None
        matrix_hour = int(hour) - hora_inicio
        if 0 <= int(day) < n_days and 0 <= matrix_hour < n_hours:
            return int(day), matrix_hour
        return None

    def session_position(chrom, session_idx):
        group_id = sessions[session_idx]["grupo_id"]
        for day in range(n_days):
            for hour in range(n_hours):
                if chrom[group_id][day][hour] == session_idx:
                    return group_id, day, hour
        return group_id, None, None

    def empty_slots_for_group(chrom, group_id):
        slots = []
        for day in range(n_days):
            for hour in range(n_hours):
                if chrom[group_id][day][hour] is None:
                    slots.append((day, hour))
        return slots

    def allowed_slots_for_session(session_idx):
        session = sessions[session_idx]
        subject = normalize_subject(session.get("nombre"))
        if subject == "INGLES":
            english_hour = 10 - hora_inicio
            if 0 <= english_hour < n_hours:
                return [(day, english_hour) for day in range(n_days)]
            return []
        return [
            (day, hour)
            for day in range(n_days)
            for hour in range(n_hours)
        ]

    def available_slots_for_session(chrom, session_idx):
        group_id = sessions[session_idx]["grupo_id"]
        return [
            (day, hour)
            for day, hour in allowed_slots_for_session(session_idx)
            if chrom[group_id][day][hour] is None
        ]

    def place_session(chrom, session_idx, preferred_first=True):
        group_id = sessions[session_idx]["grupo_id"]
        if preferred_first:
            preferred = slot_from_preferred(sessions[session_idx].get("preferred_slot"))
            if preferred and preferred in allowed_slots_for_session(session_idx):
                day, hour = preferred
                if chrom[group_id][day][hour] is None:
                    chrom[group_id][day][hour] = session_idx
                    return True

        candidates = available_slots_for_session(chrom, session_idx)
        if not candidates:
            return False
        day, hour = random.choice(candidates)
        chrom[group_id][day][hour] = session_idx
        return True

    def preferred_chromosome():
        chrom = empty_chromosome()
        unassigned = []
        for session_idx in range(len(sessions)):
            if not place_session(chrom, session_idx, preferred_first=True):
                unassigned.append(session_idx)
        repair_chromosome(chrom, unassigned)
        return chrom, unassigned

    def random_chromosome():
        chrom = empty_chromosome()
        unassigned = []
        shuffled_sessions = list(range(len(sessions)))
        random.shuffle(shuffled_sessions)
        for session_idx in shuffled_sessions:
            if not place_session(chrom, session_idx, preferred_first=False):
                unassigned.append(session_idx)
        repair_chromosome(chrom, unassigned)
        return chrom, unassigned

    def teacher_conflicts_by_slot(chrom):
        prof_slot_sessions = defaultdict(list)
        for group_id in group_ids:
            for day in range(n_days):
                for hour in range(n_hours):
                    session_idx = chrom[group_id][day][hour]
                    if session_idx is None:
                        continue
                    prof_id = sessions[session_idx]["profesor_id"]
                    prof_slot_sessions[(prof_id, day, hour)].append(session_idx)
        return {
            key: value
            for key, value in prof_slot_sessions.items()
            if len(value) > 1
        }

    def move_session(chrom, session_idx, target_day, target_hour):
        group_id, old_day, old_hour = session_position(chrom, session_idx)
        if old_day is not None:
            chrom[group_id][old_day][old_hour] = None
        chrom[group_id][target_day][target_hour] = session_idx

    def repair_chromosome(chrom, unassigned):
        """Repair teacher clashes and try to place unassigned sessions.

        Group clashes are avoided by the matrix itself: a group-day-hour cell can
        store only one session.
        """
        for _ in range(len(sessions) * 2):
            conflicts = teacher_conflicts_by_slot(chrom)
            if not conflicts:
                break
            changed = False
            for (_prof_id, day, hour), clashing_sessions in conflicts.items():
                for session_idx in clashing_sessions[1:]:
                    group_id = sessions[session_idx]["grupo_id"]
                    candidates = []
                    for cand_day, cand_hour in available_slots_for_session(chrom, session_idx):
                        has_professor_busy = False
                        for other_group in group_ids:
                            other_idx = chrom[other_group][cand_day][cand_hour]
                            if (
                                other_idx is not None
                                and sessions[other_idx]["profesor_id"] == sessions[session_idx]["profesor_id"]
                            ):
                                has_professor_busy = True
                                break
                        if not has_professor_busy:
                            candidates.append((cand_day, cand_hour))
                    if candidates:
                        target_day, target_hour = random.choice(candidates)
                        move_session(chrom, session_idx, target_day, target_hour)
                        changed = True
            if not changed:
                break

        still_unassigned = []
        for session_idx in unassigned:
            if not place_session(chrom, session_idx, preferred_first=True):
                still_unassigned.append(session_idx)
        unassigned[:] = still_unassigned

    def evaluate(individual):
        chrom, unassigned = individual

        prof_clashes = 0
        for clashing_sessions in teacher_conflicts_by_slot(chrom).values():
            prof_clashes += len(clashing_sessions) - 1

        # Group clashes are structurally prevented by X[group][day][hour].
        grup_clashes = 0

        prof_day_hours = defaultdict(list)
        group_day_hours = defaultdict(list)
        preference_penalty = 0

        for group_id in group_ids:
            for day in range(n_days):
                for hour in range(n_hours):
                    session_idx = chrom[group_id][day][hour]
                    if session_idx is None:
                        continue
                    session = sessions[session_idx]
                    prof_day_hours[(session["profesor_id"], day)].append(hour)
                    group_day_hours[(group_id, day)].append(hour)

                    preferred = slot_from_preferred(session.get("preferred_slot"))
                    if preferred is not None and preferred != (day, hour):
                        preference_penalty += 10

        gaps = 0
        for hours_list in list(prof_day_hours.values()) + list(group_day_hours.values()):
            unique = sorted(set(hours_list))
            if len(unique) > 1:
                gaps += (unique[-1] - unique[0] + 1) - len(unique)

        conflicts = prof_clashes + grup_clashes
        unassigned_penalty = len(unassigned) * 1000
        fitness = conflicts * 1000 + gaps + preference_penalty + unassigned_penalty
        return fitness, prof_clashes, grup_clashes, len(unassigned)

    def tournament(pop_with_fit, k=3):
        sample = random.sample(pop_with_fit, min(k, len(pop_with_fit)))
        return min(sample, key=lambda item: item[1])[0]

    def crossover(parent1, parent2):
        if random.random() >= crossover_rate:
            best_parent = parent1 if evaluate(parent1)[0] <= evaluate(parent2)[0] else parent2
            return clone_chromosome(best_parent[0]), best_parent[1][:]

        child = empty_chromosome()
        child_unassigned = []

        # Group-based crossover: each group calendar is inherited as a full block.
        for group_id in group_ids:
            source = parent1 if random.random() < 0.5 else parent2
            child[group_id] = copy.deepcopy(source[0][group_id])

        assigned = set()
        duplicates = []
        for group_id in group_ids:
            for day in range(n_days):
                for hour in range(n_hours):
                    session_idx = child[group_id][day][hour]
                    if session_idx is None:
                        continue
                    if session_idx in assigned:
                        child[group_id][day][hour] = None
                        duplicates.append(session_idx)
                    else:
                        assigned.add(session_idx)

        missing = [idx for idx in range(len(sessions)) if idx not in assigned]
        child_unassigned.extend(duplicates + missing)
        repair_chromosome(child, child_unassigned)
        return child, child_unassigned

    def mutate(individual):
        chrom, unassigned = clone_chromosome(individual[0]), individual[1][:]
        for session_idx in range(len(sessions)):
            if random.random() >= mutation_rate:
                continue
            group_id, day, hour = session_position(chrom, session_idx)
            if day is not None:
                chrom[group_id][day][hour] = None
            candidates = available_slots_for_session(chrom, session_idx)
            if candidates:
                target_day, target_hour = random.choice(candidates)
                chrom[group_id][target_day][target_hour] = session_idx
                if session_idx in unassigned:
                    unassigned.remove(session_idx)
            elif session_idx not in unassigned:
                unassigned.append(session_idx)
        repair_chromosome(chrom, unassigned)
        return chrom, unassigned

    population = [preferred_chromosome()]
    while len(population) < pop_size:
        population.append(random_chromosome())

    fitness_history = []
    best_overall = None
    best_overall_fitness = float("inf")

    for _gen in range(generations):
        pop_with_fit = [(individual, evaluate(individual)[0]) for individual in population]
        pop_with_fit.sort(key=lambda item: item[1])
        best_fit = pop_with_fit[0][1]
        fitness_history.append(best_fit)

        if best_fit < best_overall_fitness:
            best_overall_fitness = best_fit
            best_overall = (clone_chromosome(pop_with_fit[0][0][0]), pop_with_fit[0][0][1][:])

        new_pop = [
            (clone_chromosome(pop_with_fit[0][0][0]), pop_with_fit[0][0][1][:]),
            (clone_chromosome(pop_with_fit[1][0][0]), pop_with_fit[1][0][1][:])
            if len(pop_with_fit) > 1
            else (clone_chromosome(pop_with_fit[0][0][0]), pop_with_fit[0][0][1][:]),
        ]

        while len(new_pop) < pop_size:
            parent1 = tournament(pop_with_fit)
            parent2 = tournament(pop_with_fit)
            child = crossover(parent1, parent2)
            child = mutate(child)
            new_pop.append(child)

        population = new_pop

    final_fitness, prof_clashes, grup_clashes, unassigned_count = evaluate(best_overall)
    best_chrom, _best_unassigned = best_overall

    assignments = []
    for group_id in group_ids:
        for day in range(n_days):
            for hour in range(n_hours):
                session_idx = best_chrom[group_id][day][hour]
                if session_idx is None:
                    continue
                session = sessions[session_idx]
                assignments.append({
                    "materia_id": session["id"],
                    "materia_nombre": session["nombre"],
                    "profesor_id": session["profesor_id"],
                    "grupo_id": session["grupo_id"],
                    "day": day,
                    "hour": hour + hora_inicio,
                })

    return {
        "assignments": assignments,
        "fitness_history": fitness_history,
        "broken_rules": {
            "choques_profesor": prof_clashes,
            "choques_grupo": grup_clashes,
            "horas_sin_asignar": unassigned_count,
            "total": prof_clashes + grup_clashes + unassigned_count,
        },
        "best_fitness": final_fitness,
    }

import re
from typing import List, Dict, Optional

_TIME_RE = re.compile(r"^(\d{2}:\d{2})\b")
_SECTION_SPLIT = re.compile(r"(?=(?:GRUPO|Grupo):\s*\d+)", re.IGNORECASE)
_META_RE = {
    "group": re.compile(r"GRUPO:\s*(\S+)", re.IGNORECASE),
    "semester": re.compile(r"SEMESTRE:\s*(.+)", re.IGNORECASE),
    "aula": re.compile(r"AULA:\s*(.+)", re.IGNORECASE),
    "cycle": re.compile(r"CICLO ESCOLAR.*", re.IGNORECASE),
}


def _normalize_cell(text: str) -> str:
    return " ".join(text.replace("\t", " ").split()).strip()


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _split_sections(text: str) -> List[str]:
    normalized = _normalize_text(text)
    sections = [section.strip() for section in _SECTION_SPLIT.split(normalized) if section.strip()]
    return sections


def _extract_metadata(lines: List[str]) -> Dict[str, Optional[str]]:
    metadata = {"group": None, "semester": None, "aula": None, "cycle": None}
    for line in lines:
        for key, regex in _META_RE.items():
            match = regex.match(line)
            if match:
                metadata[key] = match.group(1).strip()
        if metadata["cycle"] is None and _META_RE["cycle"].search(line):
            metadata["cycle"] = line.strip()
    return metadata


def _find_schedule_header(lines: List[str]) -> Optional[int]:
    for idx, line in enumerate(lines):
        if line.strip().upper().startswith("HORA"):
            return idx
    return None


def _collect_schedule_rows(lines: List[str], header_index: int) -> List[str]:
    rows = []
    current = None
    for line in lines[header_index + 1 :]:
        if line.strip().upper().startswith("ASIGNATURA"):
            break
        if _TIME_RE.match(line.strip()):
            if current is not None:
                rows.append(current)
            current = line.strip()
        elif current is not None and line.strip():
            current += " " + line.strip()
    if current is not None:
        rows.append(current)
    return rows


def _distribute_tokens(tokens: List[str], num_groups: int) -> List[str]:
    if not tokens:
        return [""] * num_groups
    if len(tokens) <= num_groups:
        return tokens + [""] * (num_groups - len(tokens))
    base = len(tokens) // num_groups
    remainder = len(tokens) % num_groups
    parts = []
    idx = 0
    for group_index in range(num_groups):
        take = base + (1 if group_index < remainder else 0)
        parts.append(" ".join(tokens[idx : idx + take]))
        idx += take
    return parts


def _split_row_cells(row: str, num_days: int) -> Dict[str, List[str]]:
    parts = [p for p in re.split(r"\s{2,}|\t", row) if _normalize_cell(p)]
    if len(parts) >= num_days + 1 and _TIME_RE.match(parts[0]):
        time = parts[0]
        body = parts[1:]
    else:
        match = _TIME_RE.match(row)
        if not match:
            return {"time": None, "entries": []}
        time = match.group(1)
        body_text = row[match.end() :].strip()
        body_tokens = [t for t in body_text.split() if t]
        body = _distribute_tokens(body_tokens, num_days)
    if len(body) < num_days:
        body.extend([""] * (num_days - len(body)))
    elif len(body) > num_days:
        body = body[: num_days - 1] + [" ".join(body[num_days - 1 :])]
    return {"time": time, "entries": [ _normalize_cell(entry) for entry in body ]}


def _parse_schedule_table(lines: List[str], header_index: int) -> List[Dict[str, object]]:
    header_line = lines[header_index].strip()
    parts = header_line.split()
    days = parts[1:]
    if not days:
        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    rows = _collect_schedule_rows(lines, header_index)
    schedule = []
    for row in rows:
        cells = _split_row_cells(row, len(days))
        if not cells["time"]:
            continue
        schedule.append({
            "time": cells["time"],
            "slots": {day: cells["entries"][idx] for idx, day in enumerate(days)},
        })
    return schedule


def _extract_footer(lines: List[str], header_index: int) -> List[str]:
    footer = []
    found = False
    for idx, line in enumerate(lines):
        if idx <= header_index:
            continue
        if line.strip().upper().startswith("ASIGNATURA"):
            found = True
            continue
        if found:
            if line.strip().upper().startswith("GRUPO:"):
                break
            footer.append(_normalize_cell(line))
    return [line for line in footer if line]


def parse_schedule_sections(raw_text: str) -> List[Dict[str, object]]:
    sections = _split_sections(raw_text)
    parsed = []
    for section in sections:
        lines = [line for line in _normalize_text(section).split("\n") if line.strip()]
        if not lines:
            continue
        metadata = _extract_metadata(lines)
        header_index = _find_schedule_header(lines)
        schedule = []
        days = []
        if header_index is not None:
            schedule = _parse_schedule_table(lines, header_index)
            header_line = lines[header_index].strip()
            days = header_line.split()[1:]
        footer = _extract_footer(lines, header_index if header_index is not None else -1)
        subjects = sorted(
            {cell for row in schedule for cell in row["slots"].values() if cell and cell.upper() not in ["INGLÉS"]}
        )
        parsed.append(
            {
                "group": metadata.get("group"),
                "semester": metadata.get("semester"),
                "aula": metadata.get("aula"),
                "cycle": metadata.get("cycle"),
                "days": days,
                "schedule": schedule,
                "footer_lines": footer,
                "subjects": subjects,
            }
        )
    return parsed

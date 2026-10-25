"""Human-friendly output: terminal table, Markdown (great for PRs / wikis) and JSON."""

from __future__ import annotations

import json

from datasniff.profile import TableProfile


def _short(value: object, width: int = 22) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\n", " ")
    return text if len(text) <= width else text[: width - 1] + "…"


def _top(col) -> str:
    return ", ".join(f"{_short(v, 14)} ({n})" for v, n in col.top_values)


def _rows(profile: TableProfile) -> list[list[str]]:
    return [
        [
            c.name,
            c.dtype,
            f"{c.null_pct:g}%",
            f"{c.distinct:,}",
            _short(c.min),
            _short(c.max),
            _top(c),
            ", ".join(c.flags),
        ]
        for c in profile.columns
    ]


HEADERS = ["column", "type", "nulls", "distinct", "min", "max", "top values", "flags"]


def summary_line(profile: TableProfile) -> str:
    dupes = profile.duplicate_rows
    return (
        f"{profile.source}: {profile.rows:,} rows · {len(profile.columns)} columns · "
        f"{dupes:,} duplicate row{'s' if dupes != 1 else ''}"
    )


def to_text(profile: TableProfile) -> str:
    rows = _rows(profile)
    widths = [
        max(len(h), *(len(r[i]) for r in rows)) if rows else len(h) for i, h in enumerate(HEADERS)
    ]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    lines = [
        summary_line(profile),
        "",
        fmt.format(*HEADERS),
        fmt.format(*("-" * w for w in widths)),
    ]
    lines += [fmt.format(*r) for r in rows]
    return "\n".join(line.rstrip() for line in lines)


def to_markdown(profile: TableProfile) -> str:
    def cell(text: str) -> str:
        return text.replace("|", "\\|")

    lines = [f"### `{profile.source}`", "", summary_line(profile).split(": ", 1)[1], ""]
    lines.append("| " + " | ".join(HEADERS) + " |")
    lines.append("|" + "---|" * len(HEADERS))
    for r in _rows(profile):
        r[0], r[1] = f"`{r[0]}`", f"`{r[1]}`"
        lines.append("| " + " | ".join(cell(x) for x in r) + " |")
    return "\n".join(lines)


def to_json(profile: TableProfile) -> str:
    return json.dumps(profile.to_dict(), indent=2, default=str)

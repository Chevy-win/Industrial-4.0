from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from ortools.sat.python import cp_model


CUOXE_TYPES = {"CUOXE", "CUSTRIP", "CUSOVT"}
TOOL_EQP_TYPES = {"CUSPUT", "CUSILPE", "CUPLATE"}
CHAMBER_OUTPUT_TYPES = {
    "CUOXE",
    "CUSTRIP",
    "CUSOVT",
    "CUNITINCVD",
    "CUSINE",
    "CUMETE",
    "CUBSCLN",
}
INF_RQT = 99_999_999


@dataclass(frozen=True)
class FoupInfo:
    foup: str
    priority: float
    waitingtime: int
    isactive: int
    availfordispatch: int
    ignoreBatchSize: int
    rqteqptype1: str
    rqtseq1: int
    rqt1: int
    rqteqptype2: str
    rqtseq2: int
    rqt2: int
    rqteqptype3: str
    rqtseq3: int
    rqt3: int


@dataclass(frozen=True)
class Eqp:
    eqp: str
    eqptype: str
    availtime: int
    stopdispatchtime: int
    rtdeqptype: int


@dataclass(frozen=True)
class CUSOVTStopPeriod:
    eqp: str
    CUSOVTNextCCStopTime: int
    CUSOVTNextCCStartTime: int


@dataclass(frozen=True)
class Chamber:
    chamber: str
    type: str
    eqp: str
    eqptype: str
    availtime: int
    stopdispatchtime: int
    is40KD22: int


@dataclass(frozen=True)
class Task:
    foup: str
    seq: int
    recipe: str
    component: int
    eqptype: str
    isprocess: int
    assignedpriority: int
    qtimeeqptype1: str
    qtimeseq1: int
    qtimelimit1: int
    qtimeeqptype2: str
    qtimeseq2: int
    qtimelimit2: int
    qtimeeqptype3: str
    qtimeseq3: int
    qtimelimit3: int


@dataclass(frozen=True)
class PPID:
    ppid: str
    ppidnumber: int
    foup: str
    seq: int
    recipe: str
    eqp: str
    eqptype: str
    ptime: int
    advancedinhibit: int
    minbatchwafers: int
    maxbatchwafers: int
    batchsize: int
    minwafercountperbatch: int
    eqrecoverystart: int
    eqrecoveryend: int
    chamber: Tuple[str, ...]


@dataclass(frozen=True)
class RQT:
    rqteqptype: str
    rqtseq: int
    rqt: int


@dataclass(frozen=True)
class Assignment:
    task: Task
    ppid: PPID
    eqp: Eqp


@dataclass
class AssignmentVars:
    start: cp_model.IntVar
    end: cp_model.IntVar
    interval: cp_model.IntervalVar
    presence: cp_model.IntVar


@dataclass
class TaskVars:
    start: cp_model.IntVar
    end: cp_model.IntVar
    presence: cp_model.IntVar


@dataclass
class InputData:
    foupinfos: List[FoupInfo]
    eqps: List[Eqp]
    cusovt_stop_periods: List[CUSOVTStopPeriod]
    chambers: List[Chamber]
    tasks: List[Task]
    ppids: List[PPID]
    TransitTime: int
    DueDate: int
    QtimeUrgent: int
    QtimeBuffer: int
    CuoxeLotSum: int
    CuoxeLotis40KD22: int


def safe_name(value: object) -> str:
    text = str(value)
    text = re.sub(r"[^0-9A-Za-z_]+", "_", text)
    return text[:180]


def read_nonempty_line(handle) -> str:
    line = handle.readline()
    while line and not line.strip():
        line = handle.readline()
    if not line:
        raise EOFError("Unexpected end of input file.")
    return line.strip()


def read_input(path: str) -> InputData:
    with open(path, "r", encoding="utf-8") as handle:
        nb_foups = int(read_nonempty_line(handle))
        foupinfos: List[FoupInfo] = []
        for _ in range(nb_foups):
            x = read_nonempty_line(handle).split()
            if len(x) < 15:
                raise ValueError(f"FoupInfo expects 15 fields, got {len(x)}: {x}")
            foupinfos.append(
                FoupInfo(
                    x[0],
                    float(x[1]),
                    int(x[2]),
                    int(x[3]),
                    int(x[4]),
                    int(x[5]),
                    x[6],
                    int(x[7]),
                    int(x[8]),
                    x[9],
                    int(x[10]),
                    int(x[11]),
                    x[12],
                    int(x[13]),
                    int(x[14]),
                )
            )

        nb_eqps = int(read_nonempty_line(handle))
        eqps: List[Eqp] = []
        for _ in range(nb_eqps):
            x = read_nonempty_line(handle).split()
            if len(x) < 5:
                raise ValueError(f"Eqp expects 5 fields, got {len(x)}: {x}")
            eqps.append(Eqp(x[0], x[1], int(x[2]), int(x[3]), int(x[4])))

        nb_cusovt_stop = int(read_nonempty_line(handle))
        cusovt_stop_periods: List[CUSOVTStopPeriod] = []
        for _ in range(nb_cusovt_stop):
            x = read_nonempty_line(handle).split()
            if len(x) < 3:
                raise ValueError(f"CUSOVTStopPeriod expects 3 fields, got {len(x)}: {x}")
            cusovt_stop_periods.append(CUSOVTStopPeriod(x[0], int(x[1]), int(x[2])))

        nb_chambers = int(read_nonempty_line(handle))
        chambers: List[Chamber] = []
        for _ in range(nb_chambers):
            x = read_nonempty_line(handle).split()
            if len(x) < 7:
                raise ValueError(f"Chamber expects 7 fields, got {len(x)}: {x}")
            chambers.append(Chamber(x[0], x[1], x[2], x[3], int(x[4]), int(x[5]), int(x[6])))

        nb_tasks = int(read_nonempty_line(handle))
        tasks: List[Task] = []
        for _ in range(nb_tasks):
            x = read_nonempty_line(handle).split()
            if len(x) < 16:
                raise ValueError(f"Task expects 16 fields, got {len(x)}: {x}")
            tasks.append(
                Task(
                    x[0],
                    int(x[1]),
                    x[2],
                    int(x[3]),
                    x[4],
                    int(x[5]),
                    int(x[6]),
                    x[7],
                    int(x[8]),
                    int(x[9]),
                    x[10],
                    int(x[11]),
                    int(x[12]),
                    x[13],
                    int(x[14]),
                    int(x[15]),
                )
            )

        nb_ppids = int(read_nonempty_line(handle))
        ppids: List[PPID] = []
        for _ in range(nb_ppids):
            x = read_nonempty_line(handle).split()
            if len(x) < 23:
                raise ValueError(f"PPID expects 23 fields, got {len(x)}: {x}")
            chambers_required = tuple(ch for ch in x[15:23] if ch != "0")
            ppids.append(
                PPID(
                    x[0],
                    int(x[1]),
                    x[2],
                    int(x[3]),
                    x[4],
                    x[5],
                    x[6],
                    int(x[7]),
                    int(x[8]),
                    int(x[9]),
                    int(x[10]),
                    int(x[11]),
                    int(x[12]),
                    int(x[13]),
                    int(x[14]),
                    chambers_required,
                )
            )

        return InputData(
            foupinfos=foupinfos,
            eqps=eqps,
            cusovt_stop_periods=cusovt_stop_periods,
            chambers=chambers,
            tasks=tasks,
            ppids=ppids,
            TransitTime=int(read_nonempty_line(handle)),
            DueDate=int(read_nonempty_line(handle)),
            QtimeUrgent=int(read_nonempty_line(handle)),
            QtimeBuffer=int(read_nonempty_line(handle)),
            CuoxeLotSum=int(read_nonempty_line(handle)),
            CuoxeLotis40KD22=int(read_nonempty_line(handle)),
        )


def contains(text: str, pattern: str) -> bool:
    return pattern in text


def int_var_from_terms(
    model: cp_model.CpModel,
    name: str,
    terms: Sequence[cp_model.LinearExpr],
    lb: int,
    ub: int,
) -> cp_model.IntVar:
    var = model.NewIntVar(lb, max(lb, ub), name)
    if terms:
        model.Add(var == sum(terms))
    else:
        model.Add(var == 0)
    return var


def optional_positive_part(
    model: cp_model.CpModel,
    name: str,
    expr: cp_model.LinearExpr,
    expr_lb: int,
    expr_ub: int,
    presence: cp_model.IntVar,
) -> cp_model.IntVar:
    raw = model.NewIntVar(expr_lb, expr_ub, f"{name}_raw")
    pos = model.NewIntVar(0, max(0, expr_ub), f"{name}_pos")
    out = model.NewIntVar(0, max(0, expr_ub), name)
    model.Add(raw == expr)
    model.AddMaxEquality(pos, [0, raw])
    model.Add(out == pos).OnlyEnforceIf(presence)
    model.Add(out == 0).OnlyEnforceIf(presence.Not())
    return out


def optional_linear_nonnegative(
    model: cp_model.CpModel,
    name: str,
    expr: cp_model.LinearExpr,
    ub: int,
    presence: cp_model.IntVar,
) -> cp_model.IntVar:
    out = model.NewIntVar(0, ub, name)
    model.Add(out == expr).OnlyEnforceIf(presence)
    model.Add(out == 0).OnlyEnforceIf(presence.Not())
    return out


def remaining_qtimes_by_foup(foupinfos: Iterable[FoupInfo]) -> Tuple[Dict[str, RQT], Dict[str, RQT], Dict[str, RQT]]:
    rqt1: Dict[str, RQT] = {}
    rqt2: Dict[str, RQT] = {}
    rqt3: Dict[str, RQT] = {}
    for f in foupinfos:
        rqt1[f.foup] = RQT(f.rqteqptype1, f.rqtseq1, f.rqt1)
        rqt2[f.foup] = RQT(f.rqteqptype2, f.rqtseq2, f.rqt2)
        rqt3[f.foup] = RQT(f.rqteqptype3, f.rqtseq3, f.rqt3)
    return rqt1, rqt2, rqt3


def build_and_solve(data: InputData, time_limit_seconds: float | None = None):
    model = cp_model.CpModel()

    foup_by_id = {f.foup: f for f in data.foupinfos}
    is_active = {f.foup: f.isactive for f in data.foupinfos}
    avail_for_dispatch = {f.foup: f.availfordispatch for f in data.foupinfos}
    ignore_batch_size = {f.foup: f.ignoreBatchSize for f in data.foupinfos}
    rqt1, rqt2, rqt3 = remaining_qtimes_by_foup(data.foupinfos)
    rqts = (rqt1, rqt2, rqt3)

    for foup in foup_by_id:
        if (
            (rqt1[foup].rqt <= data.QtimeUrgent and not contains(rqt1[foup].rqteqptype, "CUOXE"))
            or (rqt2[foup].rqt <= data.QtimeUrgent and not contains(rqt2[foup].rqteqptype, "CUOXE"))
            or (rqt3[foup].rqt <= data.QtimeUrgent and not contains(rqt3[foup].rqteqptype, "CUOXE"))
        ):
            ignore_batch_size[foup] = 1

    all_chamber_ids = {ch.chamber for ch in data.chambers if ch.eqptype in CUOXE_TYPES}
    all_chambers = [ch for ch in data.chambers if ch.chamber in all_chamber_ids]
    cusovt_tasks = [t for t in data.tasks if t.eqptype == "CUSOVT"]
    cusovt_ppids = [p for p in data.ppids if p.eqptype == "CUSOVT"]
    cusovt_eqps = [e for e in data.eqps if e.eqptype == "CUSOVT"]
    tool_eqps = [e for e in data.eqps if e.eqptype in TOOL_EQP_TYPES]
    batch_eqps = [e for e in data.eqps if e.rtdeqptype == 1]

    assignments: List[Assignment] = []
    for t in data.tasks:
        for p in data.ppids:
            if p.foup != t.foup or p.seq != t.seq or p.recipe != t.recipe or p.eqptype != t.eqptype:
                continue
            for e in data.eqps:
                if p.eqp == e.eqp:
                    assignments.append(Assignment(t, p, e))

    assignments_supp: List[Assignment] = []
    for t in cusovt_tasks:
        for p in cusovt_ppids:
            if p.foup != t.foup or p.seq != t.seq or p.recipe != t.recipe or p.eqptype != t.eqptype:
                continue
            for e in cusovt_eqps:
                if p.eqp == e.eqp:
                    assignments_supp.append(Assignment(t, p, e))

    chambers_by_id = {ch.chamber: ch for ch in data.chambers}
    min_dispatch_time: Dict[Assignment, int] = {}
    stop_dispatch_time: Dict[Assignment, int] = {}

    for a in assignments:
        if a.eqp.eqptype in CUOXE_TYPES and a.ppid.chamber:
            required_avail = [
                chambers_by_id[ch].availtime for ch in a.ppid.chamber if ch in chambers_by_id
            ]
            min_dispatch_time[a] = max([avail_for_dispatch[a.task.foup], *required_avail])
        else:
            min_dispatch_time[a] = max(a.eqp.availtime, avail_for_dispatch[a.task.foup])

        stop_time = data.DueDate
        for ch in a.ppid.chamber:
            if ch in chambers_by_id:
                stop_time = min(stop_time, chambers_by_id[ch].stopdispatchtime)
        stop_time = min(stop_time, a.eqp.stopdispatchtime)
        stop_dispatch_time[a] = stop_time

    task_vars: Dict[Task, TaskVars] = {}
    for t in data.tasks:
        suffix = safe_name(f"{t.foup}_{t.seq}_{t.recipe}_{t.eqptype}")
        task_vars[t] = TaskVars(
            start=model.NewIntVar(0, data.DueDate, f"task_start_{suffix}"),
            end=model.NewIntVar(0, data.DueDate, f"task_end_{suffix}"),
            presence=model.NewBoolVar(f"task_presence_{suffix}"),
        )

    assignment_vars: Dict[Assignment, AssignmentVars] = {}
    for idx, a in enumerate(assignments):
        suffix = safe_name(f"{idx}_{a.task.foup}_{a.task.seq}_{a.ppid.ppid}_{a.eqp.eqp}")
        start = model.NewIntVar(min_dispatch_time[a], data.DueDate, f"assignment_start_{suffix}")
        end = model.NewIntVar(min_dispatch_time[a], data.DueDate, f"assignment_end_{suffix}")
        presence = model.NewBoolVar(f"assignment_presence_{suffix}")
        interval = model.NewOptionalIntervalVar(
            start,
            a.ppid.ptime,
            end,
            presence,
            f"assignment_interval_{suffix}",
        )
        assignment_vars[a] = AssignmentVars(start, end, interval, presence)

    # OPL: alternative(tasks[t], all(a in Assignments: a.task == t) assignment[a], 1)
    for t in data.tasks:
        rel = [a for a in assignments if a.task == t]
        if not rel:
            model.Add(task_vars[t].presence == 0)
            continue
        model.Add(sum(assignment_vars[a].presence for a in rel) == task_vars[t].presence)
        for a in rel:
            av = assignment_vars[a]
            tv = task_vars[t]
            model.Add(tv.start == av.start).OnlyEnforceIf(av.presence)
            model.Add(tv.end == av.end).OnlyEnforceIf(av.presence)

    # OPL: assignment_supp mirrors CUSOVT assignment. It has no independent resource usage in the source model.
    assignments_set = set(assignments)
    for a in assignments_supp:
        if a in assignments_set:
            model.Add(assignment_vars[a].presence <= assignment_vars[a].presence)

    # CUSOVT stop periods.
    for a in assignments:
        if a.task.eqptype != "CUSOVT":
            continue
        av = assignment_vars[a]
        for period in data.cusovt_stop_periods:
            if a.eqp.eqp != period.eqp:
                continue
            before = model.NewBoolVar(f"cusovt_before_{safe_name(a)}_{period.CUSOVTNextCCStopTime}")
            after = model.NewBoolVar(f"cusovt_after_{safe_name(a)}_{period.CUSOVTNextCCStartTime}")
            model.Add(av.end <= period.CUSOVTNextCCStopTime - 1).OnlyEnforceIf(before)
            model.Add(av.start >= period.CUSOVTNextCCStartTime + 1).OnlyEnforceIf(after)
            model.AddBoolOr([before, after, av.presence.Not()])

    # OPL sequence constraints.
    for t_pre in data.tasks:
        if t_pre.seq == 0:
            continue
        for t_post in data.tasks:
            if t_pre.foup != t_post.foup or t_post.seq <= t_pre.seq:
                continue
            pre = task_vars[t_pre]
            post = task_vars[t_post]
            model.Add(pre.end + data.TransitTime <= post.start).OnlyEnforceIf(
                [pre.presence, post.presence]
            )
            all_rqt_inf = (
                rqt1[t_pre.foup].rqt == INF_RQT
                and rqt2[t_pre.foup].rqt == INF_RQT
                and rqt3[t_pre.foup].rqt == INF_RQT
            )
            any_cuoxe = (
                contains(rqt1[t_pre.foup].rqteqptype, "CUOXE")
                or contains(rqt2[t_pre.foup].rqteqptype, "CUOXE")
                or contains(rqt3[t_pre.foup].rqteqptype, "CUOXE")
            )
            if all_rqt_inf or any_cuoxe:
                model.Add(pre.presence == post.presence)
            else:
                model.Add(post.presence <= pre.presence)

    # OPL QTime: startBeforeEnd(tasks[t_post], tasks[t_pre], -limit)
    for t_pre in data.tasks:
        if t_pre.seq == 0:
            continue
        qtime_pairs = (
            (t_pre.qtimeseq1, t_pre.qtimelimit1),
            (t_pre.qtimeseq2, t_pre.qtimelimit2),
            (t_pre.qtimeseq3, t_pre.qtimelimit3),
        )
        for t_post in data.tasks:
            if t_pre.foup != t_post.foup:
                continue
            for qtime_seq, qtime_limit in qtime_pairs:
                if qtime_seq == t_post.seq:
                    model.Add(task_vars[t_post].start <= task_vars[t_pre].end + qtime_limit).OnlyEnforceIf(
                        [task_vars[t_pre].presence, task_vars[t_post].presence]
                    )

    # Chamber and tool no-overlap.
    for ch in all_chambers:
        intervals = [
            assignment_vars[a].interval for a in assignments if ch.chamber in a.ppid.chamber
        ]
        if intervals:
            model.AddNoOverlap(intervals)

    for e in tool_eqps:
        intervals = [assignment_vars[a].interval for a in assignments if a.eqp == e]
        if intervals:
            model.AddNoOverlap(intervals)

    # Batch equipment approximation for OPL stateFunction/cumulFunction.
    # Different PPID numbers cannot overlap on the same batch equipment.
    # Same PPID number can overlap up to max batch size. Full alwaysIn lower-bound wafer
    # semantics require time-indexing or explicit batch grouping, which CP-SAT does not
    # provide as a native stateFunction/cumulFunction equivalent.
    for e in batch_eqps:
        rel = [a for a in assignments if a.eqp == e]
        for i, a1 in enumerate(rel):
            for a2 in rel[i + 1 :]:
                if a1.ppid.ppidnumber != a2.ppid.ppidnumber:
                    model.AddNoOverlap([assignment_vars[a1].interval, assignment_vars[a2].interval])
        if rel:
            capacity = max(max(1, a.ppid.batchsize) for a in rel)
            model.AddCumulative(
                [assignment_vars[a].interval for a in rel],
                [1 for _ in rel],
                capacity,
            )

    # Advanced inhibit.
    for a in assignments:
        if a.task.seq != 0 and (
            a.ppid.advancedinhibit < data.DueDate or stop_dispatch_time[a] < data.DueDate
        ):
            model.Add(assignment_vars[a].start <= min(a.ppid.advancedinhibit, stop_dispatch_time[a])).OnlyEnforceIf(
                assignment_vars[a].presence
            )

    # Eq recovery.
    for a in assignments:
        if a.task.seq != 0 and (
            a.ppid.eqrecoverystart < data.DueDate or a.ppid.eqrecoveryend < data.DueDate
        ):
            before = model.NewBoolVar(f"recovery_before_{safe_name(a)}")
            after = model.NewBoolVar(f"recovery_after_{safe_name(a)}")
            model.Add(assignment_vars[a].start <= a.ppid.eqrecoverystart - 1).OnlyEnforceIf(before)
            model.Add(assignment_vars[a].start >= a.ppid.eqrecoveryend + 1).OnlyEnforceIf(after)
            model.AddBoolOr([before, after, assignment_vars[a].presence.Not()])

    # Priority 40KD.
    for ch in all_chambers:
        if ch.eqptype == "CUOXE" and ch.is40KD22 == 1:
            non_40kd = [
                a
                for a in assignments
                if a.eqp.eqp == ch.eqp and not contains(a.task.recipe, "40KD-22")
            ]
            is_40kd = [
                a
                for a in assignments
                if a.eqp.eqp == ch.eqp and contains(a.task.recipe, "40KD-22")
            ]
            for a_pre in non_40kd:
                for a_post in is_40kd:
                    if a_pre.eqp != a_post.eqp:
                        continue
                    model.Add(assignment_vars[a_post].start <= assignment_vars[a_pre].end).OnlyEnforceIf(
                        [assignment_vars[a_post].presence, assignment_vars[a_pre].presence]
                    )

    # Objective expressions from staticLex.
    absence_urgent_terms: List[cp_model.LinearExpr] = []
    violation_urgent_terms: List[cp_model.LinearExpr] = []
    absence_rqt_terms: List[cp_model.LinearExpr] = []
    violation_rqt_terms: List[cp_model.LinearExpr] = []

    for t in data.tasks:
        if t.seq == 0:
            continue
        tv = task_vars[t]
        for rqt_map in rqts:
            rqt = rqt_map[t.foup]
            if rqt.rqtseq != t.seq:
                continue
            urgent_non_cuoxe = (
                0 < rqt.rqt <= 180
                and is_active[t.foup] == 1
                and not contains(rqt.rqteqptype, "CUOXE")
            )
            over_qtime = rqt.rqt <= 0
            regular_rqt = (
                (
                    rqt.rqt > 180
                    and rqt.rqt < INF_RQT
                    and is_active[t.foup] == 1
                    and not contains(rqt.rqteqptype, "CUOXE")
                )
                or (
                    rqt.rqt > 0
                    and rqt.rqt < INF_RQT
                    and is_active[t.foup] == 0
                    and not contains(rqt.rqteqptype, "CUOXE")
                )
                or (
                    0 < rqt.rqt <= 180
                    and is_active[t.foup] == 1
                    and contains(rqt.rqteqptype, "CUOXE")
                )
            )

            if urgent_non_cuoxe:
                absence_urgent_terms.append(1 - tv.presence)
                violation_urgent_terms.append(
                    optional_positive_part(
                        model,
                        f"rqt_urgent_{safe_name(t)}_{safe_name(rqt)}",
                        tv.start - rqt.rqt + data.QtimeUrgent,
                        -INF_RQT,
                        data.DueDate + data.QtimeUrgent,
                        tv.presence,
                    )
                )
            if over_qtime:
                absence_urgent_terms.append((1 - tv.presence) * 100)
                violation_urgent_terms.append(
                    optional_linear_nonnegative(
                        model,
                        f"rqt_over_{safe_name(t)}_{safe_name(rqt)}",
                        (tv.start - rqt.rqt) * 100,
                        (data.DueDate + abs(rqt.rqt)) * 100,
                        tv.presence,
                    )
                )
            if regular_rqt:
                absence_rqt_terms.append(1 - tv.presence)
                violation_rqt_terms.append(
                    optional_positive_part(
                        model,
                        f"rqt_regular_{safe_name(t)}_{safe_name(rqt)}",
                        tv.start - rqt.rqt + data.QtimeUrgent,
                        -INF_RQT,
                        data.DueDate + data.QtimeUrgent,
                        tv.presence,
                    )
                )

    absence_active_terms: List[cp_model.LinearExpr] = []
    absence_flowin_terms: List[cp_model.LinearExpr] = []
    cycle_active_terms: List[cp_model.LinearExpr] = []
    cycle_flowin_terms: List[cp_model.LinearExpr] = []
    cycle_priority_terms: List[cp_model.LinearExpr] = []

    for t in data.tasks:
        if t.seq == 0 or t.isprocess != 1:
            continue
        tv = task_vars[t]
        is_active_first_non_cuoxe = (
            not contains(t.eqptype, "CUOXE") and t.seq == 1 and is_active[t.foup] == 1
        )
        is_flowin = contains(t.eqptype, "CUOXE") or t.seq > 1 or is_active[t.foup] == 0
        if is_active_first_non_cuoxe:
            absence_active_terms.append((1 - tv.presence) * t.assignedpriority)
            cycle_active_terms.append(optional_linear_nonnegative(model, f"end_active_{safe_name(t)}", tv.end, data.DueDate, tv.presence))
        if is_flowin:
            absence_flowin_terms.append((1 - tv.presence) * t.assignedpriority)
            cycle_flowin_terms.append(optional_linear_nonnegative(model, f"end_flowin_{safe_name(t)}", tv.end, data.DueDate, tv.presence))
        if not contains(t.eqptype, "CUOXE"):
            cycle_priority_terms.append(
                optional_linear_nonnegative(
                    model,
                    f"end_priority_{safe_name(t)}",
                    tv.end * t.assignedpriority,
                    data.DueDate * max(0, t.assignedpriority),
                    tv.presence,
                )
            )

    max_priority_sum = sum(max(0, t.assignedpriority) for t in data.tasks)
    objectives = [
        int_var_from_terms(model, "absenceOfTaskUrgentRQT", absence_urgent_terms, 0, len(absence_urgent_terms) * 100),
        int_var_from_terms(model, "rqtViolationUrgent", violation_urgent_terms, 0, len(violation_urgent_terms) * (data.DueDate + INF_RQT) * 100),
        int_var_from_terms(model, "absenceOfTaskRQT", absence_rqt_terms, 0, len(absence_rqt_terms)),
        int_var_from_terms(model, "rqtViolation", violation_rqt_terms, 0, len(violation_rqt_terms) * (data.DueDate + data.QtimeUrgent)),
        int_var_from_terms(model, "absenceOfTaskActive", absence_active_terms, 0, max_priority_sum),
        int_var_from_terms(model, "absenceOfTaskFlowIn", absence_flowin_terms, 0, max_priority_sum),
        int_var_from_terms(model, "totalCycleTimeActive", cycle_active_terms, 0, data.DueDate * len(cycle_active_terms)),
        int_var_from_terms(model, "totalCycleTimeFlowIn", cycle_flowin_terms, 0, data.DueDate * len(cycle_flowin_terms)),
        int_var_from_terms(model, "totalCycleTimePriority", cycle_priority_terms, 0, data.DueDate * max_priority_sum),
    ]

    solver = cp_model.CpSolver()
    if time_limit_seconds:
        solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = 8

    objective_values: List[int] = []
    status = cp_model.UNKNOWN
    for objective in objectives:
        model.Minimize(objective)
        status = solver.Solve(model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return model, solver, status, assignments, assignment_vars, objective_values
        value = solver.Value(objective)
        objective_values.append(value)
        if status == cp_model.OPTIMAL:
            model.Add(objective == value)
        else:
            model.Add(objective <= value)

    return model, solver, status, assignments, assignment_vars, objective_values


def write_output(
    path: str,
    solver: cp_model.CpSolver,
    assignments: Sequence[Assignment],
    assignment_vars: Dict[Assignment, AssignmentVars],
) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["type", "foupId", "seq", "recipe", "PPID", "eqpId", "chamberId", "start", "end", "processTime"])
        for a in assignments:
            av = assignment_vars[a]
            if solver.Value(av.presence) != 1:
                continue
            start = solver.Value(av.start)
            end = solver.Value(av.end)
            process_time = end - start
            if a.eqp.eqptype not in CHAMBER_OUTPUT_TYPES:
                if a.task.seq != 0:
                    writer.writerow(["Eqp", a.task.foup, a.task.seq, a.task.recipe, a.ppid.ppid, a.eqp.eqp, "", start, end, process_time])
                else:
                    writer.writerow(["Eqp", "", a.task.seq, a.task.recipe, "", a.eqp.eqp, "", start, end, process_time])
            else:
                for chamber in a.ppid.chamber:
                    if a.task.seq != 0:
                        writer.writerow(["Chamber", a.task.foup, a.task.seq, a.task.recipe, a.ppid.ppid, a.eqp.eqp, chamber, start, end, process_time])
                    else:
                        writer.writerow(["Chamber", "", a.task.seq, a.task.recipe, "", a.eqp.eqp, chamber, start, end, process_time])


def main() -> int:
    parser = argparse.ArgumentParser(description="OR-Tools CP-SAT conversion of CPLEXModel.txt.")
    parser.add_argument("--input", default="data.txt", help="Input data file. Default: data.txt")
    parser.add_argument("--output", default="output.csv", help="Output CSV file. Default: output.csv")
    parser.add_argument("--time-limit", type=float, default=None, help="Time limit per lexicographic objective solve.")
    args = parser.parse_args()

    data = read_input(args.input)
    _, solver, status, assignments, assignment_vars, objective_values = build_and_solve(data, args.time_limit)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"No feasible solution. Status={solver.StatusName(status)}")
        return 2

    write_output(args.output, solver, assignments, assignment_vars)
    print(f"Status: {solver.StatusName(status)}")
    print(f"Objective values: {objective_values}")
    print(f"Output written to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


from dataclasses import dataclass
from typing import List, Dict, Set, Tuple
from ortools.sat.python import cp_model
import csv

model = cp_model.CpModel()

@dataclass(frozen=True)
class FoupInfo:
    foup: str
    priority: float
    waitingtime: int
    isactive: int
    availfordispatch: int
    rqteqptype1: str
    rqtseq1: int
    rqt1: int

@dataclass(frozen=True)
class Eqp:
    eqp: str
    eqptype: str
    availtime: int
    stopdispatchtime: int

@dataclass(frozen=True)
class Chamber:
    chamber: str
    type: str
    eqp: str
    eqptype: str
    availtime: int
    stopdispatchtime: int

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
    eqrecoverystart: int
    eqrecoveryend: int
    chamber: Tuple[str]

@dataclass
class RQT:
    rqteqptype: str
    rqtseq: int
    rqt: int

@dataclass(frozen=True)
class Assignment:
    task: Task
    ppid: PPID
    eqp: Eqp

# 1. Foups 及相关属性
Foups: Set[str] = set()
Priority: Dict[str, float] = {}
WaitingTime: Dict[str, int] = {}
IsActive: Dict[str, int] = {}
AvailForDispFoup: Dict[str, int] = {}
RemainingQTime1: Dict[str, RQT] = {}

def read_foupinfos(f, n):
    result = []
    for _ in range(n):
        line = f.readline().strip().split()
        result.append(FoupInfo(
            foup=line[0],
            priority=float(line[1]),
            waitingtime=int(line[2]),
            isactive=int(line[3]),
            availfordispatch=int(line[4]),
            rqteqptype1=line[5],
            rqtseq1=int(line[6]),
            rqt1=int(line[7])
        ))
    return result

def read_eqps(f, n):
    result = []
    for _ in range(n):
        line = f.readline().strip().split()
        result.append(Eqp(
            eqp=line[0],
            eqptype=line[1],
            availtime=int(line[2]),
            stopdispatchtime=int(line[3])
        ))
    return result

def read_chambers(f, n):
    result = []
    for _ in range(n):
        line = f.readline().strip().split()
        result.append(Chamber(
            chamber=line[0],
            type=line[1],
            eqp=line[2],
            eqptype=line[3],
            availtime=int(line[4]),
            stopdispatchtime=int(line[5])
        ))
    return result

def read_tasks(f, n):
    result = []
    for _ in range(n):
        line = f.readline().strip().split()
        result.append(Task(
            foup=line[0],
            seq=int(line[1]),
            recipe=line[2],
            component=int(line[3]),
            eqptype=line[4],
            isprocess=int(line[5]),
            assignedpriority=int(line[6]),
            qtimeeqptype1=line[7],
            qtimeseq1=int(line[8]),
            qtimelimit1=int(line[9])
        ))
    return result

def read_ppids(f, n):
    result = []
    for _ in range(n):
        line = f.readline().strip().split()
        # 假設 chamber 欄位在最後，且為多個以逗號分隔的字符串
        chamber_list = line[11:]
        result.append(PPID(
            ppid=line[0],
            ppidnumber=int(line[1]),
            foup=line[2],
            seq=int(line[3]),
            recipe=line[4],
            eqp=line[5],
            eqptype=line[6],
            ptime=int(line[7]),
            advancedinhibit=int(line[8]),
            eqrecoverystart=int(line[9]),
            eqrecoveryend=int(line[10]),
            chamber=tuple(chamber_list)
        ))
    return result

with open('input.txt', 'r') as f:
    n_foup = int(f.readline())
    foupinfos = read_foupinfos(f, n_foup)
    n_eqp = int(f.readline())
    eqps = read_eqps(f, n_eqp)
    n_chamber = int(f.readline())
    chambers = read_chambers(f, n_chamber)
    n_task = int(f.readline())
    tasks = read_tasks(f, n_task)
    n_ppid = int(f.readline())
    ppids = read_ppids(f, n_ppid)
    transferTime = int(f.readline())
    DueDate = int(f.readline())
    qtimeUrgent = int(f.readline())
    qtimeBuffer = int(f.readline())

for f in foupinfos:
    Foups.add(f.foup)
    Priority[f.foup] = f.priority
    WaitingTime[f.foup] = f.waitingtime
    IsActive[f.foup] = f.isactive
    AvailForDispFoup[f.foup] = f.availfordispatch
    RemainingQTime1[f.foup] = RQT(
        rqteqptype=f.rqteqptype1,
        rqtseq=f.rqtseq1,
        rqt=f.rqt1
    )
# 2. AllChamberIds
AllChamberIds: Set[str] = set()
for ch in chambers:
    if ch.eqptype == "EPIG":
        AllChamberIds.add(ch.chamber)
# 3. AllChambers
AllChambers: Set[Chamber] = set()
for ch in chambers:
    if ch.chamber in AllChamberIds:
        AllChambers.add(ch)
# 4. ToolEqps
ToolEqps: Set[Eqp] = set()
for e in eqps:
    if e.eqptype != "EPIG":
        ToolEqps.add(e)
# 5. Assignments
Assignments: Set[Assignment] = set()
for t in tasks:
    for p in ppids:
        for e in eqps:
            if (p.eqp == e.eqp and p.foup == t.foup and p.seq == t.seq and
                p.recipe == t.recipe and p.eqptype == t.eqptype):
                Assignments.add(Assignment(task=t, ppid=p, eqp=e))

# 6. MinDispatchTime
def maxl(a, b):
    return max(a, b)

MinDispatchTime: Dict[Assignment, int] = {}
for a in Assignments:
    if a.eqp.eqptype == "EPIG":
        for ch in chambers:
            if ch.chamber in a.ppid.chamber:
                MinDispatchTime[a] = maxl(ch.availtime, AvailForDispFoup[a.task.foup])
    else:
        MinDispatchTime[a] = maxl(a.eqp.availtime, AvailForDispFoup[a.task.foup])

# 7. StopDispatchTime
def minl(a, b):
    return min(a, b)

def matchAt(s, pattern):
    """模拟 OPL 的 matchAt，返回 -1 表示不包含，>=0 表示包含"""
    return s.find(pattern)

StopDispatchTime: Dict[Assignment, int] = {}
for a in Assignments:
    StopDispatchTime[a] = DueDate

for a in Assignments:
    for ch in chambers:
        if ch.chamber in a.ppid.chamber:
            StopDispatchTime[a] = minl(ch.stopdispatchtime, StopDispatchTime[a])

for a in Assignments:
    if a.eqp.stopdispatchtime < DueDate:
        StopDispatchTime[a] = minl(a.eqp.stopdispatchtime, StopDispatchTime[a])

# Decision Variables
tasks_vars = {}
for t in Tasks:
    # 这里假设每个任务的处理时间为 t.ptime（你可以根据实际情况调整）
    # 由于 OPL 的 optional interval，Python 里用 presence_lit 实现
    presence = model.NewBoolVar(f"presence_task_{t}")
    start = model.NewIntVar(0, DueDate, f"start_task_{t}")
    end = model.NewIntVar(0, DueDate, f"end_task_{t}")
    interval = model.NewOptionalIntervalVar(start, t.ptime, end, presence, f"interval_task_{t}")
    tasks_vars[t] = (start, end, interval, presence)

assignment_vars = {}
for a in Assignments:
    presence = model.NewBoolVar(f"presence_assignment_{a}")
    start = model.NewIntVar(MinDispatchTime[a], DueDate, f"start_assignment_{a}")
    end = model.NewIntVar(MinDispatchTime[a], DueDate, f"end_assignment_{a}")
    interval = model.NewOptionalIntervalVar(start, a.ppid.ptime, end, presence, f"interval_assignment_{a}")
    assignment_vars[a] = (start, end, interval, presence)

seqChamber = {}
for ch in AllChambers:
    relevant_assignments = [a for a in Assignments if ch.chamber in a.ppid.chamber]
    intervals = [assignment_vars[a][2] for a in relevant_assignments]
    if intervals:
        seqChamber[ch] = model.AddNoOverlap(intervals)

seqEqp = {}
for e in ToolEqps:
    relevant_assignments = [a for a in Assignments if a.eqp == e]
    intervals = [assignment_vars[a][2] for a in relevant_assignments]
    if intervals:
        seqEqp[e] = model.AddNoOverlap(intervals)

absenceOfTaskUrgentRQT = []
for t in Tasks:
    cond1 = (t.seq != 0 and
             RemainingQTime1[t.foup].rqtseq == t.seq and
             0 < RemainingQTime1[t.foup].rqt <= 60 and
             IsActive[t.foup] == 1 and
             "CAROZ" not in RemainingQTime1[t.foup].rqteqptype)
    cond2 = (t.seq != 0 and
             RemainingQTime1[t.foup].rqtseq == t.seq and
             RemainingQTime1[t.foup].rqt <= 0)
    if cond1:
        absenceOfTaskUrgentRQT.append(1 - tasks_vars[t][3])
    if cond2:
        absenceOfTaskUrgentRQT.append((1 - tasks_vars[t][3]) * 100)
absenceOfTaskUrgentRQT_expr = sum(absenceOfTaskUrgentRQT)

rqtViolationUrgent = []
for t in Tasks:
    cond1 = (t.seq != 0 and
             RemainingQTime1[t.foup].rqtseq == t.seq and
             0 < RemainingQTime1[t.foup].rqt <= 60 and
             IsActive[t.foup] == 1 and
             "CAROZ" not in RemainingQTime1[t.foup].rqteqptype)
    cond2 = (t.seq != 0 and
             RemainingQTime1[t.foup].rqtseq == t.seq and
             RemainingQTime1[t.foup].rqt <= 0)
    if cond1:
        # maxl(0, (startOf(tasks[t]) - RemainingQTime1[t.foup].rqt + QtimeUrgent))
        start = tasks_vars[t][0]
        expr = model.NewIntVar(0, DueDate, f"rqtViolationUrgent_{t}")
        model.AddMaxEquality(expr, [0, start - RemainingQTime1[t.foup].rqt + QtimeUrgent])
        rqtViolationUrgent.append(expr)
    if cond2:
        start = tasks_vars[t][0]
        expr = (start - RemainingQTime1[t.foup].rqt) * 100
        rqtViolationUrgent.append(expr)
rqtViolationUrgent_expr = sum(rqtViolationUrgent)

absenceOfTaskRQT_terms = []
for t in Tasks:
    rqt = RemainingQTime1[t.foup].rqt
    rqtseq = RemainingQTime1[t.foup].rqtseq
    rqteqptype = RemainingQTime1[t.foup].rqteqptype
    is_active = IsActive[t.foup]
    cond = (
        t.seq != 0 and
        rqtseq == t.seq and (
            (rqt > 60 and rqt < 99999999 and is_active == 1 and matchAt(rqteqptype, "CAROZ") == -1) or
            (rqt > 0 and rqt < 99999999 and is_active == 0 and matchAt(rqteqptype, "CAROZ") == -1) or
            (rqt > 0 and rqt <= 60 and is_active == 1 and matchAt(rqteqptype, "CAROZ") > -1)
        )
    )
    if cond:
        presence = tasks_vars[t][3]  # presence bool var
        absenceOfTaskRQT_terms.append(1 - presence)
absenceOfTaskRQT = model.NewIntVar(0, len(absenceOfTaskRQT_terms), "absenceOfTaskRQT")
model.Add(absenceOfTaskRQT == sum(absenceOfTaskRQT_terms))


rqtViolation_terms = []
for t in Tasks:
    rqt = RemainingQTime1[t.foup].rqt
    rqtseq = RemainingQTime1[t.foup].rqtseq
    rqteqptype = RemainingQTime1[t.foup].rqteqptype
    is_active = IsActive[t.foup]
    cond = (
        t.seq != 0 and
        rqtseq == t.seq and (
            (rqt > 60 and rqt < 99999999 and is_active == 1 and matchAt(rqteqptype, "CAROZ") == -1) or
            (rqt > 0 and rqt < 99999999 and is_active == 0 and matchAt(rqteqptype, "CAROZ") == -1) or
            (rqt > 0 and rqt <= 60 and is_active == 1 and matchAt(rqteqptype, "CAROZ") > -1)
        )
    )
    if cond:
        start = tasks_vars[t][0]
        # maxl(0, (startOf(tasks[t]) - rqt + QtimeUrgent))
        violation = model.NewIntVar(0, 100000000, f"rqtViolation_{t}")
        model.AddMaxEquality(violation, [0, start - rqt + QtimeUrgent])
        rqtViolation_terms.append(violation)
rqtViolation = model.NewIntVar(0, 100000000 * len(rqtViolation_terms), "rqtViolation")
model.Add(rqtViolation == sum(rqtViolation_terms))

absenceOfTaskActive_terms = []
for t in Tasks:
    cond = (
        t.seq != 0 and t.isprocess == 1 and matchAt(t.eqptype, "CAROZ") == -1 and t.seq == 1 and IsActive[t.foup] == 1
    )
    if cond:
        presence = tasks_vars[t][3]
        absenceOfTaskActive_terms.append((1 - presence) * t.assignedpriority)
absenceOfTaskActive = model.NewIntVar(0, sum(t.assignedpriority for t in Tasks), "absenceOfTaskActive")
model.Add(absenceOfTaskActive == sum(absenceOfTaskActive_terms))

absenceOfTaskFlowIn_terms = []
for t in Tasks:
    cond = (
        t.seq != 0 and t.isprocess == 1 and
        (matchAt(t.eqptype, "CAROZ") > -1 or t.seq > 1 or IsActive[t.foup] == 0)
    )
    if cond:
        presence = tasks_vars[t][3]
        absenceOfTaskFlowIn_terms.append((1 - presence) * t.assignedpriority)
absenceOfTaskFlowIn = model.NewIntVar(0, sum(t.assignedpriority for t in Tasks), "absenceOfTaskFlowIn")
model.Add(absenceOfTaskFlowIn == sum(absenceOfTaskFlowIn_terms))

totalCycleTimeActive_terms = []
for t in Tasks:
    cond = (
        t.seq != 0 and t.isprocess == 1 and matchAt(t.eqptype, "CAROZ") == -1 and t.seq == 1 and IsActive[t.foup] == 1
    )
    if cond:
        end = tasks_vars[t][1]
        totalCycleTimeActive_terms.append(end)
totalCycleTimeActive = model.NewIntVar(0, DueDate * len(totalCycleTimeActive_terms), "totalCycleTimeActive")
model.Add(totalCycleTimeActive == sum(totalCycleTimeActive_terms))

totalCycleTimeFlowIn_terms = []
for t in Tasks:
    cond = (
        t.seq != 0 and t.isprocess == 1 and
        (matchAt(t.eqptype, "CAROZ") > -1 or t.seq > 1 or IsActive[t.foup] == 0)
    )
    if cond:
        end = tasks_vars[t][1]
        totalCycleTimeFlowIn_terms.append(end)
totalCycleTimeFlowIn = model.NewIntVar(0, DueDate * len(totalCycleTimeFlowIn_terms), "totalCycleTimeFlowIn")
model.Add(totalCycleTimeFlowIn == sum(totalCycleTimeFlowIn_terms))

totalCycleTimePriority_terms = []
for t in Tasks:
    cond = (
        t.seq != 0 and t.isprocess == 1 and matchAt(t.eqptype, "CAROZ") == -1
    )
    if cond:
        end = tasks_vars[t][1]
        totalCycleTimePriority_terms.append(end * t.assignedpriority)
totalCycleTimePriority = model.NewIntVar(0, DueDate * sum(t.assignedpriority for t in Tasks), "totalCycleTimePriority")
model.Add(totalCycleTimePriority == sum(totalCycleTimePriority_terms))

#tasks_vars[t][0] 是 start，[1] 是 end，[3] 是 presence（可选变量）
#model.NewIntVar(...) 用于定义表达式变量，model.Add(...) 约束表达式等于和式
#matchAt 用 Python 的字符串查找实现
model.Minimize(
    absenceOfTaskUrgentRQT * 10**10 +
    rqtViolationUrgent * 10**8 +
    absenceOfTaskRQT * 10**7 +
    rqtViolation * 10**6 +
    absenceOfTaskActive * 10**5 +
    absenceOfTaskFlowIn * 10**4 +
    totalCycleTimeActive * 10**3 +
    totalCycleTimeFlowIn * 10**1 +
    totalCycleTimePriority
)

# constraint
# Sequence
for t_pre in Tasks:
    if t_pre.seq != 0:
        for t_post in Tasks:
            if t_pre.foup == t_post.foup and t_post.seq > t_pre.seq:
                # endBeforeStart(tasks[t_pre], tasks[t_post], TransitTime)
                model.Add(tasks_vars[t_pre][1] + TransitTime <= tasks_vars[t_post][0])
                # presenceOf 逻辑
                rqt = RemainingQTime1[t_pre.foup].rqt
                rqteqptype = RemainingQTime1[t_pre.foup].rqteqptype
                if (rqt == 99999999) or (rqteqptype.find("CAROZ") > -1):
                    model.Add(tasks_vars[t_pre][3] == tasks_vars[t_post][3])
                else:
                    # presenceOf(tasks[t_post]) => presenceOf(tasks[t_pre])
                    model.Add(tasks_vars[t_post][3] <= tasks_vars[t_pre][3])
# Qtime
for t_pre in Tasks:
    if t_pre.seq != 0:
        for t_post in Tasks:
            if t_pre.foup == t_post.foup:
                if t_pre.qtimeseq1 == t_post.seq:
                    # startBeforeEnd(tasks[t_post], tasks[t_pre], -ftoi(t_pre.qtimelimit1))
                    model.Add(tasks_vars[t_post][0] <= tasks_vars[t_pre][1] - int(t_pre.qtimelimit1))

for a in Assignments:
    if a.task.seq != 0 and (a.ppid.advancedinhibit < DueDate or StopDispatchTime[a] < DueDate):
        model.Add(assignment_vars[a][0] <= min(a.ppid.advancedinhibit, StopDispatchTime[a]))

for t in Tasks:
    # 找到所有 assignment[a] 使 a.task == t
    relevant_assignments = [assignment_vars[a][2] for a in Assignments if a.task == t]
    if relevant_assignments:
        model.AddAlternative(tasks_vars[t][2], relevant_assignments)

# output
with open('output.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["type", "foupId", "seq", "recipe", "PPID", "eqpId", "chamberId", "start", "end", "processTime"])
    for a in Assignments:
        start_var, end_var, interval_var, presence_var = assignment_vars[a]
        if solver.Value(presence_var):
            start = solver.Value(start_var)
            end = solver.Value(end_var)
            process_time = end - start
            if a.eqp.eqptype != "EPIG":
                if a.task.seq != 0:
                    writer.writerow([
                        "Eqp", a.task.foup, a.task.seq, a.task.recipe, a.ppid.ppid, a.eqp.eqp, "", start, end, process_time
                    ])
                else:
                    writer.writerow([
                        "Eqp", "", a.task.seq, a.task.recipe, "", a.eqp.eqp, "", start, end, process_time
                    ])
            else:
                for c in a.ppid.chamber:
                    if a.task.seq != 0:
                        writer.writerow([
                            "Chamber", a.task.foup, a.task.seq, a.task.recipe, a.ppid.ppid, a.eqp.eqp, c, start, end, process_time
                        ])
                    else:
                        writer.writerow([
                            "Chamber", "", a.task.seq, a.task.recipe, "", a.eqp.eqp, c, start, end, process_time
                        ])

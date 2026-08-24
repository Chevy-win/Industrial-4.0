import platform
import sys

import ortools
from ortools.sat.python import cp_model


def main() -> None:
    model = cp_model.CpModel()
    x = model.new_int_var(0, 10, "x")
    model.maximize(x)

    solver = cp_model.CpSolver()
    status = solver.solve(model)
    if status != cp_model.OPTIMAL or solver.value(x) != 10:
        raise RuntimeError("CP-SAT verification model did not solve correctly.")

    print(f"Python: {sys.version.split()[0]} ({platform.architecture()[0]})")
    print(f"OR-Tools: {ortools.__version__}")
    print("CP-SAT verification: OK")


if __name__ == "__main__":
    main()

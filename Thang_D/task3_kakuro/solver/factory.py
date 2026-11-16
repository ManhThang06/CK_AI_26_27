"""SolverFactory: tao BacktrackingSolver tu ten heuristic (dung chung cho CLI, UI, kiem thu)."""
from .backtracking import BacktrackingSolver
from .heuristics import VALUE_ORDERERS, VARIABLE_SELECTORS


class SolverFactory:
    VARIABLES = VARIABLE_SELECTORS
    VALUES = VALUE_ORDERERS

    @classmethod
    def variable_names(cls):
        return list(cls.VARIABLES)

    @classmethod
    def value_names(cls):
        return list(cls.VALUES)

    @classmethod
    def create(cls, puzzle, variable="mrv-degree", value="lcv", max_nodes=None, recorder=None):
        return BacktrackingSolver(puzzle, cls.VARIABLES[variable](), cls.VALUES[value](),
                                  recorder=recorder, max_nodes=max_nodes)

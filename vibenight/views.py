import json

from django.shortcuts import render

from .sudoku import DIFFICULTY_CLUES, generate_puzzle


def index(request):
    return render(request, "vibenight/index.html")


def sudoku(request):
    difficulty = request.GET.get("difficulty", "medium")
    if difficulty not in DIFFICULTY_CLUES:
        difficulty = "medium"
    puzzle, solution = generate_puzzle(difficulty)
    context = {
        "puzzle": puzzle,
        "solution_json": json.dumps(solution),
        "difficulty": difficulty,
        "difficulties": list(DIFFICULTY_CLUES.keys()),
    }
    return render(request, "vibenight/sudoku.html", context)

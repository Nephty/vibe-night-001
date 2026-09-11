import random

DIFFICULTY_CLUES = {"easy": 40, "medium": 32, "hard": 26}


def _valid(grid, r, c, num):
    for i in range(9):
        if grid[r][i] == num or grid[i][c] == num:
            return False
    br, bc = 3 * (r // 3), 3 * (c // 3)
    for i in range(br, br + 3):
        for j in range(bc, bc + 3):
            if grid[i][j] == num:
                return False
    return True


def generate_full_grid():
    grid = [[0] * 9 for _ in range(9)]

    def fill(pos):
        if pos == 81:
            return True
        r, c = divmod(pos, 9)
        nums = list(range(1, 10))
        random.shuffle(nums)
        for num in nums:
            if _valid(grid, r, c, num):
                grid[r][c] = num
                if fill(pos + 1):
                    return True
                grid[r][c] = 0
        return False

    fill(0)
    return grid


def generate_puzzle(difficulty="medium"):
    clues = DIFFICULTY_CLUES.get(difficulty, DIFFICULTY_CLUES["medium"])
    solution = generate_full_grid()
    puzzle = [row[:] for row in solution]
    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    for r, c in cells[: 81 - clues]:
        puzzle[r][c] = 0
    return puzzle, solution

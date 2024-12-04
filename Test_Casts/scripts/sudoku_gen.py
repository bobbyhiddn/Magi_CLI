import random

def create_empty_grid():
    return [[0 for _ in range(9)] for _ in range(9)]

def get_possibilities(grid, row, col):
    """Convert your square_check concept into finding valid possibilities"""
    possibilities = set(range(1, 10))
    
    # Check row
    possibilities -= set(grid[row])
    
    # Check column
    possibilities -= set(grid[i][col] for i in range(9))
    
    # Check 3x3 box
    box_row, box_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(box_row, box_row + 3):
        for j in range(box_col, box_col + 3):
            possibilities.discard(grid[i][j])
            
    return list(possibilities)

def find_empty_cell(grid):
    """Find next empty cell to fill"""
    for i in range(9):
        for j in range(9):
            if grid[i][j] == 0:
                return i, j
    return None

def generate_filled_grid():
    """Generate a completely filled valid Sudoku grid"""
    grid = create_empty_grid()
    
    def fill_grid(grid):
        # Find empty cell
        empty = find_empty_cell(grid)
        if not empty:
            return True  # Grid is filled
            
        row, col = empty
        
        # Get valid possibilities for this cell
        possibilities = get_possibilities(grid, row, col)
        random.shuffle(possibilities)  # Randomize for variety
        
        # Try each possibility
        for num in possibilities:
            grid[row][col] = num
            
            if fill_grid(grid):  # Recursively fill rest of grid
                return True
                
            grid[row][col] = 0  # Backtrack if didn't work
            
        return False
    
    fill_grid(grid)
    return grid

def create_puzzle(filled_grid, difficulty=40):
    """Create puzzle by removing numbers from filled grid"""
    puzzle = [row[:] for row in filled_grid]
    cells = [(i, j) for i in range(9) for j in range(9)]
    random.shuffle(cells)
    
    # Remove numbers while maintaining unique solution
    for row, col in cells[:difficulty]:
        puzzle[row][col] = 0
    
    return puzzle

def print_grid(grid):
    """Print grid in readable format"""
    for i, row in enumerate(grid):
        if i % 3 == 0 and i != 0:
            print("-" * 21)
        for j, num in enumerate(row):
            if j % 3 == 0 and j != 0:
                print("|", end=" ")
            print(num if num != 0 else ".", end=" ")
        print()

# Example usage
def generate_sudoku():
    print("Generating filled grid...")
    filled = generate_filled_grid()
    print("\nFilled grid:")
    print_grid(filled)
    
    print("\nCreating puzzle...")
    puzzle = create_puzzle(filled)
    print("\nPuzzle (. represents empty cells):")
    print_grid(puzzle)
    return puzzle, filled

if __name__ == "__main__":
    puzzle, solution = generate_sudoku()
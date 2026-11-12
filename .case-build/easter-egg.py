"""Draws the easter egg at the top of the page source: plus icons growing outward around a message,
like the 'crosses growing out' loop in the 3D view (and the favicon)."""
W, H = 79, 25
CX, CY = W // 2, H // 2
grid = [[' '] * W for _ in range(H)]

def put(x, y, ch='+'):
    if 0 <= x < W and 0 <= y < H:
        grid[y][x] = ch

def cross(x, y, arm):
    # Characters are about twice as tall as wide, so horizontal arms step two columns.
    put(x, y)
    for a in range(1, arm + 1):
        put(x - 2 * a, y); put(x + 2 * a, y); put(x, y - a); put(x, y + a)

# the outer field: the further from the message, the bigger the plus
for gy in (-1, 0, 1):
    for gx in (-2, -1, 0, 1, 2):
        if gy == 0 and abs(gx) < 2:
            continue  # the message and its frame sit here
        cross(CX + gx * 16, CY + gy * 8, min(abs(gx) + abs(gy), 3))

# four small pluses frame the message, as in the favicon
for x, y in [(CX, CY - 3), (CX, CY + 3), (CX - 11, CY), (CX + 11, CY)]:
    cross(x, y, 1)

msg = 'you found me!'
for i, ch in enumerate(msg):
    grid[CY][CX - len(msg) // 2 + i] = ch

art = '\n'.join(''.join(row).rstrip() for row in grid)
assert '--' not in art and '>' not in art and '<' not in art
print(art)

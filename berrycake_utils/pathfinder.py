import time
import math
import heapq
import system.lib.minescript as minescript

IMPASSABLE_BLOCKS = {"minecraft:water", "minecraft:lava", "minecraft:cactus", "minecraft:fire","minecraft:wither_rose"}
PASSABLE_BLOCKS = {"minecraft:air","minecraft:torch","minecraft:sugar_cane","minecraft:rail","minecraft:detector_rail","minecraft:activator_rail","minecraft:powered_rail","minecraft:short_dry_grass","minecraft:tall_dry_grass","minecraft:tall_grass", "minecraft:short_grass","minecraft:snow","minecraft:soul_torch","minecraft:redstone_wire","minecraft:redstone_torch","minecraft:redstone_wall_torch","minecraft:repeater","minecraft:comparator","minecraft:flower_pot","minecraft:rose_bush","minecraft:poppy","minecraft:allium","minecraft:azalea_bush","minecraft:azure_bluet","minecraft:blue_orchid","minecraft:brown_mushroom","minecraft:closed_eyeblossom","minecraft:cornflower","minecraft:crimson_fungus","minecraft:crimson_roots","minecraft:dandelion","minecraft:fern","minecraft:dead_bush","minecraft:lily_of_the_valley","minecraft:open_eyeblossom","minecraft:orange_tulip","minecraft:oxeye_daisy","minecraft:pink_tulip","minecraft:red_mushroom","minecraft:red_tulip","minecraft:torchflower","minecraft:warped_fungus","minecraft:warped_roots","minecraft:white_tulip","minecraft:acacia_pressure_plate","minecraft:bamboo_pressure_plate","minecraft:birch_pressure_plate","minecraft:cherry_pressire_plate","minecraft:crimson_pressure_plate","minecraft:dark_oak_pressure_plate","minecraft:heavy_weighted_pressure_plate","minecraft:jungle_pressure_plate","minecraft:light_weighted_pressure_plate","minecraft:mangrove_pressure_plate","minecraft:oak_pressure_plate","minecraft:pale_oak_pressure_plate","minecraft:polished_blackstone_pressure_plate","minecraft:spruce_pressure_plate","minecraft:stone_pressure_plate","minecraft:stone_pressure_plate","minecraft:warped_pressure_plate"}


# configuration
NODE_TIMEOUT_SEC = 15.0
DIAGONAL_COST_PENALTY = 0.0   # additional cost for diagonal movement if desired
main = __name__ == "__main__"

last_point = (0, 0, 0)
def lerp(a, b, t):
    return a + (b - a) * t

def lerp3(p1, p2, t):
    return tuple(lerp(a, b, t) for a, b in zip(p1, p2))

def tweenpointat(location):
    global last_point
    point = last_point
    last_point = lerp3(point, location, 0.2)
    # If player_look_at expects coordinates, keep this; if it expects yaw/pitch, convert first.
    try:
        minescript.player_look_at(*lerp3(point, location, 0.2))
    except Exception:
        # fallback: if player_look_at expects yaw,pitch you need to compute them
        pass

class Node:
    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position
        self.g = 0.0
        self.h = 0.0
        self.f = 0.0

    def __eq__(self, other):
        return isinstance(other, Node) and self.position == other.position

    def __lt__(self, other):
        return self.f < other.f

    def __hash__(self):
        return hash(self.position)

def _is_solid_block(block_id):
    """Return True if the block id represents a solid block (not passable)."""
    if not block_id:
        return False
    # exact-match logic: treat any id in PASSABLE_BLOCKS as non-solid, anything else is solid,
    # except block ids in IMPASSABLE_BLOCKS which are treated as forbidden support.
    if block_id in PASSABLE_BLOCKS:
        return False
    return True

def _is_impassable_block(block_id):
    if not block_id:
        return False
    return block_id in IMPASSABLE_BLOCKS

def _is_walkable(pos, world_data, dest_pos=None):
    """
    Checks if a 2-block-high entity can stand at 'pos'.
    world_data is expected to map (x,y,z)->block_id (string like 'minecraft:stone').
    dest_pos optionally used for debug logging; pass (x,y,z) of destination.
    """
    # positions to inspect
    feet = tuple(map(int, pos))
    head = (feet[0], feet[1] + 1, feet[2])
    support = (feet[0], feet[1] - 1, feet[2])

    block_head = world_data.get(head, "minecraft:air")
    block_feet = world_data.get(feet, "minecraft:air")
    block_support = world_data.get(support, "minecraft:air")

    head_clear = (block_head in PASSABLE_BLOCKS) or (block_head == "minecraft:air")
    feet_clear = (block_feet in PASSABLE_BLOCKS) or (block_feet == "minecraft:air")
    support_solid = _is_solid_block(block_support) and not _is_impassable_block(block_support)

    walkable = head_clear and feet_clear and support_solid

    # optional debug: show why destination fails
    if dest_pos is not None and feet == tuple(map(int, dest_pos)):
        if main:
            minescript.echo(f"Debug dest {feet} head={block_head}, feet={block_feet}, support={block_support}, walkable={walkable}")

    return walkable

def _can_move_corner_cut(curr, neighbor, world_data):
    """
    Prevent cutting through a corner: if moving diagonally in x/z, ensure both orthogonal neighbors are walkable
    E.g. moving from (x,y,z) to (x+1,y,z+1) is only allowed if (x+1,y,z) and (x,y,z+1) are also walkable.
    """
    (cx, cy, cz) = curr
    (nx, ny, nz) = neighbor
    dx = nx - cx
    dz = nz - cz

    # only check horizontal diagonal
    if abs(dx) == 1 and abs(dz) == 1 and ny == cy:
        n1 = (cx + dx, cy, cz)
        n2 = (cx, cy, cz + dz)
        return _is_walkable(n1, world_data) and _is_walkable(n2, world_data)
    return True

def find_path(start_pos, end_pos, world_data, max_nodes=2500000):
    """
    A* pathfinder. world_data: dict[(x,y,z)] -> block_id (string).
    Returns list of (x,y,z) tuples from start to end, or [] if none.
    """
    start_node = Node(None, tuple(map(int, start_pos)))
    end_node = Node(None, tuple(map(int, end_pos)))
    open_heap = []
    closed_set = set()
    open_dict = {}

    start_node.g = 0.0
    start_node.h = math.dist(start_node.position, end_node.position)
    start_node.f = start_node.h
    heapq.heappush(open_heap, start_node)
    open_dict[start_node.position] = start_node

    nodes_processed = 0
    start_time = time.time()
    minescript.echo(f'§4[§c§lBerryCake§c❤§4]§f ')

    while open_heap:
        # timeout guard by time
        if time.time() - start_time > NODE_TIMEOUT_SEC:
            minescript.echo("find_path: timeout by time")
            return []

        current_node = heapq.heappop(open_heap)
        open_dict.pop(current_node.position, None)

        if current_node.position in closed_set:
            continue
        closed_set.add(current_node.position)

        nodes_processed += 1
        if nodes_processed > max_nodes:
            minescript.echo(f'§4[§c§lBerryCake§c❤§4]§f max nodes processed: TERMINATING PATHFINDER')
            return []

        # reached target
        if current_node.position == end_node.position:
            path = []
            cur = current_node
            while cur:
                path.append(cur.position)
                cur = cur.parent
            minescript.echo(f'§4[§c§lBerryCake§c❤§4]§f nodes processed:  {nodes_processed} in {time.time() - start_time}')
            minescript.echo(f'§4[§c§lBerryCake§c❤§4]§f {len(path)} path length')
            return path[::-1]

        (x, y, z) = current_node.position
        # neighbors (26 around including vertical); may be adjusted to restrict vertical movement if desired
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if dx == 0 and dy == 0 and dz == 0:
                        continue
                    neighbor_pos = (x + dx, y + dy, z + dz)

                    if neighbor_pos in closed_set:
                        continue

                    # must be within reasonable world bounds? optionally check here

                    # quickly reject if not walkable
                    if not _is_walkable(neighbor_pos, world_data, dest_pos=end_pos):
                        continue

                    # prevent corner cutting for horizontal diagonals
                    if not _can_move_corner_cut(current_node.position, neighbor_pos, world_data):
                        continue

                    move_cost = current_node.g + math.sqrt(dx * dx + dy * dy + dz * dz)
                    if dy > 0:
                        move_cost += 0.5  # climbing penalty

                    existing = open_dict.get(neighbor_pos)
                    if existing and existing.g <= move_cost:
                        continue

                    neighbor_node = Node(current_node, neighbor_pos)
                    neighbor_node.g = move_cost
                    neighbor_node.h = math.dist(neighbor_pos, end_node.position)
                    neighbor_node.f = neighbor_node.g + neighbor_node.h

                    heapq.heappush(open_heap, neighbor_node)
                    open_dict[neighbor_pos] = neighbor_node

    # no path found
    minescript.echo('§4[§c§lBerryCake§c❤§4]§f No path found :( TERMINATING PATHFINDER')
    return []

def debug_glow_path(path, delay=0.05):
    minescript.echo(f'§4[§c§lBerryCake§c❤§4]§f starting visualisation')
    minescript.echo(path)
    for block in path:
        minescript.execute(f'/fill {block[0]} {block[1]} {block[2]} {block[0]} {block[1]} {block[2]} minecraft:glowstone')
        


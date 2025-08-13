import system.lib.minescript as ms  # MineScript API for interacting with Minecraft
import time
import keyboard
import json
import os
import berrycake_utils.pathfinder as pf


class WorldDB:
    """
    WorldDB is a dynamic in-memory database of blocks in the player's nearby area.

    GOAL:
        - Keep track of all non-air blocks around the player.
        - Continuously load chunks around the player into memory.
        - Unload chunks that are too far away to save memory.
        - Optionally modify or query these stored blocks.

    HOW IT WORKS:
        - Divides the world into chunks (16x16 columns, full height).
        - Each chunk is stored as a dictionary of coordinates -> block type.
        - A set number of chunks around the player are kept loaded in memory.
    """

    def __init__(self, world_center=[0, 128, 0], xsize=16, y_bottom=-64, y_top=150, zsize=16):
        """
        Initialize the database.
        
        Args:
            world_center (list): Starting center position [x, y, z].
            xsize (int): Chunk size in X axis (default = 16).
            ysize (int): Half the chunk height scanned up/down from center.
            zsize (int): Chunk size in Z axis (default = 16).
        """
        self.running = True

        # Ensure coordinates are integers
        self.world_center = [int(i) for i in world_center]
        
        # Coordinate offsets for scanning a chunk
        self.x_search = list(range(0, xsize))
        y_list_top =  y_top - self.world_center[1]
        y_list_bottom = y_bottom - self.world_center[1]
        self.y_search = list(range(y_list_bottom, y_list_top))
        self.z_search = list(range(0, zsize))

        # render distance for loading and unloading
        self.render_distance = 10

        # Set of chunk origin positions currently tracked
        self.chunk_origins_coll = set()

        # Main database: {chunk_origin: {block_coord: block_type}}
        self.world_db = {}

    # ---------------------------------------------------
    # CHUNK HANDLING
    # ---------------------------------------------------

    def generate_chunk_origins(self):
        """
        Calculate which chunk origins should be loaded based on player's position.
        Stores them in self.chunk_origins_coll.

        Args:
            grid_size (int): How many chunks in each direction from player to track.
        """
        grid_size = self.render_distance

        current_player_pos = ms.player_position()

        # Find which chunk the player is in
        a = current_player_pos[0] // 16
        b = current_player_pos[2] // 16 

        # Generate surrounding chunk coordinates
        grid_depth = list(range(-grid_size // 2, grid_size // 2))
        all_a = [a + i for i in grid_depth]
        all_b = [b + i for i in grid_depth]

        # Add each chunk's origin position to the set
        for x in all_a:
            for z in all_b:
                coord = (int(x * 16), 128, int(z * 16))
                self.chunk_origins_coll.add(coord)

    def generate_chunk(self, chunk_center):
        """
        Scan a single chunk, storing all non-air blocks into the database.
        
        Args:
            chunk_center (tuple): (x, y, z) origin of the chunk.
        """
        coords = []

        x0, y0, z0 = chunk_center

        # Generate a list of every block coordinate in this chunk
        for x in self.x_search:
            for y in self.y_search:
                for z in self.z_search:
                    coords.append([x0 + x, y0 + y, z0 + z])

        # Query block types from MineScript
        block_types = ms.getblocklist(coords)
        chunk_dict = dict(zip([tuple(i) for i in coords], block_types))

        ## Remove air blocks to save memory
        #chunk_dict = {coord: btype for coord, btype in chunk_dict.items() if btype != 'minecraft:air'}
    
        self.add_chunk(chunk_dict, (x0, y0, z0))
    
    def add_chunk(self, chunk_dict, chunk_start_pos):
        """Add a scanned chunk's data to the database."""
        self.world_db[chunk_start_pos] = chunk_dict

    def generate_world(self):
        """Generate all chunks in self.chunk_origins_coll that are not already loaded."""
        for chunk_origin in self.chunk_origins_coll:
            if chunk_origin not in self.world_db:
                self.generate_chunk(chunk_origin)

    def unload_chunks(self):
        """
        Unload chunks too far from the player.
        
        Args:
            max_distance (int): Max chunk distance to keep in memory.
        """
        max_distance = self.render_distance

        self.chunks_to_remove = []
        player_pos = ms.player_position()
        current_chunk = (player_pos[0] // 16, player_pos[2] // 16)

        for chunk in list(self.world_db.keys()):
            x_dist = abs(chunk[0] // 16 - current_chunk[0])
            z_dist = abs(chunk[2] // 16 - current_chunk[1])

            if x_dist > max_distance // 2 or z_dist > max_distance // 2:
                self.chunks_to_remove.append(chunk)

        '''
        for showcase - /fill chunk coord minecraft:air
        '''

        for chunk in self.chunks_to_remove:
            # remove this line to remove visualisation
            #ms.execute(f'/fill {chunk[0]} {chunk[1]} {chunk[2]} {chunk[0] + 15} {chunk[1]} {chunk[2] + 15} minecraft:air')

            del self.world_db[chunk]
            self.chunk_origins_coll.remove(chunk)

    # ---------------------------------------------------
    # DATA TOOLS
    # ---------------------------------------------------

    def filter_top_blocks(self, db):
        """
        Get the highest block for each X/Z coordinate.
        
        Args:
            db (dict): World database to process.
        
        Returns:
            dict: {(x,z): (x,y,z)}
        """
        topdb = {}
        for chunk in db.values():
            for coord in chunk.keys():
                coordxz = (coord[0], coord[2])
                coordy = coord[1]
                if coordxz not in topdb or coordy > topdb[coordxz][1]:
                    topdb[coordxz] = coord
        return topdb

    def fill_blocks_from_dict(self, block_dict, type='minecraft:diamond_block'):
        """
        Fill specific block locations with diamond blocks.
        
        Args:
            block_dict (dict): Dictionary of coordinates to replace.
        """
        for coord in block_dict.values():
            ms.execute(f'/fill {coord[0]} {coord[1]} {coord[2]} {coord[0]} {coord[1]} {coord[2]} minecraft:diamond_block')

    def flattend(self):
        """
        Combine all chunks into a single dictionary of blocks.

        Returns:
            dict: {block_coord: block_type}
        """
        flat = {}
        for chunk in self.world_db.values():
            for coord, block_type in chunk.items():
                flat[coord] = block_type
        return flat
    


    def save_to_json(self, filename="world_data.json"):
        script_dir = os.path.dirname(os.path.abspath(__file__))  # folder where the script is
        file_path = os.path.join(script_dir, filename)

        serializable = {}
        for chunk_origin, blocks in self.world_db.items():
            chunk_key = f"{chunk_origin[0]},{chunk_origin[1]},{chunk_origin[2]}"
            serializable[chunk_key] = {
                f"{b[0]},{b[1]},{b[2]}": block_type
                for b, block_type in blocks.items()
            }

        with open(file_path, "w") as f:
            json.dump(serializable, f, indent=4)


    def load_from_json(self, filename="world_data.json"):
        """Load the JSON file and convert all keys back to tuples."""
        with open(filename, "r") as f:
            data = json.load(f)

        deserialized = {}

        for chunk_key, blocks in data.items():
            chunk_origin = tuple(map(int, chunk_key.split(",")))

            block_dict = {
                tuple(map(int, b_key.split(","))): block_type
                for b_key, block_type in blocks.items()
            }

            deserialized[chunk_origin] = block_dict

        self.world_db = deserialized    

    # ---------------------------------------------------
    # MAIN LOOP - wil be run in the berrycake client main loop
    # ---------------------------------------------------

    def run(self):
        """Main loop: load nearby chunks, unload far ones, repeat forever."""

        start_time_cycle = time.time()
        # Step 1: Identify which chunks should be loaded
        self.generate_chunk_origins()
        #for chunk in [i for i in self.world_db.keys()]:
        #    ms.execute(f'/fill {chunk[0]} {chunk[1]} {chunk[2]} {chunk[0] + 15} {chunk[1]} {chunk[2] + 15} minecraft:diamond_block')
        # Step 2: Remove chunks that are too far away
        self.unload_chunks()
        # Step 3: Load chunks not yet loaded
        self.generate_world()
        

        ## Step 4: Print debug info
        ms.echo(f'Done 1 cycle in {time.time() - start_time_cycle:.2f} secs')
        ms.echo(f'Loaded chunks: {len(self.world_db)}')
        ms.echo(self.render_distance)
        # keyboard_input
        if keyboard.is_pressed('up'):
            self.render_distance += 1
        elif keyboard.is_pressed('down'):
            if self.render_distance > 0:
                self.render_distance -= 1
        elif keyboard.is_pressed('p'):
            ms.echo('p pressed')
            pf.debug_glow_path(pf.find_path(ms.player_position(), [-479, 100, -151], self.flattend()))
            ms.echo('done')
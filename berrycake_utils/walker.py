import system.lib.minescript as ms
from berrycake_utils.camctrl import CameraControl
import time
from berrycake_utils.pathfinder import find_path


class Walker:
    def __init__(self, path, sprint=True, briding=False, breaking=False):
        self.path = path


    def parse_path(self, path):
        new_path = []
        for coord in path:
            new_path.append((coord[0] + 0.5, coord[1] + 0.5,coord[2] + 0.5))

        return new_path

    def walk(self, close_distance=1, timer_per_block=1.5, repathing_dist=4.5):
        for coord in self.path:
            target_orientation = CameraControl.calculate_orientation(coord)

            start_time = time.time()
            while time.time() - start_time < timer_per_block:
                player_x, player_y, player_z = ms.player_position()
                dist = ((player_x - coord[0]) ** 2 +
                        (player_y - coord[1]) ** 2 +
                        (player_z - coord[2]) ** 2) ** 0.5

                # Stop if we're close enough to this node
                if dist <= close_distance:
                    #ms.player_press_forward(False)
                    ms.player_press_jump(False)
                    break

                # Face target
                CameraControl.lock_target(target_orientation, max_step=4.0, timeout=0.18)

                # Jump if needed
                _, ppitch = ms.player_orientation()
                if ppitch < -1:
                    ms.player_press_jump(True)
                else:
                    ms.player_press_jump(False)

                # Move forward
                ms.player_press_forward(True)

                time.sleep(0.02)  # tick delay

            player_x, player_y, player_z = ms.player_position()
            dist = ((player_x - coord[0]) ** 2 +
                        (player_y - coord[1]) ** 2 +
                        (player_z - coord[2]) ** 2) ** 0.5
            if dist >= repathing_dist:      
                ms.echo('§4[§c§lBerryCake§c❤§4]§f REPATHING - stuck')
                return 'stuck'
            


        ms.player_press_forward(False)
        ms.player_press_jump(False)
        return 'done'



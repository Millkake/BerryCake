import system.lib.minescript as ms
import time
import math
import random

class CameraControl:
    @staticmethod
    def target_entity(target_name='Iron Golem'):
        """
        Acquire the coordinates of a specified entity (Iron Golem, Zombie, etc.)
        Returns a tuple (x, y, z) or None if not found.
        """
        entities = ms.get_entities()
        for entity in entities:
            if entity.name == target_name:
                return entity.position
        return None

    @staticmethod
    def calculate_orientation(target_pos):
        """
        Calculates yaw and pitch to look at a target position.
        Returns (yaw, pitch) or None if target_pos is None.
        """
        if target_pos is None:
            return None

        player_pos = ms.player_position()

        dx = target_pos[0] - player_pos[0]
        dy = target_pos[1] - player_pos[1]
        dz = target_pos[2] - player_pos[2]

        yaw = math.degrees(math.atan2(-dx, dz))
        distance_xz = math.sqrt(dx * dx + dz * dz)
        pitch = math.degrees(math.atan2(-dy, distance_xz))
        return yaw, pitch

    @staticmethod
    def step_towards(current, target, max_step):
        """
        Steps from current angle to target angle with max_step degrees per tick.
        """
        diff = target - current
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360

        step = max_step
        if abs(diff) < step:
            return target
        return current + step if diff > 0 else current - step

    @staticmethod
    def lock_target(orientation, max_step=8.0, timeout=0.3):
        """
        Moves camera toward orientation (yaw, pitch) quickly.
        Stops when orientation reached or timeout passed.
        """
        if orientation is None:
            return False

        pyaw, ppitch = ms.player_orientation()
        if pyaw > 180:
            pyaw -= 360

        gyaw, gpitch = orientation

        start_time = time.time()
        while time.time() - start_time < timeout:
            pyaw = CameraControl.step_towards(pyaw, gyaw, max_step)
            pitch_diff = gpitch - ppitch
            if abs(pitch_diff) < max_step:
                ppitch = gpitch
            else:
                ppitch += max_step if pitch_diff > 0 else -max_step

            # Add slight randomization for natural feel
            jitter_yaw = pyaw + random.uniform(-0.3, 0.3)
            jitter_pitch = ppitch + random.uniform(-0.2, 0.2)

            ms.player_set_orientation(jitter_yaw, jitter_pitch)

            if int(pyaw) == int(gyaw) and int(ppitch) == int(gpitch):
                break

            time.sleep(0.006)
        return True

#CameraControl.lock_target(CameraControl.calculate_orientation(target_pos=CameraControl.target_entity('Iron Golem')))
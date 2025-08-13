import system.lib.minescript as ms
import time
import math

class CameraControl:
    @staticmethod
    def target_entity(target_name='Iron Golem'):
        '''
        acquire the coordinates of an entity that is specified above
        target_name=Iron Golem, Zombie, ...
        '''

        entities = ms.get_entities()
        for entity in entities:
            if entity.name == target_name:
                return entity.position


    @staticmethod
    def calculate_orientation(target_pos=target_entity()):
        '''
        calculates the yaw and pitch that the player needs to look at a certain coordinate
        '''

        player_pos = ms.player_position()
        target_pos = target_pos

        dx = target_pos[0] - player_pos[0]
        dy = target_pos[1] - player_pos[1]
        dz = target_pos[2] - player_pos[2]

        yaw = math.degrees(math.atan2(-dx, dz))
        distance_xz = math.sqrt(dx * dx + dz * dz)
        pitch = math.degrees(math.atan2(-dy, distance_xz))
        return yaw, pitch


    @staticmethod
    def step_towards(current, target, max_step):
        diff = target - current
        # Normalize diff to -180..180 for yaw to handle wraparound properly
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360

        step = max_step * min(1, abs(diff) / 30)  # scale step based on difference (30 degrees max for full step)
        if abs(diff) < step:
            return target
        return current + step if diff > 0 else current - step


    @staticmethod
    def lock_target(orientation=calculate_orientation(), max_step=2.0, timeout=0.9):
        porient = ms.player_orientation()
        pyaw = porient[0]
        if pyaw > 180:
            pyaw -= 360
        ppitch = porient[1]
        gyaw = orientation[0]
        gpitch = orientation[1]

        dt = 0
        while (int(pyaw) != int(gyaw) or int(ppitch) != int(gpitch)) and dt < timeout:
            start = time.time()
            pyaw = CameraControl.step_towards(pyaw, gyaw, max_step)
            # pitch doesn’t wrap, so simple approach:
            pitch_diff = gpitch - ppitch
            pitch_step = max_step * min(1, abs(pitch_diff) / 30)
            if abs(pitch_diff) < pitch_step:
                ppitch = gpitch
            else:
                ppitch += pitch_step if pitch_diff > 0 else -pitch_step

            ms.player_set_orientation(pyaw, ppitch)
            time.sleep(0.005)
            dt += time.time() - start
            ms.echo(dt)

CameraControl.lock_target(orientation=CameraControl.calculate_orientation(target_pos=CameraControl.target_entity(target_name='Iron Golem')))



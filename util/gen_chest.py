import system.lib.minescript as ms
from system.lib.minescript_plus import Inventory
import random
import time

START_SLOT = 0
END_SLOT = 26
slots = list(range(START_SLOT, END_SLOT + 1))
random.shuffle(slots)

# yaw: 0=south, 90=west, -90=east, 180/-180=north
tp = ms.player_get_targeted_block().position
player_yaw = ms.player_orientation()[0]
# Normalize yaw to -180..180
player_yaw = ((player_yaw + 180) % 360)

# Map yaw ranges to facing directions (front of chest)
if -45 <= player_yaw < 45:
    facing = 'south'
elif 45 <= player_yaw < 135:
    facing = 'west'
elif player_yaw >= 135 or player_yaw < -135:
    facing = 'north'
else:  # -135 <= yaw < -45
    facing = 'east'

# Place chest one block above targeted block
ms.execute(f'/fill {tp[0]} {tp[1] + 1} {tp[2]} {tp[0]} {tp[1] + 1} {tp[2]} minecraft:chest[facing={facing}]')
#DEBUG
ms.echo(f'Yaw: {player_yaw}, Facing: {facing}')


material_weights = {
    'leather': 0.3,
    'chainmail': 0.2,
    'iron': 0.2,
    'golden': 0.08,
    'diamond': 0.1,
    'netherite': 0.05
}

type_weights = {
    '_helmet': 0.32,
    '_chestplate': 0.12,
    '_leggings': 0.28,
    '_boots': 0.28
}

mat_total = sum(material_weights.values())
material_weights = {m: w / mat_total for m, w in material_weights.items()}

type_total = sum(type_weights.values())
type_weights = {t: w / type_total for t, w in type_weights.items()}

combined_weights = {
    m + t: mw * tw
    for m, mw in material_weights.items()
    for t, tw in type_weights.items()
}


def gen_armour(amount=3):
    return random.choices(population=list(combined_weights.keys()), weights=list(combined_weights.values()), k=amount)


for i, item in enumerate(gen_armour(5)):
    slot = slots[i]  # guaranteed unique slot
    itemid = item
    count = 1
    ms.execute(f"/item replace block {tp[0]} {tp[1] + 1} {tp[2]} container.{slot} with {itemid} {count}")


  
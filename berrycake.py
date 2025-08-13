import system.lib.minescript as ms  
import time
import keyboard
import json
import os
from berrycake_utils.worlddb import WorldDB

class BerryCake:
    def __init__(self):
        ms.echo('§4[§c§lBerryCake§c❤§4]§f launched BerryCake')
        # setup variables
        self.running = True

        # classes that run in main loop
        self.world_db = WorldDB()
    

    def run(self):
        # main loop, add functionality in here that needs to be ran continuously
        # safety - kills immeadiatley on press of 'q'
        ms.execute('\safetycheck')
        while self.running:
            self.world_db.run()




berrycake = BerryCake()
berrycake.run()
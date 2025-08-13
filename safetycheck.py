
import system.lib.minescript as ms
import time
import keyboard
import json
import os

while True:
    if keyboard.is_pressed('q'):
        print("You pressed Q!")
        ms.execute('\killjob -1')
        filename = 'pftest.json'
        script_dir = os.path.dirname(os.path.abspath(__file__))  # folder where the script is
        file_path = os.path.join(script_dir, filename)
        #os.remove(file_path)
    time.sleep(0.08)

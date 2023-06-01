import os.path
import time
import warnings
from typing import SupportsFloat, Any, Tuple, Dict
from rcon.source import Client
import json
import utils as U
import uuid

# We will not be using a javascript server
class FoyagerEnv():
    def __init__(
        self,
        server_ip="127.0.0.1",
        rcon_port= 27015,
        rcon_password= None,
        player_id=1,
        log_path="/opt/factorio/factorio-current.log",
        
    ):
        self.player_id = player_id
        self.log_path = log_path
        self.server_ip=server_ip
        self.rcon_port = rcon_port
        self.rcon_password = rcon_password
    def observe(self,entities,client):
        for entity in entities:
            client.run(f"/c remote.call('writeouts', 'writeout_filtered_entities', '{entity}')")
                
    """
    Sends a script to the factorio engine to be loaded and executed
    
    Args:
        function_name: The name of the script function to be loaded
        code: Script code
    Returns:
        json : {
            'load_script_response' : load_script_response,
            'execute_script_response': execute_script_response
        }
    """
    def step(
    self,
    function_name: str = "",
    code: str = "",
    refresh_entities: list[str] = []
    ) -> json:
        client = Client(self.server_ip, self.rcon_port, passwd=self.rcon_password)
        with client as c:
            if code:
                    load_message_id = uuid.uuid4()
                    c.run(f"/c remote.call('scripts', 'load_script', '{load_message_id}', '{function_name}', '{code}'")
                    
                    execute_message_id = uuid.uuid4()
                    c.run(f"/c remote.call('scripts', 'execute_script', '{execute_message_id}', '{function_name})")

            # events is the return value of the command and the state of any entities requested refreshed after the execution        
            events = []
            # TODO fix this up. It was breaking with 
            # command_res = self.get_response(load_message_id, execute_message_id)
            # events.append(json.load(command_res)            
            for entity in refresh_entities:
                if entity == 'resources':
                    deposits = U.mod_utils.resource_clustering()
                    event = deposits

                else:
                    event = U.mod_utils.process_filtered_entity(entity)
    
                events.append(event)

        return events
    


    """
    Get the response for loading and executing a script from the Factorio engine

    Args:
        load_message_id: The message id to attach to log outputs for loading the script
        execute_message_id: The message id to attach to log outputs for executing the script
    Returns:
        json : {
            'load_script_response' : load_script_response,
            'execute_script_response': execute_script_response
        }
    """
    def get_response(
    self,
    load_message_id,
    execute_message_id
    ) -> json:

        if not os.path.isfile():
            raise FileNotFoundError(self.log_path + " cannot be found")
        else:
            with open(self.log_path) as f:
                content = f.read().splitlines()
                # Find lines containing load_message_id and execute_message_id
                
                load_script_response = ""
                execute_script_response = ""
                
                for line in content:
                    if load_message_id in line:
                        load_script_response += line + '\n'
                    elif execute_message_id in line:
                        execute_script_response += line + '\n'
                        
                r = json.loads({'load_script_response' : load_script_response, 'execute_script_response': execute_script_response})
                return r
                
    def render(self):
        raise NotImplementedError("render is not implemented")

    """
    Resets the factorio environment.

    Args:
        options={
                    "mode": "soft"/"hard",
                    "wait_ticks": How many ticks to wait,
                }
    Returns:
        None
    """
    def reset(self,mode,wait_ticks,refresh_entities):
        client = Client(self.server_ip, self.rcon_port, passwd=self.rcon_password)
        with client as c:
            if mode == "soft":
                # reload mods to wipe game state
                c.run(f"/c game.reload_mods()")

            # hard reset, re observe state, reload and wait
            elif mode == "hard":
                self.observe(refresh_entities,client)
                c.run(f"/c game.reload_mods()")
                        
                if wait_ticks != 0:
                    time.sleep(wait_ticks)

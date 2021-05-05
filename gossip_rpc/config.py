# Author: Ritesh G

import json
import os


class Configuration(object):

    def __init__(self, config_file):
        self.config_file = config_file
        self.config = None
        self.get_config_file()

    def getConfigFile(self):
        return self.config_file

    def get_gossip_port(self):
        return self.config["port"]

    def get_gossip_host(self):
        return self.config["host"]

    def get_seed_port(self):
        return self.config["seed_port"]

    def get_seed_host(self):
        return self.config["seed_host"]

    def get_config_file(self):
        try:
            with open(self.config_file, 'r') as f:
                self.config = f.read()
            try:
                self.config = json.loads(self.config)
            except Exception as e:
                print(e)
                exit(1)

        except Exception as e:
            print(e)
            exit(1)

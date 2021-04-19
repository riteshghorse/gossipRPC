# done


import json
import os


# __all__ = ["ConfigurationManager"]


class Configuration(object):

    def __init__(self, config_file):
        # print(config_file)
        self._config_file = config_file
        self._config = None
        self._set_config()

    def getConfigFile(self):
        return self._config_file

    def get_gossip_port(self):
        return self._config["port"]

    def get_gossip_host(self):
        return self._config["host"]

    def get_seed_port(self):
        return self._config["seed_port"]

    def get_seed_host(self):
        return self._config["seed_host"]
    
    def get_heart_beat_state(self):
        return self._config["heart_beat_state"]

    def get_app_state(self):
        return self._config["app_state"]
    
    def get_endpoint_state(self):
        return self._config["endpoint_state"]

    def _set_config(self):

        try:
            with open(self._config_file, 'r') as f:
                self._config = f.read()

            try:
                self._config = json.loads(self._config)
            except json.JSONDecodeError:
                print("Configuration file provided not in JSON format.")
                exit(1)

        except FileNotFoundError:
            print("Configuration file provided not found.")
            exit(1)


class ConfigurationManager:

    configuration = None

    @staticmethod
    def get_configuration():

        if not ConfigurationManager.configuration:
            ConfigurationManager.configuration = \
                Configuration(os.environ["GOSSIP_CONFIG"])

        return ConfigurationManager.configuration

    @staticmethod
    def reset_configuration():
        ConfigurationManager.configuration = None
        ConfigurationManager.get_configuration()
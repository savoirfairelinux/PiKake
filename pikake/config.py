import json
import os


def save_config(dir, config):
    # Save the new config to file
    with open(os.path.join(dir, 'config.json'), 'w') as f:
        json.dump(config, f)


def load_config(dir):
    with open(os.path.join(dir, 'config.json'), 'rb') as fp:
        cfg = json.load(fp)
        return cfg

import argparse
import os
import pathlib
import logging
from . import brapi

parser = argparse.ArgumentParser(description="Start a BRAPI server instance that functions as a proxy for endpoints from existing BRAPI services.")
parser.add_argument("--config", type=str, nargs="?",
                    help="alternative location of configuration file")
parser.add_argument("--demo", action="store_true",
                    help="start a demonstration service from a configuration based on the BrAPI Test Server")
args = parser.parse_args()

logging.basicConfig(format="%(asctime)s | %(name)s |  %(levelname)s: %(message)s",
                    datefmt="%m-%d-%y %H:%M:%S")
logging.getLogger("brapi.server").setLevel(logging.DEBUG)
logging.getLogger("brapi.handler").setLevel(logging.DEBUG)

def service():
    if args.demo:
        location = os.path.join(os.path.dirname(os.path.abspath(__file__)),"config_demo.ini")
    elif args.config:
        location = os.path.abspath(args.config)
    else:
        location = pathlib.Path().absolute()
    if os.path.exists(location):
        if os.path.isfile(location):
            config_file = os.path.basename(location)
            location = os.path.dirname(location)
        else:
            config_file = "config.ini"
        brapi.BrAPI(location, config_file)
    else:
        raise Exception("couldn't find configuration file at %s" % location)
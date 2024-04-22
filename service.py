import sys,pathlib,logging
from service import brapi

logging.basicConfig(format="%(asctime)s | %(name)s |  %(levelname)s: %(message)s", datefmt="%m-%d-%y %H:%M:%S")
logging.getLogger("brapi.server").setLevel(logging.DEBUG)
logging.getLogger("brapi").setLevel(logging.DEBUG)

location = pathlib.Path().absolute()
brapi.BrAPI(location)
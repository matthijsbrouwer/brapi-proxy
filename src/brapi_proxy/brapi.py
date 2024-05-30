# pylint: disable=line-too-long

"""Main BrAPI module"""

import os
import sys
import configparser
import logging
import time
from multiprocessing import Process,get_start_method
from flask import Flask, Blueprint
from flask_restx import Api
from flask_restx.apidoc import apidoc

from waitress import serve

from . import handler
from ._version import __version__
from .core import calls_api_core, ns_api_core
from .phenotyping import calls_api_phenotyping, ns_api_phenotyping
from .genotyping import calls_api_genotyping, ns_api_genotyping
from .germplasm import calls_api_germplasm, ns_api_germplasm

api_list = [(calls_api_core, ns_api_core),
            (calls_api_phenotyping, ns_api_phenotyping),
            (calls_api_genotyping, ns_api_genotyping),
            (calls_api_germplasm, ns_api_germplasm)]

supportedCalls = {}
for api_entry in api_list:
    for supportedCall,value in api_entry[0].items():
        supportedCalls[supportedCall] = value

class BrAPI:
    """Main BrAPI class"""

    def __init__(self,location,config_file="config.ini"):
        #solve reload problem when using spawn method (osx/windows)
        if get_start_method()=="spawn":
            frame = sys._getframe()
            while frame:
                if "__name__" in frame.f_locals.keys():
                    if not frame.f_locals["__name__"]=="__main__":
                        return
                frame = frame.f_back
        self.location = str(location)
        #set logging
        self.logger = logging.getLogger("brapi.server")
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(self.location,config_file))
        self.logger.info("read configuration file")
        if self.config.getboolean("brapi","debug",fallback=False):
            self.logger.setLevel(logging.DEBUG)
            self.logger.debug("run in debug mode")
        else:
            self.logger.setLevel(logging.INFO)
        self.version = self.config.get("brapi","version",fallback=__version__)
        #restart on errors
        while True:
            try:
                process_api = Process(target=self.process_api_messages, args=[])
                self.logger.debug("try to start server")
                process_api.start()
                #wait until ends
                process_api.join()
            except Exception as e:
                self.logger.error("error: %s",str(e))
            break

    def process_api_messages(self):
        """
        Processing the API messages, implement BrAPI
        """
        #--- initialize Flask application ---
        app = Flask(__name__, static_url_path="/static",
                    static_folder=os.path.join(self.location,"static"),
                    template_folder=os.path.join(self.location,"templates"))
        app.config["location"] = self.location
        #blueprint
        server_location = self.config.get("brapi","location", fallback="/")
        blueprint = Blueprint("brapi", __name__, url_prefix=server_location)
        authorizations = {
            "apikey": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization"
            }
        }
        api_title = self.config.get("serverinfo","serverName",fallback="BrAPI")
        api_description = self.config.get("serverinfo","serverDescription",fallback="The Breeding API")
        api = Api(blueprint, title=api_title,
                  authorizations=authorizations, security="apikey",
                  description=api_description, version=self.version)
        #config
        apidoc.static_url_path = os.path.join(server_location,"swaggerui")
        api.config = self.config
        api.brapi = {
            "servers": {},
            "calls": {"serverinfo": {
                "resources": supportedCalls["serverinfo"].get("resources",[]),
                "acceptedVersions": supportedCalls["serverinfo"].get("acceptedVersions",[]),
                "additionalVersions": supportedCalls["serverinfo"].get("acceptedVersions",[]),
                "servers":{}
            }},
            "authorization": {},
            "identifiers": {call : value.get("identifier",None) for call,value in supportedCalls.items()}
        }
        #check serverinfo
        assert "serverinfo" in supportedCalls, "serverinfo should be supported"
        #get configuration
        if self.config.has_section("authorization"):
            for option in self.config.options("authorization"):
                api.brapi["authorization"][option] = str(self.config.get("authorization",option))
        servers = [entry[7:] for entry in self.config.sections()
                   if entry.startswith("server.") and len(entry)>7]
        for server_name in servers:
            server_section="server.{}".format(server_name)
            if self.config.has_option(server_section,"url"):
                api.brapi["servers"][server_name] = {}
                api.brapi["servers"][server_name]["url"] = self.config.get(server_section,"url")
                api.brapi["servers"][server_name]["authorization"] = None
                api.brapi["servers"][server_name]["name"] = server_name
                api.brapi["servers"][server_name]["calls"] = {}
                api.brapi["servers"][server_name]["prefixes"] = {}
                for key in self.config.options(server_section):
                    if key=="authorization":
                        api.brapi["servers"][server_name][key] = self.config.get(server_section,key)
                    elif key.startswith("prefix."):
                        api.brapi["servers"][server_name]["prefixes"][key[7:]] = str(
                            self.config.get(server_section,key))
                serverinfo,_,_ = handler.brapiGetRequest(
                    api.brapi["servers"][server_name],"serverinfo")
                if not serverinfo:
                    self.logger.error("server %s unreachable",server_name)
                    time.sleep(60)
                    raise ConnectionError("retry because server {} unreachable".format(server_name))
                #get serverinfo versions
                server_calls = serverinfo.get("result",{}).get("calls",[])
                serverinfo_versions = []
                for server_call in server_calls:
                    if server_call.get("service")=="serverinfo":
                        serverinfo_versions.extend(server_call.get("versions",[]))
                if len(set(supportedCalls["serverinfo"].get("acceptedVersions",[])).intersection(serverinfo_versions))==0:
                    self.logger.warning("call serverinfo not supported by %s with right version",call,server_name)
                if self.config.has_option(server_section,"calls"):
                    #get available method/services with the right version and contentType
                    availableServerCalls = set()
                    availableServerCallVersions = {}
                    for server_call in server_calls:
                        if (
                            ("application/json" in server_call.get("contentTypes",[])
                            or
                            "application/json" in server_call.get("dataTypes",[]))
                        ) :
                            for method in server_call.get("methods",[]):
                                method_service = (str(method).lower(),server_call.get("service"))
                                availableServerCalls.add(method_service)
                                availableServerCallVersions[method_service] = server_call.get("versions",[])
                    #get configured calls
                    calls = set()
                    for callEntry in self.config.get(server_section,"calls").split(","):
                        if callEntry=="*":
                            for call,call_value in supportedCalls.items():
                                if availableServerCalls.issuperset(call_value.get("requiredServices",[])):
                                    calls.add(call)
                        elif callEntry.endswith(".*"):
                            namespace = callEntry[:-2]
                            for call,call_value in supportedCalls.items():
                                if not call_value.get("namespace",None)==namespace:
                                    continue
                                if availableServerCalls.issuperset(call_value.get("requiredServices",[])):
                                    calls.add(call)
                        else:
                            calls.add(callEntry)
                    #try to add configured calls
                    for call in calls:
                        if not call in supportedCalls:
                            self.logger.warning(
                                "call %s for %s not supported by proxy",call,server_name)
                        else:
                            requiredServices = supportedCalls[call].get("requiredServices",[])
                            if not availableServerCalls.issuperset(requiredServices):
                                self.logger.warning(
                                    "call %s not supported by %s",call,server_name)
                                continue
                            if len(requiredServices)>0:
                                versions = set.intersection(*[set(availableServerCallVersions[method_service])
                                                              for method_service in requiredServices])
                                if len(set(supportedCalls[call].get("acceptedVersions",[])).intersection(versions))==0:
                                    self.logger.warning(
                                        "call %s not supported by %s with right version",call,server_name)
                                    continue
                            #register call
                            if not call in api.brapi["calls"]:
                                api.brapi["calls"][call] = {
                                    "resources": supportedCalls[call].get("resources",[]),
                                    "acceptedVersions": supportedCalls[call].get("acceptedVersions",[]),
                                    "additionalVersions": supportedCalls[call].get("acceptedVersions",[]),
                                    "servers":{}
                                }
                            if not server_name in api.brapi["calls"][call]["servers"]:
                                api.brapi["calls"][call]["servers"][server_name] = []
                            if not call in api.brapi["servers"][server_name]["calls"]:
                                api.brapi["servers"][server_name]["calls"][call] = []
                            for entry in availableServerCalls:
                                if (entry in supportedCalls[call].get("requiredServices",[]) or
                                    entry in supportedCalls[call].get("optionalServices",[])):
                                    api.brapi["calls"][call]["servers"][server_name].append(entry)
                                    api.brapi["servers"][server_name]["calls"][call].append(entry)

                self.logger.debug("%s: checked serverinfo, supported versions: %s",server_name,", ".join(serverinfo_versions))
                self.logger.debug("%s: calls: %s",server_name,", ".join(api.brapi["servers"][server_name]["calls"].keys()))


        #add namespaces
        for api_entry in api_list:
            api_calls = set(api_entry[0].keys()).intersection(api.brapi["calls"])
            if len(api_calls)>0:
                api.add_namespace(api_entry[1])
                for call in api_calls:
                    for resource in api_entry[0][call].get("resources",[]):
                        api_entry[1].add_resource(resource[0], resource[1])

        #register blueprint
        app.register_blueprint(blueprint)
        app.config.SWAGGER_UI_DOC_EXPANSION = "list"

        #--- start webserver ---
        server_host = self.config.get("brapi","host", fallback="0.0.0.0")
        server_port = self.config.get("brapi","port", fallback="8080")
        server_threads = self.config.get("brapi","threads", fallback="4")
        self.logger.info("start server on host %s and port %s with %s threads",
            server_host,server_port,server_threads)
        serve(app, host=server_host, port=server_port, threads=server_threads)

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
from .core import calls_api_core, ns_api_core
from .genotyping import calls_api_genotyping, ns_api_genotyping

supportedCalls = {}
for key,value in calls_api_core.items(): supportedCalls[key] = (value[0],value[1],value[2])
for key,value in calls_api_genotyping.items(): supportedCalls[key] = (value[0],value[1],value[2])

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
        self.version = self.config.get("brapi","version",fallback="2.1")
        assert self.version in ["2.1"], "version {} not supported".format(self.version)
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
        api_title = self.config.get("brapi","serverName",fallback="BrAPI")
        api_description = self.config.get("brapi","serverDescription",fallback="The Breeding API")
        api = Api(blueprint, title=api_title,
                  authorizations=authorizations, security="apikey",
                  description=api_description, version=self.version)
        #config
        apidoc.static_url_path = os.path.join(server_location,"swaggerui")
        api.config = self.config
        api.brapi = {
            "servers": {},
            "calls": {"serverinfo":{}},
            "authorization": {},
            "identifiers": {call : value[0] for call,value in supportedCalls.items()},
            "version": self.version
        }
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
                api.brapi["servers"][server_name]["name"] = server_name
                api.brapi["servers"][server_name]["calls"] = []
                api.brapi["servers"][server_name]["prefixes"] = {}
                for key in self.config.options(server_section):
                    if key.startswith("prefix."):
                        api.brapi["servers"][server_name]["prefixes"][key[7:]] = str(
                            self.config.get(server_section,key))
                serverinfo,_,_ = handler.brapiGetRequest(
                    api.brapi["servers"][server_name],"serverinfo")
                if not serverinfo:
                    self.logger.error("server %s unreachable",server_name)
                    time.sleep(60)
                    raise ConnectionError("retry because server {} unreachable".format(server_name))
                if self.config.has_option(server_section,"calls"):
                    calls = self.config.get(server_section,"calls").split(",")
                    server_calls = serverinfo.get("result",{}).get("calls",[])
                    #get available method/services with the right version and contentType
                    availableServerCalls = set()
                    for server_call in server_calls:
                        if (
                            "application/json" in server_call.get("contentTypes",[])
                            and
                            "application/json" in server_call.get("dataTypes",[])
                            and
                            self.version in server_call.get("versions",[])
                        ) :
                            for method in server_call.get("methods",[]):
                                availableServerCalls.add((str(method).lower(),server_call.get("service")))
                    for call in calls:
                        if not call in supportedCalls:
                            self.logger.warning(
                                "call %s for %s not supported by proxy",call,server_name)
                        elif not availableServerCalls.issuperset(supportedCalls[call][1]):
                            self.logger.warning(
                                "call %s not supported by %s",call,server_name)
                        else:
                            if not call in api.brapi["calls"]:
                                api.brapi["calls"][call] = {}
                            if not server_name in api.brapi["calls"][call]:
                                api.brapi["calls"][call][server_name] = []
                            for server_call in server_calls:
                                for method in server_call["methods"]:
                                    callKey = (method.lower(),server_call["service"])
                                    if callKey in supportedCalls[call][1] or callKey in supportedCalls[call][2]:
                                        for method in server_call.get("methods"):
                                            entry = (method.lower(),server_call.get("service"))
                                            if entry in supportedCalls[call][1] or entry in supportedCalls[call][2]:
                                                api.brapi["calls"][call][server_name].append(entry)
                self.logger.debug("checked configuration server %s",server_name)
        
        #always provide core namespace
        api.add_namespace(ns_api_core)
        core_calls = set(calls_api_core.keys()).intersection(api.brapi["calls"])
        core_calls.add("serverinfo")
        for call in core_calls:
            for resource in calls_api_core[call][3]:
                servers = list(api.brapi["calls"][call].keys())
                if len(servers)>0:
                    shared = set.intersection(*[set([tuple(entry) for entry in item]) for item in api.brapi["calls"][call].values()])
                else:
                    shared = set()
                methods = resource[0]._methods(shared,servers) if callable(getattr(resource[0], "_methods", None)) else ["get"]
                ns_api_core.add_resource(resource[0], resource[1], methods=methods)
        #genotyping namespace
        genotyping_calls = set(calls_api_genotyping.keys()).intersection(api.brapi["calls"])
        if len(genotyping_calls)>0:
            api.add_namespace(ns_api_genotyping)
            for call in genotyping_calls:
                servers = list(api.brapi["calls"][call].keys())
                shared = set.intersection(*[set([tuple(entry) for entry in item]) for item in api.brapi["calls"][call].values()])
                if len(servers)>0:
                    shared = set.intersection(*[set([tuple(entry) for entry in item]) for item in api.brapi["calls"][call].values()])
                else:
                    shared = set()
                for resource in calls_api_genotyping[call][3]:
                    methods = resource[0]._methods(shared,servers) if callable(getattr(resource[0], "_methods", None)) else ["get"]
                    ns_api_genotyping.add_resource(resource[0], resource[1], methods=methods)
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

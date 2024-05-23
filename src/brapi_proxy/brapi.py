"""Main BrAPI module"""

import os
import sys
import configparser
import logging
import time
from multiprocessing import Process,get_start_method
from flask import Flask, Blueprint
from flask_restx import Api
from waitress import serve

from . import handler
from .core import calls_api_core, ns_api_core
from .genotyping import calls_api_genotyping, ns_api_genotyping

supportedCalls = list(calls_api_core.keys()) + list(calls_api_genotyping.keys())

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
        blueprint = Blueprint("brapi", __name__, url_prefix="/")
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
        api.config = self.config
        api.brapi = {
            "namespaces": {},
            "servers": {},
            "calls": {},
            "authorization": {},
            "supportedCalls": supportedCalls,
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
                serverinfo,_,_ = handler.brapiRequest(
                    api.brapi["servers"][server_name],"serverinfo")
                if not serverinfo:
                    self.logger.error("server %s unreachable",server_name)
                    time.sleep(60)
                    raise ConnectionError("retry because server {} unreachable".format(server_name))
                if self.config.has_option(server_section,"calls"):
                    calls = self.config.get(server_section,"calls").split(",")
                    server_calls = serverinfo.get("result",{}).get("calls",[])
                    for call in calls:
                        if not call in supportedCalls:
                            self.logger.warning(
                                "call %s for %s not supported by proxy",call,server_name)
                        else:
                            call_found_for_server = False
                            for server_call in server_calls:
                                if call==server_call["service"]:
                                    api.brapi["servers"][server_name]["calls"].append(call)
                                    if not call in api.brapi["calls"]:
                                        api.brapi["calls"][call] = []
                                    if not "application/json" in server_call.get(
                                        "contentTypes",[]):
                                        self.logger.error(
                                            "contentType application/json not supported "+
                                            "for %s by %s",call,server_name)
                                    elif not "application/json" in server_call.get(
                                        "dataTypes",[]):
                                        self.logger.error(
                                            "dataType application/json not supported "+
                                            "for %s by %s",call,server_name)
                                    elif not self.version in server_call.get(
                                        "versions",[]):
                                        self.logger.error(
                                            "version %s not supported "+
                                            "for %s by %s",self.version,call,server_name)
                                    else:
                                        api.brapi["calls"][call].append(
                                            {"server": server_name, "info": server_call})
                                        call_found_for_server = True
                            #continue but log error if call not found
                            if not call_found_for_server:
                                self.logger.error("call %s for %s not available",
                                                  call,server_name)
                self.logger.debug("checked configuration server %s",server_name)
        #always provide core namespace
        api.add_namespace(ns_api_core)
        core_calls = set(calls_api_core.keys()).intersection(api.brapi["calls"])
        core_calls.add("serverinfo")
        for call in core_calls:
            for resource in calls_api_core[call]:
                ns_api_core.add_resource(resource[0], resource[1])
        #genotyping namespace
        genotyping_calls = set(calls_api_genotyping.keys()).intersection(api.brapi["calls"])
        if len(genotyping_calls)>0:
            api.add_namespace(ns_api_genotyping)
            for call in genotyping_calls:
                for resource in calls_api_genotyping[call]:
                    ns_api_genotyping.add_resource(resource[0], resource[1])
        #register blueprint
        app.register_blueprint(blueprint)
        app.config.SWAGGER_UI_DOC_EXPANSION = "list"

        #--- start webserver ---
        server_host = self.config.get("brapi","host", fallback="::")
        server_port = self.config.get("brapi","port", fallback="8080")
        server_threads = self.config.get("brapi","threads", fallback="4")
        self.logger.info("start server on host %s and port %s with %s threads",
            server_host,server_port,server_threads)
        serve(app, host=server_host, port=server_port, threads=server_threads)

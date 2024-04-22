import os,sys,configparser,logging,requests, math, time
from multiprocessing import Process,get_start_method
from flask import Flask, Blueprint, Response, render_template, current_app, g, request
from flask_restx import Api, Resource
from waitress import serve
from functools import wraps

def authorization(brapiCall):
    @wraps(brapiCall)
    def decorated(*args, **kwargs):
        authorization = args[0].api.brapi.get("authorization",{})
        if len(authorization)>0:
            token = request.headers.get("authorization")
            if not (token and (token[:7].lower() == "bearer ")):
                response = Response("bearer token authorization required", mimetype="content/text")
                response.status_code = 403
                return response
            else:
                token = token[7:]
                if not token in authorization.values():
                    response = Response("unauthorized", mimetype="content/text")
                    response.status_code = 401
                    return response
        return brapiCall(*args, **kwargs)
    return decorated

from service.core import *
from service.genotyping import *

supportedCalls = list(calls_api_core.keys()) + list(calls_api_genotyping.keys())

logger = logging.getLogger("brapi")

class BrAPI:
    
    def __init__(self, location, configFile="config.ini"):
                                
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
        self.config.read(os.path.join(self.location,configFile)) 
        
        self.logger.info("read configuration file") 
        if self.config.getboolean("brapi","debug"):
            self.logger.info("run in debug mode") 
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
            
        self.version = self.config["brapi"].get("version",None)
        assert self.version in ["2.1"], "version {} not supported".format(self.version)
        
        #restart on errors
        while True:
            try:
                process_api = Process(target=self.process_api_messages, args=[])
                self.logger.info("start server on port {:s}".format(
                    self.config["brapi"].get("port","8080")))
                process_api.start()
                #wait until ends  
                process_api.join()
            except Exception as e:  
                self.logger.error("error: "+ str(e))  
                
                
    def process_api_messages(self):    
        
        #--- initialize Flask application ---  
        #os.environ["WERKZEUG_RUN_MAIN"] = "true"
        app = Flask(__name__, static_url_path="/static", 
                    static_folder=os.path.join(self.location,"static"), 
                    template_folder=os.path.join(self.location,"templates")) 
        app.config["location"] = self.location
                
        #blueprint     
        blueprint = Blueprint("brapi", __name__, url_prefix="/")
        authorizations = {
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization'
            }
        }
        api = Api(blueprint, title="BrAPI", 
                  authorizations=authorizations, security='apikey',
                  description="The Breeding API", version=self.version)
                
        #config
        api.config = self.config
        
        api.brapi = {
            "namespaces": {},
            "servers": {},
            "calls": {},
            "authorization": {}
        }
        
        #get configuration
        if self.config.has_section("authorization"):
            for option in self.config.options("authorization"):
                api.brapi["authorization"][option] = str(self.config.get("authorization",option))
        
        servers = [entry[7:] for entry in self.config.sections() if entry.startswith("server.") and len(entry)>7]
        for serverName in servers:
            serverSection="server.{}".format(serverName)
            if self.config.has_option(serverSection,"url"):
                api.brapi["servers"][serverName] = {}
                api.brapi["servers"][serverName]["url"] = self.config.get(serverSection,"url")
                api.brapi["servers"][serverName]["name"] = serverName
                api.brapi["servers"][serverName]["calls"] = []
                api.brapi["servers"][serverName]["prefixes"] = {}
                for key in self.config.options(serverSection):
                    if key.startswith("prefix."):
                        api.brapi["servers"][serverName]["prefixes"][key[7:]] = str(self.config.get(serverSection,key))
                serverinfo,_,_ = BrAPI._brapiRequest(api.brapi["servers"][serverName],"serverinfo")
                if not serverinfo:
                    self.logger.error("server {} unreachable".format(serverName))
                    time.sleep(60)
                    raise Exception("retry because server {} unreachable".format(serverName))
                else:
                    if self.config.has_option(serverSection,"calls"):
                        calls = self.config.get(serverSection,"calls").split(",")
                        serverCalls = serverinfo.get("result",{}).get("calls",[])
                        for call in calls:
                            if not call in supportedCalls:
                                self.logger.warning("call {} for {} not supported by proxy".format(call,serverName))
                            else:
                                callFoundForServer = False
                                for serverCall in serverCalls:
                                    if call==serverCall["service"]:
                                        api.brapi["servers"][serverName]["calls"].append(call)
                                        if not call in api.brapi["calls"]:
                                            api.brapi["calls"][call] = []
                                        if not "application/json" in serverCall.get("contentTypes",[]):
                                            self.logger.error(
                                                "contentType application/json not supported for {} by {}".format(
                                                call,serverName))
                                        elif not "application/json" in serverCall.get("dataTypes",[]):
                                            self.logger.error(
                                                "dataType application/json not supported for {} by {}".format(
                                                call,serverName))
                                        elif not self.version in serverCall.get("versions",[]):
                                            self.logger.error(
                                                "version {} not supported for {} by {}".format(
                                                self.version,call,serverName))
                                        else:
                                            api.brapi["calls"][call].append(
                                                {"server": serverName, "info": serverCall})
                                            callFoundForServer = True
                                #continue but log error if call not found
                                if not callFoundForServer:
                                    self.logger.error("call {} for {} not available".format(call,serverName))
                                                
        
        #always provide core namespace
        api.add_namespace(ns_api_core)
        coreCalls = set(calls_api_core.keys()).intersection(api.brapi["calls"])
        coreCalls.add("serverinfo")
        for call in coreCalls:
            for resource in calls_api_core[call]:
                ns_api_core.add_resource(resource[0], resource[1])
        #genotyping namespace
        genotypingCalls = set(calls_api_genotyping.keys()).intersection(api.brapi["calls"])
        if len(genotypingCalls)>0:
            api.add_namespace(ns_api_genotyping)
            for call in genotypingCalls:
                for resource in calls_api_genotyping[call]:
                    ns_api_genotyping.add_resource(resource[0], resource[1])
                    
        #register blueprint       
        app.register_blueprint(blueprint) 
        app.config.SWAGGER_UI_DOC_EXPANSION = "list"

        #--- start webserver ---
        serve(app, 
              host=self.config["brapi"].get("host", "::"), 
              port=self.config["brapi"].get("port", "8080"), 
              threads=self.config["brapi"].get("threads", "10"))         
        
    def _prefixDataEntry(data,prefixes):
        for key,value in prefixes.items():
            if value and key in supportedCalls:
                if key.endswith("ies"):
                    idKey = "{}yDbId".format(key[:-3])
                else:
                    idKey = "{}DbId".format(key[:-1])
                if idKey in data and not data[idKey] is None:
                    if isinstance(data[idKey],str):
                        data[idKey] = "{}{}".format(value,data[idKey])
                if key.endswith("ies"):
                    idsKey = "{}yDbIds".format(key[:-3])
                else:
                    idsKey = "{}DbIds".format(key[:-1])
                if idsKey in data and not data[idsKey] is None:
                    if isinstance(data[idsKey],str):
                        data[idsKey] = "{}{}".format(value,data[idsKey])
                    elif isinstance(data[idsKey],list):
                        data[idsKey] = ["{}{}".format(value,entry) for entry in data[idsKey]]
        return data
    
    def _prefixRewriteParams(params,prefixes):
        newParams = params.copy()
        for key,value in prefixes.items():
            if value and key in supportedCalls:
                if key.endswith("ies"):
                    idKey = "{}yDbId".format(key[:-3])
                else:
                    idKey = "{}DbId".format(key[:-1])
                if idKey in newParams and not newParams[idKey] is None:
                    if isinstance(newParams[idKey],str):
                        if newParams[idKey].startswith(value):
                            newParams[idKey] = newParams[idKey][len(value):]
                        else:
                            return None
        return newParams
    
    def _brapiResponse(result):
        response = {}
        response["@context"] = ["https://brapi.org/jsonld/context/metadata.jsonld"]
        response["metadata"] = {}
        response["result"] = result
        return response

    def _brapiRequest(server,call,method="get",**args):
        try:
            if method=="get":
                params = args.get("params",{})
                headers = {"Accept": "application/json"}
                url = "{}/{}".format(server["url"],call)
                response = requests.get(url, params=params, headers=headers)
                try:
                    if response.ok:
                        return response.json(), response.status_code, None
                    else:
                        return None, response.status_code, response.text
                except:
                    return None, 500, response.text
            else:
                return None, 501, "unsupported method {} ".format(method)
        except Exception as e:
            return None, 500, "error: {}".format(str(e))


    def _brapiIdRequestResponse(brapi, call, name, id, method="get", **args):
        #get servers
        servers = []
        for item in brapi["calls"][call]:
            servers.append(brapi["servers"].get(item["server"],{}))
        #handle request
        if method=="get":
            #construct response
            response = {}
            response["@context"] = ["https://brapi.org/jsonld/context/metadata.jsonld"]
            response["metadata"] = {}
            for server in servers:
                try:
                    serverParams = {}
                    serverParams[name] = id
                    serverParams = BrAPI._prefixRewriteParams(serverParams,server["prefixes"])
                    if not serverParams is None:
                        itemResponse,itemStatus,itemError = BrAPI._brapiRequest(server,call,params=serverParams)
                        if itemResponse:
                            try:
                                data = itemResponse.get("result").get("data")
                                data = [BrAPI._prefixDataEntry(entry,server["prefixes"]) for entry in data]
                                if len(data)==1:
                                    if name in data[0]:
                                        if data[0][name]==id:
                                            response["result"] = data[0]
                                            return response, 200, None
                                        else:
                                            logger.warning("unexpected response with {}: {} from {}".format(
                                                name,data[0][name],server["name"]))
                                    else:
                                        logger.warning("unexpected response without {} from {}".format(
                                                name,server["name"]))
                                elif len(data)>1:
                                    logger.warning("unexpected multiple ({}) entries in response from {}".format(
                                                len(data),server["name"]))
                            except:
                                logger.warning("unexpected response from {}".format(server["name"]))
                except Exception as e:
                    return None, 500, "problem processing response from {}: {}".format(server["name"],str(e))
            return None, 404, "{} {} not found in {}".format(name,id,call)
        else:
            return None, 501, "unsupported method {}".format(method)


    def _brapiRepaginateRequestResponse(brapi, call, method="get", **args):
        #get servers
        servers = []
        for item in brapi["calls"][call]:
            servers.append(brapi["servers"].get(item["server"],{}))
        #handle request
        if method=="get":
            params = args.get("params",{})
            page = params.get("page",0)
            pageSize = params.get("pageSize",1000)
            #construct response
            response = {}
            response["@context"] = ["https://brapi.org/jsonld/context/metadata.jsonld"]
            response["metadata"] = {}
            response["metadata"]["pagination"] = {
                "currentPage": page,
                "pageSize": pageSize
            }
            data = []
            totalCount = 0
            start = page*pageSize
            end = ((page+1)*pageSize) - 1
            for server in servers:
                try:
                    subStart = start - totalCount
                    subEnd = end - totalCount
                    serverParams = BrAPI._prefixRewriteParams(params,server["prefixes"])
                    if not serverParams is None:
                        #recompute page and pageSize
                        serverParams["page"] = max(0,math.floor(subStart/pageSize))
                        serverParams["pageSize"] = pageSize
                        #get page
                        itemResponse,itemStatus,itemError = BrAPI._brapiRequest(server,call,params=serverParams)
                        if not itemResponse:
                            return None, 500, "invalid response ({}) from {}: {}".format(
                                itemStatus,server["name"],str(itemError))
                        subTotal = itemResponse.get("metadata",{}).get("pagination",{}).get("totalCount",0)
                        subPage = itemResponse.get("metadata",{}).get("pagination",{}).get("currentPage",0)
                        subPageSize = itemResponse.get("metadata",{}).get("pagination",{}).get("pageSize",1000)
                        subData = itemResponse.get("result",{}).get("data",[])    
                        subData = [BrAPI._prefixDataEntry(entry,server["prefixes"]) for entry in subData]
                        logger.debug("server {} for {} has {} results, get {} on page {} with size {}".format(
                            server["name"], call, subTotal, len(subData), subPage, subPageSize))
                        if not subPage==serverParams["page"]:
                            logger.warning("unexpected page: {} instead of {}".format(
                                subPage,serverParams["page"]))
                        elif not subPageSize==serverParams["pageSize"]:
                            logger.warning("unexpected pageSize: {} instead of {}".format(
                                subPageSize,serverParams["pageSize"]))
                        elif len(subData)>subPageSize:
                            logger.warning("unexpected number of results: {} > {}".format(
                                len(subData),subPageSize))
                        if (subStart<subTotal) and (subEnd>=0):
                            s1 = max(0,subStart-(subPage*subPageSize))
                            s2 = min(subPageSize-1,min(subTotal-1,subEnd)-(subPage*subPageSize))
                            if s2>=s1:
                                subData = subData[s1:s2+1]
                                logger.debug("add {} entries ({} - {}) from {} to {} result".format(
                                    len(subData),s1,s2,server["name"], call))
                                data = data + subData
                                #another page necessary
                                if subEnd>(((subPage+1)*subPageSize)-1):
                                    serverParams["page"]+=1
                                    #get next page
                                    itemResponse = BrAPI._brapiRequest(server,call,params=serverParams)
                                    if not itemResponse:
                                        return None, 500, "invalid response ({}) from {}: {}".format(
                                            itemStatus,server["name"],str(itemError))
                                    subTotal = itemResponse.get("metadata",{}).get("pagination",{}).get("totalCount",0)
                                    subPage = itemResponse.get("metadata",{}).get("pagination",{}).get("currentPage",0)
                                    subPageSize = itemResponse.get("metadata",{}).get("pagination",{}).get("pageSize",1000)
                                    subData = itemResponse.get("result",{}).get("data",[])
                                    logger.debug("server {} for {} has {} results, get {} on page {} with size {}".format(
                                        server["name"], call, subTotal, len(subData), subPage, subPageSize))
                                    if not subPage==serverParams["page"]:
                                        logger.warning("unexpected page: {} instead of {}".format(
                                            subPage,serverParams["page"]))
                                    elif not subPageSize==serverParams["pageSize"]:
                                        logger.warning("unexpected pageSize: {} instead of {}".format(
                                            subPageSize,serverParams["pageSize"]))
                                    elif len(subData)>subPageSize:
                                        logger.warning("unexpected number of results: {} > {}".format(
                                            len(subData),subPageSize))
                                    s1 = max(0,subStart-(subPage*subPageSize))
                                    s2 = min(subPageSize-1,min(subTotal-1,subEnd)-(subPage*subPageSize))
                                    subData = subData[s1:s2+1]
                                    if s2>=s1:
                                        subData = subData[s1:s2+1]
                                        logger.debug("add {} entries ({} - {}) from {} to {} result".format(
                                            len(subData),s1,s2,server["name"], call))
                                        data = data + subData
                        totalCount += subTotal
                except Exception as e:
                    return None, 500, "problem processing response from {}: {}".format(server["name"],str(e))
            logger.debug("result for {} has in total {} entries".format(call,len(data)))
            response["result"] = {"data": data}
            response["metadata"]["pagination"]["totalCount"] = totalCount
            response["metadata"]["pagination"]["totalPages"] = math.ceil(totalCount/pageSize)
            return response, 200, None   
        else:
            return None, 501, "unsupported method {}".format(method)




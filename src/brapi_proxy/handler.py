# pylint: disable=line-too-long

"""Handler BrAPI requests"""

import math
import logging
from functools import wraps
import requests
from flask import Response, request

logger = logging.getLogger("brapi.handler")

def authorization(brapi_call):
    """
    handles authorization all brapi calls
    """
    @wraps(brapi_call)
    def decorated(*args, **kwargs):
        auth = args[0].api.brapi.get("authorization",{})
        if len(auth)>0:
            token = request.headers.get("authorization")
            if not (token and (token[:7].lower() == "bearer ")):
                response = Response("bearer token authorization required", mimetype="content/text")
                response.status_code = 403
                return response
            token = token[7:]
            if not token in auth.values():
                response = Response("unauthorized", mimetype="content/text")
                response.status_code = 401
                return response
        return brapi_call(*args, **kwargs)
    return decorated


def prefixDataEntry(data,prefixes,identifiers):
    for key,value in prefixes.items():
        if value and key in identifiers and not identifiers[key] is None:
            idKey = identifiers[key]
            idsKey = "{}s".format(idKey)
            if idKey in data and not data[idKey] is None:
                if isinstance(data[idKey],str):
                    data[idKey] = "{}{}".format(value,data[idKey])
            if idsKey in data and not data[idsKey] is None:
                if isinstance(data[idsKey],str):
                    data[idsKey] = "{}{}".format(value,data[idsKey])
                elif isinstance(data[idsKey],list):
                    data[idsKey] = ["{}{}".format(value,entry) for entry in data[idsKey]]
    return data

def prefixRewriteParams(params,prefixes,identifiers):
    newParams = params.copy()
    for key,value in prefixes.items():
        if value and key in identifiers and not identifiers[key] is None:
            idKey = identifiers[key]
            if idKey in newParams and not newParams[idKey] is None:
                if isinstance(newParams[idKey],str):
                    if newParams[idKey].startswith(value):
                        newParams[idKey] = newParams[idKey][len(value):]
                    else:
                        return None
    return newParams

def brapiResponse(result, status=[]):
    response = {}
    response["@context"] = ["https://brapi.org/jsonld/context/metadata.jsonld"]
    response["metadata"] = {
        "datafiles": None,
        "status": status,
        "pagination": None
    }
    response["result"] = result
    return response

def brapiGetRequest(server,call,**args): 
    try:
        params = args.get("params",{})
        headers = {"Accept": "application/json"}
        if not server["authorization"] is None:
            headers["Authorization"] = "Bearer {}".format(server["authorization"])
        url = "{}/{}".format(server["url"],call)
        response = requests.get(url, params=params, headers=headers)
        try:
            if response.ok:
                return response.json(), response.status_code, None
            return None, response.status_code, response.text
        except:
            return None, 500, response.text
    except Exception as e:
        return None, 500, "error: {}".format(str(e))

def brapiPostRequest(server,call,payload):
    try:
        headers = {"Accept": "application/json"}
        if not server["authorization"] is None:
            headers["Authorization"] = "Bearer {}".format(server["authorization"])
        url = "{}/{}".format(server["url"],call)
        response = requests.post(url, data=payload, headers=headers)
        try:
            if response.ok:
                return response.json(), response.status_code, None
            return None, response.status_code, response.text
        except:
            return None, 500, response.text
    except Exception as e:
        return None, 500, "error: {}".format(str(e))

def brapiIdRequestResponse(brapi, call, name, id, method="get"):
    #get servers
    servers = []
    for server in brapi["calls"][call]["servers"]:
        servers.append(brapi["servers"].get(server,{}))
    #handle request
    callById="{}/{{{}}}".format(call,name)
    if method=="get":
        #construct response
        response = {}
        response["@context"] = ["https://brapi.org/jsonld/context/metadata.jsonld"]
        response["metadata"] = {
            "datafiles": None,
            "status": [],
            "pagination": None
        }
        for server in servers:
            try:
                serverParams = {}
                serverParams[name] = id
                serverParams = prefixRewriteParams(serverParams,server["prefixes"], brapi["identifiers"])
                if not serverParams is None:
                    if (method, callById) in brapi["calls"][call]["servers"][server["name"]]:
                        serverCall = "{}/{}".format(call,serverParams[name])
                        itemResponse,itemStatus,itemError = brapiGetRequest(server,serverCall)
                        if itemResponse:
                            try:
                                data = itemResponse.get("result")
                                data = prefixDataEntry(data,server["prefixes"],brapi["identifiers"])
                                response["result"] = data
                                return response, 200, None
                            except:
                                logger.warning("unexpected response from {}".format(server["name"]))
                    elif (method, call) in brapi["calls"][call]["servers"][server["name"]]:
                        itemResponse,itemStatus,itemError = brapiGetRequest(
                            server,call,params=serverParams)
                        if itemResponse:
                            try:
                                data = itemResponse.get("result").get("data")
                                data = [prefixDataEntry(
                                    entry,server["prefixes"],
                                    brapi["identifiers"]) for entry in data]
                                if len(data)==1:
                                    if name in data[0]:
                                        if data[0][name]==id:
                                            response["result"] = data[0]
                                            return response, 200, None
                                        logger.warning("unexpected response with "+
                                                        "{}: {} from {}".format(
                                                name,data[0][name],server["name"]))
                                    else:
                                        logger.warning("unexpected response without "+
                                                       "{} from {}".format(
                                                name,server["name"]))
                                elif len(data)>1:
                                    logger.warning("unexpected multiple ({}) ".format(len(data))+
                                                   "entries in response from {}".format(
                                                       server["name"]))
                            except:
                                logger.warning("unexpected response from {}".format(
                                    server["name"]))
            except Exception as e:
                return None, 500, "problem processing response from {}: {}".format(
                    server["name"],str(e))
        return None, 404, "{} {} not found in {}".format(name,id,call)
    else:
        return None, 501, "unsupported method {}".format(method)

def brapiRepaginateRequestResponse(brapi, call, **args):
    #get servers
    servers = []
    for server in brapi["calls"][call]["servers"]:
        servers.append(brapi["servers"].get(server,{}))
    #handle request
    params = args.get("params",{})
    if len(servers)>1:
        unsupported = args.get("unsupportedForMultipleServerResponse",[])
        for key in params:
            if key in unsupported:
                return None, 501, "unsupported parameter {}".format(key)
    #pagination
    page = params.get("page",0)
    pageSize = params.get("pageSize",1000)
    #construct response
    response = {}
    response["@context"] = ["https://brapi.org/jsonld/context/metadata.jsonld"]
    response["metadata"] = {
        "datafiles": None,
        "status": [],
        "pagination": {
            "currentPage": page,
            "pageSize": pageSize
        }
    }
    data = []
    totalCount = 0
    start = page*pageSize
    end = ((page+1)*pageSize) - 1
    for server in servers:
        try:
            subStart = start - totalCount
            subEnd = end - totalCount
            serverParams = prefixRewriteParams(params,server["prefixes"], brapi["identifiers"])
            if not serverParams is None:
                #recompute page and pageSize
                serverParams["page"] = max(0,math.floor(subStart/pageSize))
                serverParams["pageSize"] = pageSize
                #get page
                itemResponse,itemStatus,itemError = brapiGetRequest(
                    server,call,params=serverParams)
                if not itemResponse:
                    return None, 500, "invalid response ({}) from {}: {}".format(
                        itemStatus,server["name"],str(itemError))
                subTotal = itemResponse.get("metadata",{}).get(
                    "pagination",{}).get("totalCount",0)
                subTotalPages = itemResponse.get("metadata",{}).get(
                    "pagination",{}).get("totalPages",0)
                subPage = itemResponse.get("metadata",{}).get(
                    "pagination",{}).get("currentPage",0)
                subPageSize = itemResponse.get("metadata",{}).get(
                    "pagination",{}).get("pageSize",1000)
                subData = itemResponse.get("result",{}).get("data",[])
                subData = [prefixDataEntry(entry,server["prefixes"], brapi["identifiers"])
                           for entry in subData]
                logger.debug("server {} for {} has {} results, ".format(
                    server["name"], call, subTotal)+
                    "get {} on page {} with size {}".format(
                        len(subData), subPage, subPageSize))
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
                        if (subEnd>(((serverParams["page"]+1)*subPageSize)-1)) and (serverParams["page"]+1<subTotalPages):
                            serverParams["page"]+=1
                            #get next page
                            itemResponse,itemStatus,itemError = brapiGetRequest(
                                server,call,params=serverParams)
                            if not itemResponse:
                                return (None, 500,
                                    "invalid response ({}) from {}: {}".format(
                                    itemStatus,server["name"],str(itemError)))
                            subTotal = itemResponse.get("metadata",{}).get(
                                "pagination",{}).get("totalCount",0)
                            subTotalPages = itemResponse.get("metadata",{}).get(
                                "pagination",{}).get("totalPages",0)
                            subPage = itemResponse.get("metadata",{}).get(
                                "pagination",{}).get("currentPage",0)
                            subPageSize = itemResponse.get("metadata",{}).get(
                                "pagination",{}).get("pageSize",1000)
                            subData = itemResponse.get("result",{}).get("data",[])
                            logger.debug("server {} for {} has {} results, ".format(
                                server["name"], call, subTotal)+
                                "get {} on page {} with size {}".format(
                                    len(subData), subPage, subPageSize))
                            if not subPage==serverParams["page"]:
                                logger.warning("unexpected page: {} instead of {}".format(
                                    subPage,serverParams["page"]))
                            elif not subPageSize==serverParams["pageSize"]:
                                logger.warning("unexpected pageSize: {} ".format(
                                    subPageSize)+
                                    "instead of {}".format(serverParams["pageSize"]))
                            elif len(subData)>subPageSize:
                                logger.warning("unexpected number of "+
                                               "results: {} > {}".format(
                                    len(subData),subPageSize))
                            s1 = max(0,subStart-(subPage*subPageSize))
                            s2 = min(subPageSize-1,
                                     min(subTotal-1,subEnd)-(subPage*subPageSize))
                            subData = subData[s1:s2+1]
                            if s2>=s1:
                                subData = subData[s1:s2+1]
                                logger.debug("add {} entries ({} - {}) ".format(
                                    len(subData),s1,s2)+
                                    "from {} to {} result".format(
                                        server["name"], call))
                                #update data
                                data = data + subData
                totalCount += subTotal
        except Exception as e:
            return (None, 500, "problem processing response "+
                    "from {}: {}".format(server["name"],str(e)))
    logger.debug("result for {} has in total {} entries".format(call,len(data)))
    response["result"] = {"data": data}
    response["metadata"]["pagination"]["totalCount"] = totalCount
    response["metadata"]["pagination"]["totalPages"] = math.ceil(totalCount/pageSize)
    return response, 200, None

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


def prefixDataEntry(data,prefixes,supportedCalls):
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

def prefixRewriteParams(params,prefixes,supportedCalls):
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

def brapiResponse(result):
    response = {}
    response["@context"] = ["https://brapi.org/jsonld/context/metadata.jsonld"]
    response["metadata"] = {}
    response["result"] = result
    return response

def brapiRequest(server,call,method="get",**args):
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


def brapiIdRequestResponse(brapi, call, name, id, method="get", **args):
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
                serverParams = prefixRewriteParams(serverParams,server["prefixes"],
                                                   brapi["supportedCalls"])
                if not serverParams is None:
                    itemResponse,itemStatus,itemError = brapiRequest(
                        server,call,params=serverParams)
                    if itemResponse:
                        try:
                            data = itemResponse.get("result").get("data")
                            data = [prefixDataEntry(
                                entry,server["prefixes"],
                                brapi["supportedCalls"]) for entry in data]
                            if len(data)==1:
                                if name in data[0]:
                                    if data[0][name]==id:
                                        response["result"] = data[0]
                                        return response, 200, None
                                    else:
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


def brapiRepaginateRequestResponse(brapi, call, method="get", **args):
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
                serverParams = prefixRewriteParams(params,server["prefixes"],
                                                   brapi["supportedCalls"])
                if not serverParams is None:
                    #recompute page and pageSize
                    serverParams["page"] = max(0,math.floor(subStart/pageSize))
                    serverParams["pageSize"] = pageSize
                    #get page
                    itemResponse,itemStatus,itemError = brapiRequest(
                        server,call,params=serverParams)
                    if not itemResponse:
                        return None, 500, "invalid response ({}) from {}: {}".format(
                            itemStatus,server["name"],str(itemError))
                    subTotal = itemResponse.get("metadata",{}).get(
                        "pagination",{}).get("totalCount",0)
                    subPage = itemResponse.get("metadata",{}).get(
                        "pagination",{}).get("currentPage",0)
                    subPageSize = itemResponse.get("metadata",{}).get(
                        "pagination",{}).get("pageSize",1000)
                    subData = itemResponse.get("result",{}).get("data",[])
                    subData = [prefixDataEntry(entry,server["prefixes"],
                                               brapi["supportedCalls"])
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
                            if subEnd>(((subPage+1)*subPageSize)-1):
                                serverParams["page"]+=1
                                #get next page
                                itemResponse = brapiRequest(
                                    server,call,params=serverParams)
                                if not itemResponse:
                                    return (None, 500,
                                        "invalid response ({}) from {}: {}".format(
                                        itemStatus,server["name"],str(itemError)))
                                subTotal = itemResponse.get("metadata",{}).get(
                                    "pagination",{}).get("totalCount",0)
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
    else:
        return None, 501, "unsupported method {}".format(method)

import json
import math
import logging
from .. import handler
from . import ns_api_genotyping as namespace
from flask import Response
from flask_restx import Resource

parser = namespace.parser()
parser.add_argument("dimensionVariantPage", type=int, required=False, 
        help="The requested page number for the Variant dimension of the matrix")
parser.add_argument("dimensionVariantPageSize", type=int, required=False,
        help="The requested page size for the Variant dimension of the matrix")
parser.add_argument("dimensionCallSetPage", type=int, required=False, 
        help="The requested page number for the CallSet dimension of the matrix")
parser.add_argument("dimensionCallSetPageSize", type=int, required=False,
        help="The requested page size for the CallSet dimension of the matrix")
parser.add_argument("preview", type=bool, required=False,
        help="Default Value = false\n<br/>If 'preview' is set to true, then the server should return with the \"dataMatrices\" field as null or empty. All other data fields should be returned normally. \nThis is intended to be a preview and give the client a sense of how large the matrix returned will be\n<br/>If 'preview' is set to false or not set (default), then the server should return all the matrix data as requested.")
parser.add_argument("dataMatrixNames", type=str, required=False,
        help="\"dataMatrixNames\" is a comma seperated list of names (ie ''Genotype, Read Depth'' etc). This list controls which data matrices are returned in the response.<br> This maps to a FORMAT field in the VCF file standard.")
parser.add_argument("dataMatrixAbbreviations", type=str, required=False,
        help="\"dataMatrixAbbreviations\" is a comma seperated list of abbreviations (ie ''GT, RD'' etc). This list controls which data matrices are returned in the response.<br> This maps to a FORMAT field in the VCF file standard.")
parser.add_argument("positionRange", type=str, required=False,
        help="The postion range to search\n<br/> Uses the format \"contig:start-end\" where \"contig\" is the chromosome or contig name, \"start\" is  \nthe starting position of the range, and \"end\" is the ending position of the range\n<br> Example: CHROM_1:12000-14000")
parser.add_argument("germplasmDbId", type=str, required=False,
        help="Use this parameter to only return results associated with the given `Germplasm` unique identifier. \n<br/>Use `GET /germplasm` to find the list of available `Germplasm` on a server.")
parser.add_argument("germplasmName", type=str, required=False,
        help="Use this parameter to only return results associated with the given `Germplasm` by its human readable name. \n<br/>Use `GET /germplasm` to find the list of available `Germplasm` on a server.")
parser.add_argument("germplasmPUI", type=str, required=False,
        help="Use this parameter to only return results associated with the given `Germplasm` by its global permanent unique identifier. \n<br/>Use `GET /germplasm` to find the list of available `Germplasm` on a server.")
parser.add_argument("callSetDbId", type=str, required=False,
        help="The ID which uniquely identifies a `CallSet` within the given database server")
parser.add_argument("variantDbId", type=str, required=False,
        help="The ID which uniquely identifies a `Variant` within the given database")
parser.add_argument("variantSetDbId", type=str, required=False,
        help="The ID which uniquely identifies a `VariantSet` within the given database")
parser.add_argument("expandHomozygotes", type=bool, required=False,
        help="Should homozygotes be expanded (true) or collapsed into a single occurrence (false)")
parser.add_argument("unknownString", type=str, required=False,
        help="The string to use as a representation for missing data")
parser.add_argument("sepPhased", type=str, required=False,
        help="The string to use as a separator for phased allele calls")
parser.add_argument("sepUnphased", type=str, required=False,
        help="The string to use as a separator for unphased allele calls")
parser.add_argument("Authorization", type=str, required=False,
        help="HTTP HEADER - Token used for Authorization<br>**Bearer {token_string}**", 
        location="headers")

class GenotypingAllelematrix(Resource):

    @namespace.expect(parser, validate=True)
    @handler.authorization
    def get(self):
        strict = self.api.config.getboolean("brapi","strict") if self.api.config.has_option("brapi","strict") else False
        args = parser.parse_args(strict=strict)
        try:
            #get parameters
            dimensionVariantPage = (int(args["dimensionVariantPage"]) 
                                    if not args["dimensionVariantPage"] is None else 0)
            dimensionVariantPageSize = (int(args["dimensionVariantPageSize"]) 
                                        if not args["dimensionVariantPageSize"] is None else 100)
            dimensionCallSetPage = (int(args["dimensionCallSetPage"]) 
                                    if not args["dimensionCallSetPage"] is None else 0)
            dimensionCallSetPageSize = (int(args["dimensionCallSetPageSize"]) 
                                        if not args["dimensionCallSetPageSize"] is None else 100)
            args["preview"] = args["preview"] if not args["preview"] is None else False
            args["expandHomozygotes"] = args["expandHomozygotes"] if not args["expandHomozygotes"] is None else True
            args["unknownString"] = args["unknownString"] if not args["unknownString"] is None else "."
            args["sepPhased"] = args["sepPhased"] if not args["sepPhased"] is None else "|"
            args["sepUnphased"] = args["sepUnphased"] if not args["sepUnphased"] is None else "/"
            params = {"dimensionVariantPage": dimensionVariantPage, 
                      "dimensionVariantPageSize": dimensionVariantPageSize,
                      "dimensionCallSetPage": dimensionCallSetPage,
                      "dimensionCallSetPageSize": dimensionCallSetPageSize}
            for key,value in args.items():
                if not key in ["dimensionVariantPage","dimensionVariantPageSize",
                               "dimensionCallSetPage","dimensionCallSetPageSize","Authorization"]:
                    if not value is None:
                        params[key] = value
            brapiResponse,brapiStatus,brapiError = _brapiRepaginateAllelematrixRequestResponse(
                self.api.brapi, params)
            if brapiResponse:
                return Response(json.dumps(brapiResponse), mimetype="application/json")
            response = Response(json.dumps(str(brapiError)), mimetype="application/json")
            response.status_code = brapiStatus
            return response
        except Exception as e:
            response = Response(json.dumps(str(e)), mimetype="application/json")
            response.status_code = 500
            return response
        
        
logger = logging.getLogger("brapi.handler")

def _brapiRepaginateAllelematrixServerRequest(server, serverParams, identifiers,
                                                subStartVariants, subEndVariants, 
                                                subStartCallSets, subEndCallSets):
    additionalVariantsRequest = False
    additionalCallSetsRequest = False
    #get page
    itemResponse,itemStatus,itemError = handler.brapiGetRequest(server,"allelematrix",params=serverParams)
    if not itemResponse:
        return None, 500, "invalid response ({}) from {}: {}".format(
            itemStatus,server["name"],str(itemError))
    subVariantsTotal = 0
    subVariantsPage = 0
    subVariantsPageSize = serverParams["dimensionVariantPageSize"]
    subCallSetsTotal = 0
    subCallSetsPage = 0
    subCallSetsPageSize = serverParams["dimensionCallSetPageSize"]
    for entry in itemResponse.get("result",{}).get("pagination",[]):
        if entry.get("dimension","")=="VARIANTS":
            subVariantsTotal = int(entry.get("totalCount",subVariantsTotal))
            subVariantsPage = int(entry.get("page",subVariantsPage))
            subVariantsPageSize = int(entry.get("pageSize",subVariantsPageSize))
        elif entry.get("dimension","")=="CALLSETS":
            subCallSetsTotal = int(entry.get("totalCount",subCallSetsTotal))
            subCallSetsPage = int(entry.get("page",subCallSetsPage))
            subCallSetsPageSize = int(entry.get("pageSize",subCallSetsPageSize))
    subVariantDbIds = itemResponse.get("result",{}).get("variantDbIds",[]) 
    subVariantDbIds = handler.prefixDataEntry({"variantDbIds": subVariantDbIds},
                                   server["prefixes"],identifiers)["variantDbIds"]
    subVariantSetDbIds = itemResponse.get("result",{}).get("variantSetDbIds",[])
    subVariantSetDbIds = [] if not subVariantSetDbIds else subVariantSetDbIds
    subVariantSetDbIds = handler.prefixDataEntry({"variantSetDbIds": subVariantSetDbIds},
                                   server["prefixes"],identifiers)["variantSetDbIds"]
    subCallSetDbIds = itemResponse.get("result",{}).get("callSetDbIds",[])
    subCallSetDbIds = handler.prefixDataEntry({"callSetDbIds": subCallSetDbIds},
                                   server["prefixes"],identifiers)["callSetDbIds"]
    subDataMatrices = itemResponse.get("result",{}).get("dataMatrices",[]) 
    #check variants
    logger.debug("server {} for allematrix has {} variants, get {} on page {} with size {}".format(
                server["name"], subVariantsTotal, len(subVariantDbIds), 
        subVariantsPage, subVariantsPageSize))
    if not subVariantsPage==serverParams["dimensionVariantPage"]:
        logger.warning("unexpected variants page: {} instead of {}".format(
            subVariantsPage,serverParams["dimensionVariantPage"]))
    elif not subVariantsPageSize==serverParams["dimensionVariantPageSize"]:
        logger.warning("unexpected variants pageSize: {} instead of {}".format(
            subVariantsPageSize,serverParams["dimensionVariantPageSize"]))
    elif len(subVariantDbIds)>subVariantsPageSize:
        logger.warning("unexpected number of variants: {} > {}".format(
            len(subVariantDbIds),subVariantsPageSize))
    #check callsets
    logger.debug("server {} for allematrix has {} callsets, get {} on page {} with size {}".format(
                server["name"], subCallSetsTotal, len(subCallSetDbIds), 
        subCallSetsPage, subCallSetsPageSize))
    if not subCallSetsPage==serverParams["dimensionCallSetPage"]:
        logger.warning("unexpected callsets page: {} instead of {}".format(
            subCallSetsPage,serverParams["dimensionCallSetPage"]))
    elif not subCallSetsPageSize==serverParams["dimensionCallSetPageSize"]:
        logger.warning("unexpected callsets pageSize: {} instead of {}".format(
            subCallSetsPageSize,serverParams["dimensionCallSetPageSize"]))
    elif len(subCallSetDbIds)>subCallSetsPageSize:
        logger.warning("unexpected number of callsets: {} > {}".format(
            len(subCallSetDbIds),subCallSetsPageSize))

    if (subStartVariants<subVariantsTotal) and (subEndVariants>=0):
        sVariants1 = max(0,subStartVariants-(subVariantsPage*subVariantsPageSize))
        sVariants2 = min(subVariantsPageSize-1,
                         min(subVariantsTotal-1,subEndVariants)-(subVariantsPage*subVariantsPageSize))
        if sVariants2>=sVariants1:
            subVariantDbIds = subVariantDbIds[sVariants1:sVariants2+1]
            logger.debug("add {} variants ({} - {}) from {} to allelematrix result".format(
                len(subVariantDbIds),sVariants1,sVariants2,server["name"]))
            #another page necessary
            if subEndVariants>(((subVariantsPage+1)*subVariantsPageSize)-1):
                additionalVariantsRequest = True
        else:
            subVariantDbIds = []
    else:
        subVariantDbIds = []

    if (subStartCallSets<subCallSetsTotal) and (subEndCallSets>=0):
        sCallSets1 = max(0,subStartCallSets-(subCallSetsPage*subCallSetsPageSize))
        sCallSets2 = min(subCallSetsPageSize-1,
                         min(subCallSetsTotal-1,subEndCallSets)-(subCallSetsPage*subCallSetsPageSize))
        if sCallSets2>=sCallSets1:
            subCallSetDbIds = subCallSetDbIds[sCallSets1:sCallSets2+1]
            logger.debug("add {} callsets ({} - {}) from {} to allelematrix result".format(
                len(subCallSetDbIds),sCallSets1,sCallSets2,server["name"]))
            #another page necessary
            if subEndCallSets>(((subCallSetsPage+1)*subCallSetsPageSize)-1):
                additionalCallSetsRequest = True
        else:
            subCallSetDbIds = []
    else:
        subCallSetDbIds = []

    if len(subVariantDbIds)>0 and len(subCallSetDbIds)>0:
        subDataMatrices = itemResponse.get("result",{}).get("dataMatrices",[])
        for i in range(len(subDataMatrices)):
            subDataMatrices[i]["dataMatrix"] = [entry[sVariants1:sVariants2+1] for entry in 
                             subDataMatrices[i]["dataMatrix"][sCallSets1:sCallSets2+1]]
    else:
        subDataMatrices = []
        
    #server response
    return {"variantDbIds": subVariantDbIds,
            "variantSetDbIds": subVariantSetDbIds,
            "callSetDbIds": subCallSetDbIds,
            "dataMatrices": subDataMatrices,
            "variantsTotal": subVariantsTotal,
            "callSetsTotal": subCallSetsTotal,
            "additionalVariantsRequest": additionalVariantsRequest,
            "additionalCallSetsRequest": additionalCallSetsRequest}
    

def _mergeAllematrixDataMatrices(dataMatrices,newDataMatrices,
                                 variantsStart,variantsEnd,
                                 callSetsStart,callSetsEnd,
                                 unknownString):
    for i in range(len(newDataMatrices)):
        matrixFound = False
        newKey = (newDataMatrices[i]["dataMatrixAbbreviation"],
                  newDataMatrices[i]["dataMatrixName"],
                  newDataMatrices[i]["dataType"])
        for j in range(len(dataMatrices)):
            oldKey = (dataMatrices[j]["dataMatrixAbbreviation"],
                      dataMatrices[j]["dataMatrixName"],
                      dataMatrices[j]["dataType"])
            #glue new dataMatrix to existing
            if newKey==oldKey:
                matrixFound = True
                dataMatrix = dataMatrices[j]["dataMatrix"]
                for k in range(callSetsStart):
                    if k<len(dataMatrix):
                        dataMatrix[k] = dataMatrix[k] + [unknownString]*(variantsEnd-len(dataMatrix[k]))
                    else:
                        dataMatrix.append([unknownString]*variantsEnd)                           
                for k in range(callSetsStart,callSetsEnd):
                    if k<len(dataMatrix):
                        dataMatrix[k] = dataMatrix[k] + [unknownString]*(variantsEnd-len(dataMatrix[k]))
                        dataMatrix[k][variantsStart:variantsEnd] = (
                            newDataMatrices[i]["dataMatrix"][k-callSetsStart][0:variantsEnd-variantsStart])
                    else:
                        row = [unknownString]*variantsStart
                        row.extend(newDataMatrices[i]["dataMatrix"][k-callSetsStart])
                        dataMatrix.append(row)
                dataMatrices[j]["dataMatrix"] = dataMatrix
                break
        #insert new dataMatrix
        if not matrixFound:
            dataMatrix = []
            for k in range(callSetsStart):
                dataMatrix.append([unknownString]*variantsEnd)
            for k in range(callSetsStart,callSetsEnd):
                row = [unknownString]*variantsStart
                row.extend(newDataMatrices[i]["dataMatrix"][k-callSetsStart])
                dataMatrix.append(row)
            newDataMatrices[i]["dataMatrix"] = dataMatrix
            dataMatrices.append(newDataMatrices[i])
    #fix sizes if necessary
    for j in range(len(dataMatrices)):
        dataMatrix = dataMatrices[j]["dataMatrix"]
        for k in range(callSetsEnd):
            if k<len(dataMatrix):
                dataMatrix[k] = dataMatrix[k] + [unknownString]*(variantsEnd-len(dataMatrix[k]))
            else:
                dataMatrix.append([unknownString]*variantsEnd)
        dataMatrices[j]["dataMatrix"] = dataMatrix
    return dataMatrices
    
def _brapiRepaginateAllelematrixRequestResponse(brapi, params):
    #get servers
    servers = []
    for server in brapi["calls"]["allelematrix"]["servers"]:
        servers.append(brapi["servers"].get(server,{}))
    #initialise result
    result = {
        "callSetDbIds": [],
        "dataMatrices": [],
        "expandHomozygotes": params["expandHomozygotes"],
        "pagination": [
          {
            "dimension": "VARIANTS",
            "page": params["dimensionVariantPage"],
            "pageSize": params["dimensionVariantPageSize"],
            "totalCount": 0,
            "totalPages": 0
          },
          {
            "dimension": "CALLSETS",
            "page": params["dimensionCallSetPage"],
            "pageSize": params["dimensionCallSetPageSize"],
            "totalCount": 0,
            "totalPages": 0
          }
        ],
        "sepPhased": params["sepPhased"],
        "sepUnphased": params["sepUnphased"],
        "unknownString": params["unknownString"],
        "variantDbIds": [],
        "variantSetDbIds": []
    }
    #handle requests
    variantDbIds = []
    variantSetDbIds = []
    callSetDbIds = []
    dataMatrices = []
    totalCountVariants = 0
    startVariants = params["dimensionVariantPage"]*params["dimensionVariantPageSize"]
    endVariants = ((params["dimensionVariantPage"]+1)*params["dimensionVariantPageSize"]) - 1
    totalCountCallSets = 0
    startCallSets = params["dimensionCallSetPage"]*params["dimensionCallSetPageSize"]
    endCallSets = ((params["dimensionCallSetPage"]+1)*params["dimensionCallSetPageSize"]) - 1
    for server in servers:
        try:
            subStartVariants = startVariants - totalCountVariants
            subEndVariants = endVariants - totalCountVariants
            subStartCallSets = startCallSets - totalCountCallSets
            subEndCallSets = endCallSets - totalCountCallSets
            serverParams = handler.prefixRewriteParams(
                params,server["prefixes"],brapi["identifiers"])
            if not serverParams is None:
                #recompute page and pageSize
                serverParams["dimensionVariantPage"] = max(0,math.floor(subStartVariants/params["dimensionVariantPageSize"]))
                serverParams["dimensionVariantPageSize"] = params["dimensionVariantPageSize"]
                serverParams["dimensionCallSetPage"] = max(0,math.floor(subStartCallSets/params["dimensionCallSetPageSize"]))
                serverParams["dimensionCallSetPageSize"] = params["dimensionCallSetPageSize"]
                #restrict to preview if additional information is not needed
                if subStartVariants<0 and subEndVariants<0:
                    serverParams["preview"] = True
                elif subStartCallSets<0 and subEndCallSets<0:
                    serverParams["preview"] = True
                #get server response
                serverResponse = _brapiRepaginateAllelematrixServerRequest(
                                       server, serverParams, brapi["identifiers"],
                                       subStartVariants, subEndVariants, subStartCallSets, subEndCallSets)
                variantsStart = len(variantDbIds)
                variantsEnd = variantsStart + len(serverResponse["variantDbIds"])
                callSetsStart = len(callSetDbIds)
                callSetsEnd = callSetsStart + len(serverResponse["callSetDbIds"])
                variantDbIds = variantDbIds + serverResponse["variantDbIds"]
                variantSetDbIds = list(set(variantSetDbIds + serverResponse["variantSetDbIds"]))
                callSetDbIds = callSetDbIds + serverResponse["callSetDbIds"]
                dataMatrices = _mergeAllematrixDataMatrices(
                    dataMatrices, serverResponse["dataMatrices"],
                    variantsStart,variantsEnd,
                    callSetsStart,callSetsEnd,serverParams["unknownString"])
                totalCountVariants += serverResponse["variantsTotal"]
                totalCountCallSets += serverResponse["callSetsTotal"]
                if serverResponse["additionalVariantsRequest"] or serverResponse["additionalCallSetsRequest"]:
                    if serverResponse["additionalVariantsRequest"]:
                        serverParams1 = serverParams.copy()
                        subStartVariants1 = subStartVariants+len(serverResponse["variantDbIds"])
                        serverParams1["dimensionVariantPage"]+=1
                        newServerResponse1 = _brapiRepaginateAllelematrixServerRequest(
                                               server, serverParams1, brapi["identifiers"],
                                               subStartVariants1, subEndVariants, subStartCallSets, subEndCallSets)
                        variantDbIds = variantDbIds + newServerResponse1["variantDbIds"]
                        variantSetDbIds = list(set(variantSetDbIds + newServerResponse1["variantSetDbIds"]))
                        variantsStart1 = variantsStart + len(serverResponse["variantDbIds"])
                        variantsEnd1 = variantsStart1 + len(newServerResponse1["variantDbIds"])
                        dataMatrices = _mergeAllematrixDataMatrices(
                            dataMatrices, newServerResponse1["dataMatrices"],
                            variantsStart1,variantsEnd1,
                            callSetsStart,callSetsEnd,serverParams1["unknownString"])
                    if serverResponse["additionalCallSetsRequest"]:
                        serverParams2 = serverParams.copy()
                        subStartCallSets2 = subStartCallSets+len(serverResponse["callSetDbIds"])
                        serverParams2["dimensionCallSetPage"]+=1
                        newServerResponse2 = _brapiRepaginateAllelematrixServerRequest(
                                               server, serverParams2, brapi["identifiers"],
                                               subStartVariants, subEndVariants, subStartCallSets2, subEndCallSets)
                        callSetDbIds = callSetDbIds + newServerResponse2["callSetDbIds"]
                        callSetsStart2 = callSetsStart + len(serverResponse["callSetDbIds"])
                        callSetsEnd2 = callSetsStart2 + len(newServerResponse2["callSetDbIds"])
                        dataMatrices = _mergeAllematrixDataMatrices(
                            dataMatrices, newServerResponse2["dataMatrices"],
                            variantsStart,variantsEnd,
                            callSetsStart2,callSetsEnd2,serverParams2["unknownString"])
                    if serverResponse["additionalVariantsRequest"] and serverResponse["additionalCallSetsRequest"]:
                        serverParams3 = serverParams.copy()
                        subStartVariants3 = subStartVariants+len(serverResponse["variantDbIds"])
                        subStartCallSets3 = subStartCallSets+len(serverResponse["callSetDbIds"])
                        serverParams3["dimensionVariantPage"]+=1
                        serverParams3["dimensionCallSetPage"]+=1
                        newServerResponse3 = _brapiRepaginateAllelematrixServerRequest(
                                               server, serverParams3, brapi["identifiers"],
                                               subStartVariants3, subEndVariants, subStartCallSets3, subEndCallSets)
                        variantsStart3 = variantsStart + len(serverResponse["variantDbIds"])
                        variantsEnd3 = variantsStart3 + len(newServerResponse3["variantDbIds"])
                        callSetsStart3 = callSetsStart + len(serverResponse["callSetDbIds"])
                        callSetsEnd3 = callSetsStart3 + len(newServerResponse3["callSetDbIds"])
                        dataMatrices = _mergeAllematrixDataMatrices(
                            dataMatrices, newServerResponse3["dataMatrices"],
                            variantsStart3,variantsEnd3,
                            callSetsStart3,callSetsEnd3,serverParams3["unknownString"])
        except Exception as e: 
            return None, 500, "problem processing response from {}: {}".format(server["name"],str(e))
    #process results
    result["variantDbIds"] = variantDbIds
    result["variantSetDbIds"] = variantSetDbIds
    result["callSetDbIds"] = callSetDbIds
    result["dataMatrices"] = dataMatrices
    result["pagination"][0]["totalCount"] = totalCountVariants
    result["pagination"][0]["totalPages"] = math.ceil(totalCountVariants/params["dimensionVariantPageSize"])
    result["pagination"][1]["totalCount"] = totalCountCallSets
    result["pagination"][1]["totalPages"] = math.ceil(totalCountCallSets/params["dimensionCallSetPageSize"])
    #construct response
    response = {}
    response["@context"] = ["https://brapi.org/jsonld/context/metadata.jsonld"]
    response["metadata"] = {
        "datafiles": None,
        "status": [],
        "pagination": None
    }
    response["result"] = result
    return response, 200, None   
        
        
        
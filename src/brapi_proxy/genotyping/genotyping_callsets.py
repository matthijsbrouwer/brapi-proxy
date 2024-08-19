from flask import Response
from flask_restx import Resource
import json

from .. import handler
from . import ns_api_genotyping as namespace

parser = namespace.parser()
parser.add_argument("callSetDbId", type=str, required=False,
                    help="The ID which uniquely identifies a `CallSet` within the given database server")
parser.add_argument("callSetName", type=str, required=False,
                    help="The human readable name of a `CallSet`.")
parser.add_argument("variantSetDbId", type=str, required=False,
                    help="The ID which uniquely identifies a `VariantSet` within the given database server")
parser.add_argument("sampleDbId", type=str, required=False,
                    help="The ID which uniquely identifies a `Sample` within the given database server<br>Filter results to only include `CallSets` generated from this `Sample`")
parser.add_argument("germplasmDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given `Germplasm` unique identifier. \n<br/>Use `GET /germplasm` to find the list of available `Germplasm` on a server.")
parser.add_argument("page", type=int, required=False, 
        help="Used to request a specific page of data to be returned<br>The page indexing starts at 0 (the first page is 'page'= 0). Default is `0`")
parser.add_argument("pageSize", type=int, required=False,
        help="The size of the pages to be returned. Default is `1000`")
parser.add_argument("Authorization", type=str, required=False,
        help="HTTP HEADER - Token used for Authorization<br>**Bearer {token_string}**", 
        location="headers")

class GenotypingCallSets(Resource):

    @namespace.expect(parser, validate=True)
    @handler.authorization
    def get(self):
        strict = self.api.config.getboolean("brapi","strict") if self.api.config.has_option("brapi","strict") else False
        args = parser.parse_args(strict=strict)
        try:            
            #get parameters
            page = int(args["page"]) if not args["page"] is None else 0
            pageSize = int(args["pageSize"]) if not args["pageSize"] is None else 1000
            params = {"page": page, "pageSize": pageSize}
            for key,value in args.items():
                if not key in ["page","pageSize","Authorization"]:
                    if not value is None:
                        params[key] = value
            brapiResponse,brapiStatus,brapiError = handler.brapiRepaginateRequestResponse(
                self.api.brapi, "callsets", params=params)
            if brapiResponse:
                return Response(json.dumps(brapiResponse), mimetype="application/json")
            else:
                response = Response(json.dumps(str(brapiError)), mimetype="application/json")
                response.status_code = brapiStatus
                return response
        except Exception as e:
            response = Response(json.dumps(str(e)), mimetype="application/json")
            response.status_code = 500
            return response
            

parserId = namespace.parser()
parserId.add_argument("Authorization", type=str, required=False,
        help="HTTP HEADER - Token used for Authorization<br>**Bearer {token_string}**", 
        location="headers")
            
class GenotypingCallSetsId(Resource):

    @namespace.expect(parserId, validate=True)
    @handler.authorization
    def get(self,callSetDbId):
        strict = self.api.config.getboolean("brapi","strict") if self.api.config.has_option("brapi","strict") else False
        args = parser.parse_args(strict=strict)
        try:
            brapiResponse,brapiStatus,brapiError = handler.brapiIdRequestResponse(
                self.api.brapi, "callsets", "callSetDbId", callSetDbId)
            if brapiResponse:
                return Response(json.dumps(brapiResponse), mimetype="application/json")
            else:
                response = Response(json.dumps(str(brapiError)), mimetype="application/json")
                response.status_code = brapiStatus
                return response
        except Exception as e:
            response = Response(json.dumps(str(e)), mimetype="application/json")
            response.status_code = 500
            return response
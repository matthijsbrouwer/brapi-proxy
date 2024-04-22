from flask import Response, abort, request
from flask_restx import Resource
import json

from service import brapi
from service.genotyping import ns_api_genotyping as namespace

parser = namespace.parser()
parser.add_argument("variantDbId", type=str, required=False, 
        help="The ID which uniquely identifies a `Variant`")
parser.add_argument("variantSetDbId", type=str, required=False, 
        help="The ID which uniquely identifies a `VariantSet`")
parser.add_argument("referenceDbId", type=str, required=False, 
        help="The ID which uniquely identifies a `Reference`")
parser.add_argument("referenceSetDbId", type=str, required=False, 
        help="The ID which uniquely identifies a `ReferenceSet`")
parser.add_argument("externalReferenceId", type=str, required=False, 
        help="An external reference ID. Could be a simple string or a URI. (use with `externalReferenceSource` parameter)")
parser.add_argument("externalReferenceSource", type=str, required=False, 
        help="An identifier for the source system or database of an external reference (use with `externalReferenceId` parameter)")
parser.add_argument("page", type=int, required=False, 
        help="Used to request a specific page of data to be returned<br>The page indexing starts at 0 (the first page is 'page'= 0). Default is `0`")
parser.add_argument("pageSize", type=int, required=False,
        help="The size of the pages to be returned. Default is `1000`")
parser.add_argument("Authorization", type=str, required=False,
        help="HTTP HEADER - Token used for Authorization<br>**Bearer {token_string}**", 
        location="headers")

class GenotypingVariants(Resource):

    @namespace.expect(parser, validate=True)
    @brapi.authorization
    def get(self):
        args = parser.parse_args(strict=True)
        try:
            #get parameters
            page = int(request.args.get("page",0))
            pageSize = int(request.args.get("pageSize",1000))
            params = {"page": page, "pageSize": pageSize}
            for key,value in args.items():
                if not key in ["page","pageSize","Authorization"]:
                    if not value is None:
                        params[key] = value
            brapiResponse,brapiStatus,brapiError = brapi.BrAPI._brapiRepaginateRequestResponse(
                self.api.brapi, "variants", params=params)
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

class GenotypingVariantsId(Resource):

    @namespace.expect(parserId, validate=True)
    @brapi.authorization
    def get(self,variantDbId):
        args = parser.parse_args(strict=True)
        try:
            brapiResponse,brapiStatus,brapiError = brapi.BrAPI._brapiIdRequestResponse(
                self.api.brapi, "variants", "variantDbId", variantDbId)
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
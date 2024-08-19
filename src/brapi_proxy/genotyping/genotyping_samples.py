from flask import Response
from flask_restx import Resource
import json

from .. import handler
from . import ns_api_genotyping as namespace

parser = namespace.parser()
parser.add_argument("sampleDbId", type=str, required=False,
                    help="The unique identifier for a `Sample`")
parser.add_argument("sampleName", type=str, required=False,
                    help="The human readable name of the `Sample`")
parser.add_argument("sampleGroupDbId", type=str, required=False,
                    help="The unique identifier for a group of related `Samples`")
parser.add_argument("observationUnitDbId", type=str, required=False,
                    help="The ID which uniquely identifies an `ObservationUnit`")
parser.add_argument("plateDbId", type=str, required=False,
                    help="The ID which uniquely identifies a `Plate` of `Sample`")
parser.add_argument("plateName", type=str, required=False,
                    help="The human readable name of a `Plate` of `Sample`")
parser.add_argument("commonCropName", type=str, required=False,
                    help="The BrAPI Common Crop Name is the simple, generalized, widely accepted name of the organism being researched. It is most often used in multi-crop systems where digital resources need to be divided at a high level. Things like 'Maize', 'Wheat', and 'Rice' are examples of common crop names.\n\nUse this parameter to only return results associated with the given crop. \n\nUse `GET /commoncropnames` to find the list of available crops on a server.")
parser.add_argument("programDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given `Program` unique identifier. \n<br/>Use `GET /programs` to find the list of available `Programs` on a server.")
parser.add_argument("trialDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given `Trial` unique identifier. \n<br/>Use `GET /trials` to find the list of available `Trials` on a server.")
parser.add_argument("studyDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given `Study` unique identifier. \n<br/>Use `GET /studies` to find the list of available `Studies` on a server.")
parser.add_argument("germplasmDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given `Germplasm` unique identifier. \n<br/>Use `GET /germplasm` to find the list of available `Germplasm` on a server.")
parser.add_argument("externalReferenceID", type=str, required=False,
                    help="**Deprecated in v2.1** Please use `externalReferenceId`. Github issue number #460 \n<br>An external reference ID. Could be a simple string or a URI. (use with `externalReferenceSource` parameter)")
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

class GenotypingSamples(Resource):

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
                self.api.brapi, "samples", params=params)
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
            
class GenotypingSamplesId(Resource):

    @namespace.expect(parserId, validate=True)
    @handler.authorization
    def get(self,sampleDbId):
        strict = self.api.config.getboolean("brapi","strict") if self.api.config.has_option("brapi","strict") else False
        args = parser.parse_args(strict=strict)
        try:
            brapiResponse,brapiStatus,brapiError = handler.brapiIdRequestResponse(
                self.api.brapi, "samples", "sampleDbId", sampleDbId)
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
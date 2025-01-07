from flask import Response
from flask_restx import Resource
import json

from .. import handler
from . import ns_api_phenotyping as namespace

parser = namespace.parser()
parser.add_argument("observationDbId", type=str, required=False,
                    help="The unique ID of an Observation")
parser.add_argument("observationUnitDbId", type=str, required=False,
                    help="The unique ID of an Observation Unit")
parser.add_argument("observationVariableDbId", type=str, required=False,
                    help="The unique ID of an observation variable")
parser.add_argument("locationDbId", type=str, required=False,
                    help="The unique ID of a location where these observations were collected")
parser.add_argument("seasonDbId", type=str, required=False,
                    help="The year or Phenotyping campaign of a multi-annual study (trees, grape, ...)")
parser.add_argument("observationTimeStampRangeStart", type=str, required=False,
                    help="Timestamp range start")
parser.add_argument("observationTimeStampRangeEnd", type=str, required=False,
                    help="Timestamp range end")
parser.add_argument("observationUnitLevelName", type=str, required=False,
                    help="The Observation Unit Level. Returns only the observation unit of the specified Level.")
parser.add_argument("observationUnitLevelOrder", type=str, required=False,
                    help="The Observation Unit Level Order Number. Returns only the observation unit of the specified Level.")
parser.add_argument("observationUnitLevelCode", type=str, required=False,
                    help="The Observation Unit Level Code. This parameter should be used together with `observationUnitLevelName` or `observationUnitLevelOrder`")
parser.add_argument("observationUnitLevelRelationshipName", type=str, required=False,
                    help="The Observation Unit Level Relationship is a connection that this observation unit has to another level of the hierarchy.")
parser.add_argument("observationUnitLevelRelationshipOrder", type=str, required=False,
                    help="The Observation Unit Level Order Number.<br>Returns only the observation unit of the specified Level.")
parser.add_argument("observationUnitLevelRelationshipCode", type=str, required=False,
                    help="The Observation Unit Level Code.<br>This parameter should be used together with `observationUnitLevelName` or `observationUnitLevelOrder`.")
parser.add_argument("observationUnitLevelRelationshipDbId", type=str, required=False,
                    help="The observationUnitDbId associated with a particular level and code.<br>This parameter should be used together with `observationUnitLevelName` or `observationUnitLevelOrder`.")
parser.add_argument("commonCropName", type=str, required=False,
                    help="The BrAPI Common Crop Name is the simple, generalized, widely accepted name of the organism being researched. It is most often used in multi-crop systems where digital resources need to be divided at a high level. Things like 'Maize', 'Wheat', and 'Rice' are examples of common crop names.<br>Use this parameter to only return results associated with the given crop.<br>Use `GET /commoncropnames` to find the list of available crops on a server.")
parser.add_argument("programDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given Program unique identifier.<br>Use `GET /programs` to find the list of available Programs on a server.")
parser.add_argument("trialDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given Trial unique identifier.<br>Use `GET /trials` to find the list of available Trials on a server.")
parser.add_argument("studyDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given Study unique identifier.<br>Use `GET /studies` to find the list of available Studies on a server.")
parser.add_argument("germplasmDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given Germplasm unique identifier.<br>Use `GET /germplasm` to find the list of available Germplasm on a server.")
parser.add_argument("externalReferenceID", type=str, required=False,
                    help="**Deprecated in v2.1** Please use `externalReferenceId`. Github issue number #460<br>An external reference ID. Could be a simple string or a URI. (use with `externalReferenceSource` parameter)")
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

class PhenotypingObservations(Resource):

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
                self.api.brapi, "observations", params=params)
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
            
class PhenotypingObservationsId(Resource):

    @namespace.expect(parserId, validate=True)
    @handler.authorization
    def get(self,observationDbId):
        strict = self.api.config.getboolean("brapi","strict") if self.api.config.has_option("brapi","strict") else False
        args = parser.parse_args(strict=strict)
        try:
            brapiResponse,brapiStatus,brapiError = handler.brapiIdRequestResponse(
                self.api.brapi, "observations", "observationDbId", observationDbId)
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
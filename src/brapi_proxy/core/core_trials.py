from flask import Response
from flask_restx import Resource
import json

from .. import handler
from . import ns_api_core as namespace


parser = namespace.parser()
parser.add_argument("active", type=bool, required=False,
                    help="A flag to indicate if a Study is currently active and ongoing")
parser.add_argument("contactDbId", type=str, required=False,
                    help="Contact entities associated with this trial")
parser.add_argument("locationDbId", type=str, required=False,
                    help="Filter by location")
parser.add_argument("searchDateRangeStart", type=str, required=False,
                    help="The start of the overlapping search date range. `searchDateRangeStart` must be before `searchDateRangeEnd`.\n\nReturn a Trial entity if any of the following cases are true\n\n- `searchDateRangeStart` is before `trial.endDate` AND `searchDateRangeEnd` is null \n\n- `searchDateRangeStart` is before `trial.endDate` AND `searchDateRangeEnd` is after `trial.startDate`\n\n- `searchDateRangeEnd` is after `trial.startDate` AND `searchDateRangeStart` is null\n\n- `searchDateRangeEnd` is after `trial.startDate` AND `searchDateRangeStart` is before `trial.endDate`")
parser.add_argument("searchDateRangeEnd", type=str, required=False,
                    help="The start of the overlapping search date range. `searchDateRangeStart` must be before `searchDateRangeEnd`.\n\nReturn a Trial entity if any of the following cases are true\n\n- `searchDateRangeStart` is before `trial.endDate` AND `searchDateRangeEnd` is null \n\n- `searchDateRangeStart` is before `trial.endDate` AND `searchDateRangeEnd` is after `trial.startDate`\n\n- `searchDateRangeEnd` is after `trial.startDate` AND `searchDateRangeStart` is null\n\n- `searchDateRangeEnd` is after `trial.startDate` AND `searchDateRangeStart` is before `trial.endDate`")
parser.add_argument("trialPUI", type=str, required=False,
                    help="Filter by trial PUI")
parser.add_argument("sortBy", type=str, required=False,
                    choices=["trialDbId", "trialName", "programDbId", "programName", "locationDbId", 
                             "startDate", "endDate"],
                    help="Sort order. Name of the field to sort by.")
parser.add_argument("sortOrder", type=str, required=False,
                    choices=["asc", "ASC", "desc", "DESC"],
                    help="Sort order direction. Ascending/Descending.")
parser.add_argument("commonCropName", type=str, required=False,
                    help="he BrAPI Common Crop Name is the simple, generalized, widely accepted name of the organism being researched. It is most often used in multi-crop systems where digital resources need to be divided at a high level. Things like 'Maize', 'Wheat', and 'Rice' are examples of common crop names.\n\nUse this parameter to only return results associated with the given crop. \n\nUse `GET /commoncropnames` to find the list of available crops on a server.")
parser.add_argument("programDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given `Program` unique identifier. \n<br/>Use `GET /programs` to find the list of available `Programs` on a server.")
parser.add_argument("trialDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given `Trial` unique identifier. \n<br/>Use `GET /trials` to find the list of available `Trials` on a server.")
parser.add_argument("trialName", type=str, required=False,
                    help="Use this parameter to only return results associated with the given `Trial` by its human readable name. \n<br/>Use `GET /trials` to find the list of available `Trials` on a server.")
parser.add_argument("studyDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given `Study` unique identifier. \n<br/>Use `GET /studies` to find the list of available `Studies` on a server.")
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

class CoreTrials(Resource):

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
                self.api.brapi, "trials", params=params, unsupportedForMultipleServerResponse=["sortBy","sortOrder"])
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
            
class CoreTrialsId(Resource):

    @namespace.expect(parserId, validate=True)
    @handler.authorization
    def get(self,trialDbId):
        strict = self.api.config.getboolean("brapi","strict") if self.api.config.has_option("brapi","strict") else False
        args = parser.parse_args(strict=strict)
        try:
            brapiResponse,brapiStatus,brapiError = handler.brapiIdRequestResponse(
                self.api.brapi, "trials", "trialDbId", trialDbId)
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
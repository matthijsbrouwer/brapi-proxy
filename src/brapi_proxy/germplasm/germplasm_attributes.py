from flask import Response
from flask_restx import Resource
import json

from .. import handler
from . import ns_api_germplasm as namespace

parser = namespace.parser()
parser.add_argument("attributeCategory", type=str, required=False,
                    help="The general category for the attribute. very similar to Trait class.")
parser.add_argument("attributeDbId", type=str, required=False,
                    help="The unique id for an attribute")
parser.add_argument("attributeName", type=str, required=False,
                    help="The human readable name for an attribute")
parser.add_argument("attributePUI", type=str, required=False,
                    help="The Permanent Unique Identifier of an Attribute, usually in the form of a URI")
parser.add_argument("methodDbId", type=str, required=False,
                    help="Method unique identifier")
parser.add_argument("methodName", type=str, required=False,
                    help="Human readable name for the method MIAPPE V1.1 (DM-88) Method Name of the method of observation")
parser.add_argument("methodPUI", type=str, required=False,
                    help="The Permanent Unique Identifier of a Method, usually in the form of a URI")
parser.add_argument("scaleDbId", type=str, required=False,
                    help="Scale unique identifier")
parser.add_argument("scaleName", type=str, required=False,
                    help="Human readable name for the scale MIAPPE V1.1 (DM-88) Scale Name of the scale of observation")
parser.add_argument("scalePUI", type=str, required=False,
                    help="The Permanent Unique Identifier of a Scale, usually in the form of a URI")
parser.add_argument("traitDbId", type=str, required=False,
                    help="Trait unique identifier")
parser.add_argument("traitName", type=str, required=False,
                    help="Human readable name for the trait MIAPPE V1.1 (DM-88) Trait Name of the trait of observation")
parser.add_argument("traitPUI", type=str, required=False,
                    help="The Permanent Unique Identifier of a Trait, usually in the form of a URI")
parser.add_argument("commonCropName", type=str, required=False,
                    help="The BrAPI Common Crop Name is the simple, generalized, widely accepted name of the organism being researched. It is most often used in multi-crop systems where digital resources need to be divided at a high level. Things like 'Maize', 'Wheat', and 'Rice' are examples of common crop names. Use this parameter to only return results associated with the given crop.")
parser.add_argument("programDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given `Program` unique identifier. ")
parser.add_argument("germplasmDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given `Germplasm` unique identifier. ")
parser.add_argument("externalReferenceID", type=str, required=False,
                    help="An external reference ID. Could be a simple string or a URI. (use with `externalReferenceSource` parameter)")
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

class GermplasmAttributes(Resource):

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
                self.api.brapi, "attributes", params=params)
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
            
class GermplasmAttributesId(Resource):

    @namespace.expect(parserId, validate=True)
    @handler.authorization
    def get(self,attributeDbId):
        strict = self.api.config.getboolean("brapi","strict") if self.api.config.has_option("brapi","strict") else False
        args = parser.parse_args(strict=strict)
        try:
            brapiResponse,brapiStatus,brapiError = handler.brapiIdRequestResponse(
                self.api.brapi, "attributes", "attributeDbId", attributeDbId)
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
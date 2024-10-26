from flask import Response
from flask_restx import Resource
import json

from .. import handler
from . import ns_api_germplasm as namespace

parser = namespace.parser()
parser.add_argument("accessionNumber", type=str, required=False,
                    help="The unique identifier for a material or germplasm within a genebank<br>MCPD (v2.1) (ACCENUMB) 2. This is the unique identifier for accessions within a genebank, and is assigned when a sample is entered into the genebank collection (e.g. \"PI 113869\").")
parser.add_argument("collection", type=str, required=False,
                    help="A specific panel/collection/population name this germplasm belongs to.")
parser.add_argument("binomialName", type=str, required=False,
                    help="The full binomial name (scientific name) to identify a germplasm")
parser.add_argument("genus", type=str, required=False,
                    help="Genus name to identify germplasm")
parser.add_argument("species", type=str, required=False,
                    help="Species name to identify germplasm")
parser.add_argument("synonym", type=str, required=False,
                    help="Alternative name or ID used to reference this germplasm")
parser.add_argument("parentDbId", type=str, required=False,
                    help="Search for Germplasm with this parent")
parser.add_argument("progenyDbId", type=str, required=False,
                    help="Search for Germplasm with this child")
parser.add_argument("commonCropName", type=str, required=False,
                    help="The BrAPI Common Crop Name is the simple, generalized, widely accepted name of the organism being researched. It is most often used in multi-crop systems where digital resources need to be divided at a high level. Things like 'Maize', 'Wheat', and 'Rice' are examples of common crop names.<br>Use this parameter to only return results associated with the given crop.<br>Use GET /commoncropnames to find the list of available crops on a server.")
parser.add_argument("programDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given Program unique identifier.<br>Use GET /programs to find the list of available Programs on a server.")
parser.add_argument("trialDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given Trial unique identifier.<br>Use GET /trials to find the list of available Trials on a server.")
parser.add_argument("studyDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given Study unique identifier.<br>Use GET /studies to find the list of available Studies on a server.")
parser.add_argument("germplasmDbId", type=str, required=False,
                    help="Use this parameter to only return results associated with the given Germplasm unique identifier.<br>Use GET /germplasm to find the list of available Germplasm on a server.")
parser.add_argument("germplasmName", type=str, required=False,
                    help="Use this parameter to only return results associated with the given Germplasm by its human readable name.<br>Use GET /germplasm to find the list of available Germplasm on a server.")
parser.add_argument("germplasmPUI", type=str, required=False,
                    help="Use this parameter to only return results associated with the given Germplasm by its global permanent unique identifier.<br>Use GET /germplasm to find the list of available Germplasm on a server.")
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

class GermplasmGermplasm(Resource):

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
                self.api.brapi, "germplasm", params=params)
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
            
class GermplasmGermplasmId(Resource):

    @namespace.expect(parserId, validate=True)
    @handler.authorization
    def get(self,germplasmDbId):
        strict = self.api.config.getboolean("brapi","strict") if self.api.config.has_option("brapi","strict") else False
        args = parser.parse_args(strict=strict)
        try:
            brapiResponse,brapiStatus,brapiError = handler.brapiIdRequestResponse(
                self.api.brapi, "germplasm", "germplasmDbId", germplasmDbId)
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
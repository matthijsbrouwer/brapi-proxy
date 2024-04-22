from flask import Response, abort, request
from flask_restx import Resource
import json

from service import brapi
from service.core import ns_api_core as namespace

parser = namespace.parser()
parser.add_argument("page", type=int, required=False, 
        help="Used to request a specific page of data to be returned<br>The page indexing starts at 0 (the first page is 'page'= 0). Default is `0`")
parser.add_argument("pageSize", type=int, required=False,
        help="The size of the pages to be returned. Default is `1000`")
parser.add_argument("Authorization", type=str, required=False,
        help="HTTP HEADER - Token used for Authorization<br>**Bearer {token_string}**", 
        location="headers")

class CoreCommoncropnames(Resource):

    @namespace.expect(parser, validate=True)
    @brapi.authorization
    def get(self):
        args = parser.parse_args(strict=True)
        try:
            #get parameters
            page = int(args["page"]) if not args["page"] is None else 0
            pageSize = int(args["pageSize"]) if not args["pageSize"] is None else 1000
            params = {"page": page, "pageSize": pageSize}
            for key,value in args.items():
                if not key in ["page","pageSize","Authorization"]:
                    if not value is None:
                        params[key] = value
            brapiResponse,brapiStatus,brapiError = brapi.BrAPI._brapiRepaginateRequestResponse(
                self.api.brapi, "commoncropnames", params=params)
            if brapiResponse:
                return Response(json.dumps(brapiResponse), mimetype="application/json")
            else:
                response = Response(brapiError, mimetype="content/text")
                response.status_code = brapiStatus
                return response
        except Exception as e:
            response = Response(str(e), mimetype="content/text")
            response.status_code = 500
            return response

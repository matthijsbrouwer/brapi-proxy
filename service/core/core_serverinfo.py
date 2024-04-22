from flask import Response, abort, request
from flask_restx import Resource
import json

from service import brapi
from service.core import ns_api_core as namespace

parser = namespace.parser()
parser.add_argument("contentType", type=str, required=False, 
        choices=["application/json", "text/csv", "text/tsv", "application/flapjack"],
        help="Filter the list of endpoints based on the response content type")
parser.add_argument("dataType", type=str, required=False,
        choices=["application/json", "text/csv", "text/tsv", "application/flapjack"],
        help="**Deprecated in v2.1** Please use `contentType`<br>The data format supported by the call")
parser.add_argument("Authorization", type=str, required=False,
        help="HTTP HEADER - Token used for Authorization<br>**Bearer {token_string}**", 
        location="headers")

class CoreServerinfo(Resource):

    @namespace.expect(parser, validate=True)
    @brapi.authorization
    def get(self):
        args = parser.parse_args(strict=True)
        try:
            result = {"calls": []}
            for call,definition in self.api.__schema__["paths"].items():
                entry = {
                    "contentTypes":["application/json"],
                    "dataTypes":["application/json"],
                    "methods": [method.upper() for method in definition.keys() 
                                if method.upper() in ["GET","PUT","POST","DELETE"]],
                    "service": str(call).removeprefix("/"),
                    "versions":[self.api.config.get("brapi","version")]
                }
                result["calls"].append(entry)
            if not args["contentType"] is None:
                result["calls"] = [entry for entry in result["calls"] if args["contentType"] in entry["contentTypes"]]
            elif not args["dataType"] is None:
                result["calls"] = [entry for entry in result["calls"] if args["dataType"] in entry["dataTypes"]]
            for item in ["contactEmail","documentationURL","location","organizationName",
                         "organizationURL","serverDescription","serverName"]:
                if self.api.config.has_option("serverinfo",item):
                    result[item] = str(self.api.config.get("serverinfo",item))
            return Response(json.dumps(brapi.BrAPI._brapiResponse(result)), mimetype="application/json") 
        except Exception as e:
            abort(e.code if hasattr(e,"code") else 500, str(e))

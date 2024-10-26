from flask import Response, abort
from flask_restx import Resource
import json

from .. import handler
from . import ns_api_core as namespace

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
    @handler.authorization
    def get(self):
        strict = self.api.config.getboolean("brapi","strict") if self.api.config.has_option("brapi","strict") else False
        args = parser.parse_args(strict=strict)
        try:
            result = {"calls": []}
            for call,value in self.api.brapi["calls"].items():
                versions = value.get("acceptedVersions",[])
                for resource in value.get("resources",[]):
                    methods = []
                    # print(resource[0].methods)
                    for method in ["get","post","put","delete"]:
                        if hasattr(resource[0], method) and callable(getattr(resource[0],method)): 
                            methods.append(method.upper())
                    entry = {
                        "contentTypes":["application/json"],
                        "dataTypes":["application/json"],
                        "methods": methods,
                        "service": str(resource[1]).removeprefix("/"),
                        "versions": versions
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
                else:
                    result[item] = None
            return Response(json.dumps(handler.brapiResponse(result)), mimetype="application/json") 
        except Exception as e:
            abort(e.code if hasattr(e,"code") else 500, str(e))

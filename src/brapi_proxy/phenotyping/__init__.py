from flask_restx import Namespace

ns_api_phenotyping = Namespace("phenotyping",
    description="The BrAPI-Phenotyping module contains entities related to phenotypic observations. ", 
    path="/")

from .phenotyping_ontologies import PhenotypingOntologies,PhenotypingOntologiesId

# <callName> : {
#     "namespace": <identifier>,
#     "identifier": <identifier>,
#     "acceptedVersions": [<version>,<version>,...],
#     "additionalVersions": [<version>,<version>,...],
#     "requiredServices": [(<method>,<service>),...],
#     "optionalServices": [(<method>,<service>),...],
#     "resources": [(<Resource>,<location>),...]
# }

calls_api_phenotyping = {
    "ontologies": {
        "namespace": ns_api_phenotyping.name,
        "acceptedVersions": ["2.1"],
        "additionalVersions": ["2.0"],
        "requiredServices": [("get","ontologies")],
        "optionalServices": [("get","ontologies/{ontologyDbId}")],
        "resources": [(PhenotypingOntologies,"/ontologies"),
                      (PhenotypingOntologiesId,"/ontologies/<ontologyDbId>")]
    },
}

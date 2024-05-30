from flask_restx import Namespace

ns_api_germplasm = Namespace("germplasm",
    description="The BrAPI-Germplasm module contains entities related to germplasm management.", 
    path="/")

from .germplasm_breedingmethods import GermplasmBreedingMethods,GermplasmBreedingMethodsId

# <callName> : {
#     "namespace": <identifier>,
#     "identifier": <identifier>,
#     "acceptedVersions": [<version>,<version>,...],
#     "additionalVersions": [<version>,<version>,...],
#     "requiredServices": [(<method>,<service>),...],
#     "optionalServices": [(<method>,<service>),...],
#     "resources": [(<Resource>,<location>),...]
# }

calls_api_germplasm = {
    "breedingmethods": {
        "namespace": ns_api_germplasm.name,
        "identifier": "breedingMethodDbId",
        "acceptedVersions": ["2.1","2.0"],
        "requiredServices": [("get","breedingmethods")],
        "optionalServices": [("get","breedingmethods/{breedingMethodDbId}")],
        "resources": [(GermplasmBreedingMethods,"/breedingmethods"),
                      (GermplasmBreedingMethodsId,"/breedingmethods/<breedingMethodDbId>")]
    },
}
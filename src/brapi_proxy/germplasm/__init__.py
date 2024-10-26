from flask_restx import Namespace

ns_api_germplasm = Namespace("germplasm",
    description="The BrAPI-Germplasm module contains entities related to germplasm management.", 
    path="/")

from .germplasm_breedingmethods import GermplasmBreedingMethods,GermplasmBreedingMethodsId
from .germplasm_germplasm import GermplasmGermplasm,GermplasmGermplasmId
from .germplasm_attributes import GermplasmAttributes,GermplasmAttributesId
from .germplasm_attributevalues import GermplasmAttributeValues,GermplasmAttributeValuesId

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
    "germplasm": {
        "namespace": ns_api_germplasm.name,
        "identifier": "germplasmDbId",
        "acceptedVersions": ["2.1","2.0"],
        "requiredServices": [("get","germplasm")],
        "optionalServices": [("get","germplasm/{germplasmDbId}")],
        "resources": [(GermplasmGermplasm,"/germplasm"),
                      (GermplasmGermplasmId,"/germplasm/<germplasmDbId>")]
    },
    "attributes": {
        "namespace": ns_api_germplasm.name,
        "identifier": "attributeDbId",
        "acceptedVersions": ["2.1","2.0"],
        "requiredServices": [("get","attributes")],
        "optionalServices": [("get","attributes/{attributeDbId}")],
        "resources": [(GermplasmAttributes,"/attributes"),
                      (GermplasmAttributesId,"/attributes/<attributeDbId>")]
    },
    "attributevalues": {
        "namespace": ns_api_germplasm.name,
        "identifier": "attributeValueDbId",
        "acceptedVersions": ["2.1","2.0"],
        "requiredServices": [("get","attributevalues")],
        "optionalServices": [("get","attributevalues/{attributeValueDbId}")],
        "resources": [(GermplasmAttributeValues,"/attributevalues"),
                      (GermplasmAttributeValuesId,"/attributevalues/<attributeValueDbId>")]
    },
}
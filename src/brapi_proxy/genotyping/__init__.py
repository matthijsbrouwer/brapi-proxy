from flask_restx import Namespace

ns_api_genotyping = Namespace("genotyping",
    description="The BrAPI-Genotyping module contains entities related to genotyping analysis.", 
    path="/")

from .genotyping_variants import GenotypingVariants,GenotypingVariantsId
from .genotyping_samples import GenotypingSamples,GenotypingSamplesId
from .genotyping_plates import GenotypingPlates,GenotypingPlatesId
from .genotyping_references import GenotypingReferences,GenotypingReferencesId
from .genotyping_variantsets import GenotypingVariantSets,GenotypingVariantSetsId
from .genotyping_referencesets import GenotypingReferenceSets,GenotypingReferenceSetsId
from .genotyping_callsets import GenotypingCallSets,GenotypingCallSetsId
from .genotyping_allelematrix import GenotypingAllelematrix

# <callName> : {
#     "namespace": <identifier>,
#     "identifier": <identifier>,
#     "acceptedVersions": [<version>,<version>,...],
#     "additionalVersions": [<version>,<version>,...],
#     "requiredServices": [(<method>,<service>),...],
#     "optionalServices": [(<method>,<service>),...],
#     "resources": [(<Resource>,<location>),...]
# }

calls_api_genotyping = {
    "variants": {
        "namespace": ns_api_genotyping.name,
        "identifier": "variantDbId",
        "acceptedVersions": ["2.1"],
        "requiredServices": [("get","variants")],
        "optionalServices": [("get","variants/{variantDbId}")],
        "resources": [(GenotypingVariants,"/variants"),
                      (GenotypingVariantsId,"/variants/<variantDbId>")]
    },
    "samples": {
        "namespace": ns_api_genotyping.name,
        "identifier": "sampleDbId",
        "acceptedVersions": ["2.1"],
        "requiredServices": [("get","samples")],
        "optionalServices": [("get","samples/{sampleDbId}")],
        "resources": [(GenotypingSamples,"/samples"),
                      (GenotypingSamplesId,"/samples/<sampleDbId>")]
    },
    "plates": {
        "namespace": ns_api_genotyping.name,
        "identifier": "plateDbId",
        "acceptedVersions": ["2.1"],
        "requiredServices": [("get","plates")],
        "optionalServices": [("get","plates/{plateDbId}")],
        "resources": [(GenotypingPlates,"/plates"),
                      (GenotypingPlatesId,"/plates/<plateDbId>")]
    },
    "references": {
        "namespace": ns_api_genotyping.name,
        "identifier": "referenceDbId",
        "acceptedVersions": ["2.1"],
        "requiredServices": [("get","references")],
        "optionalServices": [("get","references/{referenceDbId}")],
        "resources": [(GenotypingReferences,"/references"),
                      (GenotypingReferencesId,"/references/<referenceDbId>")]
    },
    "variantsets": {
        "namespace": ns_api_genotyping.name,
        "identifier": "variantSetDbId",
        "acceptedVersions": ["2.1"],
        "requiredServices": [("get","variantsets")],
        "optionalServices": [("get","variantsets/{variantSetDbId}")],
        "resources": [(GenotypingVariantSets,"/variantsets"),
                      (GenotypingVariantSetsId,"/variantsets/<variantSetDbId>")]
    },
    "referencesets": {
        "namespace": ns_api_genotyping.name,
        "identifier": "referenceSetDbId",
        "acceptedVersions": ["2.1"],
        "requiredServices": [("get","referencesets")],
        "optionalServices": [("get","referencesets/{referenceSetDbId}")],
        "resources": [(GenotypingReferenceSets,"/referencesets"),
                      (GenotypingReferenceSetsId,"/referencesets/<referenceSetDbId>")]
    },
    "callsets": {
        "namespace": ns_api_genotyping.name,
        "identifier": "callSetDbId",
        "acceptedVersions": ["2.1"],
        "requiredServices": [("get","callsets")],
        "optionalServices": [("get","callsets/{callSetDbId}")],
        "resources": [(GenotypingCallSets,"/callsets"),
                      (GenotypingCallSetsId,"/callsets/<callSetDbId>")]
    },
    "allelematrix": {
        "namespace": ns_api_genotyping.name,
        "acceptedVersions": ["2.1"],
        "requiredServices": [("get","allelematrix")],
        "resources": [(GenotypingAllelematrix,"/allelematrix")]
    }
}

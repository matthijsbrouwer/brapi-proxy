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

# callName: [
#    <callIdentifierName>,
#    [<requiredService>,...],
#    [<optionalService>,...],
#    [[<resourceClass,<location>],...]
#]

calls_api_genotyping = {
    "variants": ("variantDbId",[("get","variants")],[("get","variants/{variantDbId}")],
                 [(GenotypingVariants,"/variants"),
                 (GenotypingVariantsId,"/variants/<variantDbId>")]),
    "samples": ("sampleDbId",[("get","samples")],[("get","samples/{sampleDbId}")],
                [(GenotypingSamples,"/samples"),
                (GenotypingSamplesId,"/samples/<sampleDbId>")]),
    "plates": ("plateDbId",[("get","plates")],[("get","plates/{plateDbId}")],
                [(GenotypingPlates,"/plates"),
                (GenotypingPlatesId,"/plates/<plateDbId>")]),
    "references": ("referenceDbId",[("get","references")],[("get","references/{referenceDbId}")],
                 [(GenotypingReferences,"/references"),
                (GenotypingReferencesId,"/references/<referenceDbId>")]),
    "variantsets": ("variantSetDbId",[("get","variantsets")],[("get","variantsets/{variantSetDbId}")],
                 [(GenotypingVariantSets,"/variantsets"),
                (GenotypingVariantSetsId,"/variantsets/<variantSetDbId>")]),
    "referencesets": ("referenceSetDbId",[("get","referencesets")],[("get","referencesets/{referenceSetDbId}")],
                 [(GenotypingReferenceSets,"/referencesets"),
                (GenotypingReferenceSetsId,"/referencesets/<referenceSetDbId>")]),
    "callsets": ("callSetDbId",[("get","callsets")],[("get","callsets/{callSetDbId}")],
                 [(GenotypingCallSets,"/callsets"),
                (GenotypingCallSetsId,"/callsets/<callSetDbId>")]),
    "allelematrix": (None,[("get","allelematrix")],[],
                 [(GenotypingAllelematrix,"/allelematrix")]),
}

from flask_restx import Namespace

ns_api_genotyping = Namespace("genotyping",
    description="The BrAPI-Genotyping module contains entities related to genotyping analysis.", 
    path="/")

from service.genotyping.genotyping_variants import GenotypingVariants,GenotypingVariantsId
from service.genotyping.genotyping_samples import GenotypingSamples,GenotypingSamplesId
from service.genotyping.genotyping_plates import GenotypingPlates,GenotypingPlatesId
from service.genotyping.genotyping_references import GenotypingReferences,GenotypingReferencesId
from service.genotyping.genotyping_variantsets import GenotypingVariantSets,GenotypingVariantSetsId
from service.genotyping.genotyping_referencesets import GenotypingReferenceSets,GenotypingReferenceSetsId
from service.genotyping.genotyping_callsets import GenotypingCallSets,GenotypingCallSetsId
from service.genotyping.genotyping_allelematrix import GenotypingAllelematrix

calls_api_genotyping = {
    "variants": [(GenotypingVariants,"/variants"),
                 (GenotypingVariantsId,"/variants/<variantDbId>")],
    "samples": [(GenotypingSamples,"/samples"),
                (GenotypingSamplesId,"/samples/<sampleDbId>")],
    "plates": [(GenotypingPlates,"/plates"),
                (GenotypingPlatesId,"/plates/<plateDbId>")],
    "references": [(GenotypingReferences,"/references"),
                (GenotypingReferencesId,"/references/<referenceDbId>")],
    "variantsets": [(GenotypingVariantSets,"/variantsets"),
                (GenotypingVariantSetsId,"/variantsets/<variantSetDbId>")],
    "referencesets": [(GenotypingReferenceSets,"/referencesets"),
                (GenotypingReferenceSetsId,"/referencesets/<referenceSetDbId>")],
    "callsets": [(GenotypingCallSets,"/callsets"),
                (GenotypingCallSetsId,"/callsets/<callSetDbId>")],
    "allelematrix": [(GenotypingAllelematrix,"/allelematrix")],
}

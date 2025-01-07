from flask_restx import Namespace

ns_api_phenotyping = Namespace("phenotyping",
    description="The BrAPI-Phenotyping module contains entities related to phenotypic observations. ", 
    path="/")

from .phenotyping_methods import PhenotypingMethods,PhenotypingMethodsId
from .phenotyping_observations import PhenotypingObservations,PhenotypingObservationsId
from .phenotyping_observationunits import PhenotypingObservationUnits,PhenotypingObservationUnitsId
from .phenotyping_ontologies import PhenotypingOntologies,PhenotypingOntologiesId
from .phenotyping_scales import PhenotypingScales,PhenotypingScalesId
from .phenotyping_traits import PhenotypingTraits,PhenotypingTraitsId
from .phenotyping_variables import PhenotypingVariables,PhenotypingVariablesId

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
    "methods": {
        "namespace": ns_api_phenotyping.name,
        "acceptedVersions": ["2.1"],
        "additionalVersions": ["2.0"],
        "requiredServices": [("get","methods")],
        "optionalServices": [("get","methods/{methodDbId}")],
        "resources": [(PhenotypingMethods,"/methods"),
                      (PhenotypingMethodsId,"/methods/<methodDbId>")]
    },
    "observations": {
        "namespace": ns_api_phenotyping.name,
        "acceptedVersions": ["2.1"],
        "additionalVersions": ["2.0"],
        "requiredServices": [("get","observations")],
        "optionalServices": [("get","observations/{observationDbId}")],
        "resources": [(PhenotypingObservations,"/observations"),
                      (PhenotypingObservationsId,"/observations/<observationDbId>")]
    },
    "observationunits": {
        "namespace": ns_api_phenotyping.name,
        "acceptedVersions": ["2.1"],
        "additionalVersions": ["2.0"],
        "requiredServices": [("get","observationunits")],
        "optionalServices": [("get","observationunits/{observationunitDbId}")],
        "resources": [(PhenotypingObservationUnits,"/observationunits"),
                      (PhenotypingObservationUnitsId,"/observationunits/<observationUnitDbId>")]
    },
    "ontologies": {
        "namespace": ns_api_phenotyping.name,
        "acceptedVersions": ["2.1"],
        "additionalVersions": ["2.0"],
        "requiredServices": [("get","ontologies")],
        "optionalServices": [("get","ontologies/{ontologyDbId}")],
        "resources": [(PhenotypingOntologies,"/ontologies"),
                      (PhenotypingOntologiesId,"/ontologies/<ontologyDbId>")]
    },
    "scales": {
        "namespace": ns_api_phenotyping.name,
        "acceptedVersions": ["2.1"],
        "additionalVersions": ["2.0"],
        "requiredServices": [("get","scales")],
        "optionalServices": [("get","scales/{scaleDbId}")],
        "resources": [(PhenotypingScales,"/scales"),
                      (PhenotypingScalesId,"/scales/<scaleDbId>")]
    },
    "traits": {
        "namespace": ns_api_phenotyping.name,
        "acceptedVersions": ["2.1"],
        "additionalVersions": ["2.0"],
        "requiredServices": [("get","traits")],
        "optionalServices": [("get","traits/{traitDbId}")],
        "resources": [(PhenotypingTraits,"/traits"),
                      (PhenotypingTraitsId,"/traits/<traitDbId>")]
    },
    "variables": {
        "namespace": ns_api_phenotyping.name,
        "acceptedVersions": ["2.1"],
        "additionalVersions": ["2.0"],
        "requiredServices": [("get","variables")],
        "optionalServices": [("get","variables/{observationVariableDbId}")],
        "resources": [(PhenotypingVariables,"/variables"),
                      (PhenotypingVariablesId,"/variables/<observationVariableDbId>")]
    }
}

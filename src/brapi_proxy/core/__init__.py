from flask_restx import Namespace

ns_api_core = Namespace("core",
    description="The BrAPI-Core module contains high level entities used for organization and management.", 
    path="/")

from .core_serverinfo import CoreServerinfo
from .core_commoncropnames import CoreCommoncropnames
from .core_studies import CoreStudies
from .core_studies import CoreStudiesId
from .core_trials import CoreTrials
from .core_trials import CoreTrialsId
from .core_programs import CorePrograms
from .core_programs import CoreProgramsId
from .core_locations import CoreLocations
from .core_locations import CoreLocationsId
from .core_people import CorePeople
from .core_people import CorePeopleId
from .core_seasons import CoreSeasons
from .core_seasons import CoreSeasonsId
from .core_lists import CoreLists
from .core_lists import CoreListsId

# <callName> : {
#     "namespace": <identifier>,
#     "identifier": <identifier>,
#     "acceptedVersions": [<version>,<version>,...],
#     "additionalVersions": [<version>,<version>,...],
#     "requiredServices": [(<method>,<service>),...],
#     "optionalServices": [(<method>,<service>),...],
#     "resources": [(<Resource>,<location>),...]
# }

calls_api_core = {
    "serverinfo": {
        "namespace": ns_api_core.name,
        "acceptedVersions": ["2.1","2.0"],
        "requiredServices": [("get","serverinfo")],
        "resources": [(CoreServerinfo,"/serverinfo")]
    },
    "commoncropnames": {
        "namespace": ns_api_core.name,
        "acceptedVersions": ["2.1","2.0"],
        "requiredServices": [("get","commoncropnames")],
        "resources": [(CoreCommoncropnames,"/commoncropnames")]
    },
    "studies": {
        "namespace": ns_api_core.name,
        "identifier": "studyDbId",
        "acceptedVersions": ["2.1"],
        "requiredServices": [("get","studies")],
        "optionalServices": [("get","studies/{studyDbId}")],
        "resources": [(CoreStudies,"/studies"),
                      (CoreStudiesId,"/studies/<studyDbId>")]
    },
    "trials": {
        "namespace": ns_api_core.name,
        "identifier": "trialDbId",
        "acceptedVersions": ["2.1"],
        "requiredServices": [("get","trials")],
        "optionalServices": [("get","trials/{trialDbId}")],
        "resources": [(CoreTrials,"/trials"),
                      (CoreTrialsId,"/trials/<trialDbId>")]
    },
    "programs": {
        "namespace": ns_api_core.name,
        "identifier": "programDbId",
        "acceptedVersions": ["2.1"],
        "requiredServices": [("get","programs")],
        "optionalServices": [("get","programs/{programDbId}")],
        "resources": [(CorePrograms,"/programs"),
                      (CoreProgramsId,"/programs/<programDbId>")]
    },
    "locations": {
        "namespace": ns_api_core.name,
        "identifier": "locationDbId",
        "acceptedVersions": ["2.1"],
        "requiredServices": [("get","locations")],
        "optionalServices": [("get","locations/{locationDbId}")],
        "resources": [(CoreLocations,"/locations"),
                      (CoreLocationsId,"/locations/<locationDbId>")]
    },
    "people": {
        "namespace": ns_api_core.name,
        "identifier": "personDbId",
        "acceptedVersions": ["2.1"],
        "requiredServices": [("get","people")],
        "optionalServices": [("get","people/{personDbId}")],
        "resources": [(CorePeople,"/people"),
                      (CorePeopleId,"/people/<personDbId>")]
    },
    "seasons": {
        "namespace": ns_api_core.name,
        "identifier": "seasonDbId",
        "acceptedVersions": ["2.1"],
        "requiredServices": [("get","seasons")],
        "optionalServices": [("get","seasons/{seasonDbId}")],
        "resources": [(CoreSeasons,"/seasons"),
                      (CoreSeasonsId,"/seasons/<seasonDbId>")]
    },
    "lists": {
        "namespace": ns_api_core.name,
        "identifier": "seasonDbId",
        "acceptedVersions": ["2.1"],
        "requiredServices": [("get","lists"),("get","lists/{listDbId}")],
        "resources": [(CoreLists,"/lists"),
                      (CoreListsId,"/lists/<listDbId>")]
    }
}

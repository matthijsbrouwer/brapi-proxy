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

# callName: [
#    <callIdentifierName>,
#    [<requiredService>,...],
#    [<optionalService>,...],
#    [[<resourceClass,<location>],...]
#]
    
calls_api_core = {
    "serverinfo": (None,[],[],[(CoreServerinfo,"/serverinfo")]),
    "commoncropnames": (None,[("get","commoncropnames")],[],
                        [(CoreCommoncropnames,"/commoncropnames")]),
    "studies": ("studyDbId",[("get","studies")],[("get","studies/{studyDbId}")],
                [(CoreStudies,"/studies"),
                (CoreStudiesId,"/studies/<studyDbId>")]),
    "trials": ("trialDbId",[("get","trials")],[("get","trials/{trialDbId}")],
               [(CoreTrials,"/trials"),
                (CoreTrialsId,"/trials/<trialDbId>")]),
    "programs": ("programDbId",[("get","programs")],[("get","programs/{programDbId}")],
                 [(CorePrograms,"/programs"),
                (CoreProgramsId,"/programs/<programDbId>")]),
    "locations": ("locationDbId",[("get","locations")],[("get","locations/{locationDbId}")],
                  [(CoreLocations,"/locations"),
                (CoreLocationsId,"/locations/<locationDbId>")]),
    "people": ("personDbId",[("get","people")],[("get","people/{personDbId}")],
               [(CorePeople,"/people"),
                (CorePeopleId,"/people/<personDbId>")]),
    "seasons": ("seasonDbId",[("get","seasons")],[("get","seasons/{seasonDbId}")],
                [(CoreSeasons,"/seasons"),
                (CoreSeasonsId,"/seasons/<seasonDbId>")]),
    "lists": ("listDbId",[("get","lists")],[("post","lists"),("get","lists/{listDbId}")],
              [(CoreLists,"/lists"),
                (CoreListsId,"/lists/<listDbId>")]),
}

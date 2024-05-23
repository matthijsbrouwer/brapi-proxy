from flask_restx import Namespace

ns_api_core = Namespace("core",
    description="The BrAPI-Core module contains high level entities used for organization and management.", 
    path="/")

from .core_serverinfo import CoreServerinfo
from .core_commoncropnames import CoreCommoncropnames
from .core_studies import CoreStudies
from .core_studies import CoreStudiesId

calls_api_core = {
    "serverinfo": [(CoreServerinfo,"/serverinfo")],
    "commoncropnames": [(CoreCommoncropnames,"/commoncropnames")],
    "studies": [(CoreStudies,"/studies"),
                (CoreStudiesId,"/studies/<studyDbId>")],
}

from flask_restx import Namespace

ns_api_core = Namespace("core",
    description="The BrAPI-Core module contains high level entities used for organization and management.", 
    path="/")

from service.core.core_serverinfo import CoreServerinfo
from service.core.core_commoncropnames import CoreCommoncropnames
from service.core.core_studies import CoreStudies
from service.core.core_studies import CoreStudiesId

calls_api_core = {
    "serverinfo": [(CoreServerinfo,"/serverinfo")],
    "commoncropnames": [(CoreCommoncropnames,"/commoncropnames")],
    "studies": [(CoreStudies,"/studies"),
                (CoreStudiesId,"/studies/<studyDbId>")],
}

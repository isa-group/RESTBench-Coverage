# config.py
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict

SCRIPT_DIR = Path(__file__).parent.resolve()
ROOT_DIR = SCRIPT_DIR.parent.resolve()


class JdkVersion(Enum):
    JAVA_8 = os.getenv("JDK_8") or "/usr/lib/jvm/java-8-openjdk-amd64"
    JAVA_11 = os.getenv("JDK_11") or "/usr/lib/jvm/java-11-openjdk-amd64"
    JAVA_17 = os.getenv("JDK_17") or "/usr/lib/jvm/java-17-openjdk-amd64"
    IND = "ind"

    @property
    def home(self) -> str:
        return self.value


class BuildTool(Enum):
    MAVEN = "mvn"
    GRADLE = "gradle"


@dataclass(frozen=True)
class ApiConfig:
    name: str
    jdk_version: JdkVersion
    build_tool: BuildTool
    module_name: str
    preparation_class: str
    endpoint_test_class: str
    is_ind: bool = False

    def mt_abs_path(self) -> Path:
        if self.is_ind:
            return ROOT_DIR / "ind" / self.module_name
        jdk_home = f"jdk_{self.jdk_version.name.split('_', 1)[1].lower()}_{self.build_tool.name.lower()}"
        return ROOT_DIR / jdk_home / "mt" / self.module_name

    def sut_abs_path(self) -> Path:
        if self.is_ind:
            return None
        jdk_home = f"jdk_{self.jdk_version.name.split('_', 1)[1].lower()}_{self.build_tool.name.lower()}"
        return ROOT_DIR / jdk_home / "sut" / self.module_name

    def maven_module_selector(self) -> str:
        return self.module_name if self.is_ind else f"mt/{self.module_name}"

    def work_dir(self) -> Path:
        if self.is_ind:
            return ROOT_DIR / "ind"
        jdk_short = self.jdk_version.name.split("_", 1)[1].lower()
        tool_dir = f"jdk_{jdk_short}_{self.build_tool.name.lower()}"
        return ROOT_DIR / tool_dir


@dataclass(frozen=True)
class OperationConfig:
    id: str
    api: ApiConfig
    operation_path: str
    http_method: str
    pict_model_file: str
    oas: str
    remove_json_paths: str = ""
    remove_json_nodes: str = ""
    remove_headers: str = ""
    csv_mapper: Optional[str] = None
    mvn_profile: str = ""
    formal_name: str = ""

    def resolved_model(self) -> str:
        return str(ROOT_DIR / "pictModels" / Path(self.pict_model_file))

    def resolved_oas(self) -> str:
        return str(ROOT_DIR / "processedSpecs" / Path(self.oas))


OPS_MAP: Dict[ApiConfig, List[OperationConfig]] = {}

# Scout API: POST /v1/activities, PUT /v1/activities/{id}
scout_api = ApiConfig(
    name="ScoutAPI",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="scout-api",
    preparation_class="ScoutAPIPreparationTest",
    endpoint_test_class="ScoutAPIEndpointTest"
)

OPS_MAP[scout_api] = [
    OperationConfig(
        id="postActivities",
        api=scout_api,
        operation_path="/api/v1/activities",
        http_method="POST",
        pict_model_file="scout-api/postActivities.model",
        oas="scout-api/post-activities.json",
        remove_json_nodes="date_created",
        remove_json_paths="",
        csv_mapper="mt.se.devscout.scoutapi.mapper.PostActivitiesMapper",
        mvn_profile="post-activities",
        formal_name="ScoutAPI-CreateActivities"
    ),
]
# Project Tracking System API: POST /app/api/assignments, POST /app/api/employees
pts = ApiConfig(
    name="ProjectTrackingSystem",
    jdk_version=JdkVersion.JAVA_11,
    build_tool=BuildTool.MAVEN,
    module_name="project-tracking-system",
    preparation_class="ProjectTrackingSystemPreparationTest",
    endpoint_test_class="ProjectTrackingSystemEndpointTest"
)
OPS_MAP[pts] = [
    OperationConfig(
        id="postAssignments",
        api=pts,
        operation_path="/app/api/assignments",
        http_method="POST",
        pict_model_file="project-tracking-system/postAssignments.model",
        oas="project-tracking-system/postAssignments.yaml",
        remove_json_nodes="",
        remove_json_paths="timestamp",
        csv_mapper="mt.com.pfa.mapper.PostAssignmentMapper",
        mvn_profile="post-assignments",
        formal_name="ProjectSwagger-AssignTask"
    ),
]
# User Management: POST /users, PUT /users/{id}
user_mgmt = ApiConfig(
    name="UserManagement",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="user-management",
    preparation_class="UserManagementPreparationTest",
    endpoint_test_class="UserManagementEndpointTest"
)
OPS_MAP[user_mgmt] = [
    OperationConfig(
        id="putUsersId",
        api=user_mgmt,
        operation_path="/users/{id}",
        http_method="PUT",
        pict_model_file="user-management/put-usersId.model",
        oas="user-management/put-userId.yaml",
        remove_json_nodes="",
        remove_json_paths="creationDt,updatedDt,timestamp",
        csv_mapper="mt.com.giassi.microservice.demo2.mapper.PutUsersIdMapper",
        mvn_profile="put-usersId",
        formal_name="UserOpenAPI-UpdateUser"
    )
]

# Market API: POST /register
market_api = ApiConfig(
    name="Market",
    jdk_version=JdkVersion.JAVA_11,
    build_tool=BuildTool.MAVEN,
    module_name="market",
    preparation_class="MarketPreparationTest",
    endpoint_test_class="MarketEndpointTest"
)
OPS_MAP[market_api] = [
    OperationConfig(
        id="postRegister",
        api=market_api,
        operation_path="/register",
        http_method="POST",
        pict_model_file="market/post-register.model",
        oas="market/post-register.json",
        remove_json_nodes="href",
        remove_json_paths="",
        remove_headers="set-cookie",
        csv_mapper="mt.market.mapper.PostRegisterMapper",
        mvn_profile="post-register",
        formal_name="Market-RegisterUser"
    ),
]

# Person Controller: POST /person
person_controller = ApiConfig(
    name="PersonController",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="person-controller",
    preparation_class="PersonControllerPreparationTest",
    endpoint_test_class="PersonControllerEndpointTest"
)
OPS_MAP[person_controller] = [
    OperationConfig(
        id="postPerson",
        api=person_controller,
        operation_path="/api/person",
        http_method="POST",
        pict_model_file="person/post-person.model",
        oas="person/post-person.yaml",
        remove_json_nodes="",
        remove_json_paths="id,createdAt,timestamp",
        csv_mapper="mt.com.mongodb.starter.mapper.PostPersonMapper",
        mvn_profile="post-person",
        formal_name="PersonOpenAPI-CreatePerson"
    )
]

# ProxyPrint API: POST /request/register
proxy_print = ApiConfig(
    name="ProxyPrint",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="proxyprint",
    preparation_class="ProxyprintPreparationTest",
    endpoint_test_class="ProxyprintEndpointTest")
OPS_MAP[proxy_print] = [
    OperationConfig(
        id="postRequestRegister",
        api=proxy_print,
        operation_path="/request/register",
        http_method="POST",
        pict_model_file="proxyprint/post-requestRegister.model",
        oas="proxyprint/post-requestRegister.json",
        remove_json_nodes="",
        remove_json_paths="pShopDateRequest,timestamp",
        csv_mapper="mt.io.github.proxyprint.kitchen.mapper.PostRequestRegisterMapper",
        mvn_profile="post-request-register",
        formal_name="ProxyPrint-RegisterRequest"
    )
]

# Language Tool API: POST /v2/check
language_tool = ApiConfig(
    name="LanguageTool",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="languagetool",
    preparation_class="LanguagetoolPreparationTest",
    endpoint_test_class="LanguagetoolEndpointTest"
)
OPS_MAP[language_tool] = [
    OperationConfig(
        id="postCheck",
        api=language_tool,
        operation_path="/check",
        http_method="POST",
        pict_model_file="languagetool/post-check.model",
        oas="languagetool/post-check.json",
        remove_json_nodes="",
        remove_json_paths="",
        csv_mapper="mt.org.languagetool.server.mapper.PostCheckCsvRowMapper",
        mvn_profile="post-check",
        formal_name="LanguageTool-CheckText"
    )
]

genome_nexus = ApiConfig(
    name="GenomeNexus",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="genome-nexus",
    preparation_class="GenomeNexusPreparationTest",
    endpoint_test_class="GenomeNexusEndpointTest"
)
OPS_MAP[genome_nexus] = [
    OperationConfig(
        id="postAnnotation",
        api=genome_nexus,
        operation_path="/annotation",
        http_method="POST",
        pict_model_file="genome-nexus/postAnnotation.model",
        oas="genome-nexus/post-annotation.json",
        remove_json_nodes="colocatedVariants",
        remove_json_paths="",
        csv_mapper="mt.org.cbioportal.genome_nexus.web.mapper.PostAnnotationMapper",
        mvn_profile="post-annotations",
        formal_name="GenomeNexus-Annotate"
    ),
]
# Catwatch API: GET /projects, GET /contributors
catwatch = ApiConfig(
    name="Catwatch",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="catwatch",
    preparation_class="CatwatchPreparationTest",
    endpoint_test_class="CatwatchEndpointTest"
)
OPS_MAP[catwatch] = [
    OperationConfig(
        id="getProjects",
        api=catwatch,
        operation_path="/projects",
        http_method="GET",
        pict_model_file="catwatch/get-project.model",
        oas="catwatch/get-projects.json",
        remove_json_nodes="snapshotDate",
        remove_json_paths="timestamp",
        csv_mapper="mt.org.zalando.catwatch.backend.mapper.GetProjectMapper",
        mvn_profile="get-projects",
        formal_name="CatWatch-ListProjects"
    ),
]
# gestaohospital API: POST /hospital
gestaohospital = ApiConfig(
    name="Gestaohospital",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="gestaohospital",
    preparation_class="GestaohosiptalPreparationTest",
    endpoint_test_class="GestaohosiptalEndpointTest"
)
OPS_MAP[gestaohospital] = [
    OperationConfig(
        id="postHospital",
        api=gestaohospital,
        operation_path="/v1/hospitais/",
        http_method="POST",
        pict_model_file="gestaohosiptal/post-hospital.model",
        oas="gestaohospital/post-hospital.json",
        remove_json_nodes="",
        remove_json_paths="id,timestamp",
        csv_mapper="mt.br.com.codenation.hospital.mapper.PostHospitalMapper",
        mvn_profile="post-hospitals",
        formal_name="Gestaohospital-CreateHospital"
    )
]


# ──────────────────────────────────────────────────────────────────────────────
# Industrial APIs 
# ──────────────────────────────────────────────────────────────────────────────
stripe_api = ApiConfig(
    name="Stripe",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="stripe",
    preparation_class="StripePreparationTest",
    endpoint_test_class="StripeEndpointTest",
    is_ind=True
)
OPS_MAP[stripe_api] = [
    OperationConfig(
        id="postV1Products",
        api=stripe_api,
        operation_path="/v1/products",
        http_method="POST",
        pict_model_file="stripe/post-products.model",
        oas="stripe/post-products.yaml",
        remove_json_paths="id,created,default_price,name,updated,error.request_log_url",
        remove_headers="original-request,request-id,idempotency-key",
        csv_mapper="mt.stripe.mapper.PostProductMapper",
        formal_name="Stripe-CreateProduct"
    )
]

foursquare_api = ApiConfig(
    name="Foursquare",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="foursquare",
    preparation_class="FourSquarePreparationTest",
    endpoint_test_class="FourSquareEndpointTest",
    is_ind=True
)
OPS_MAP[foursquare_api] = [
    OperationConfig(
        id="getPlacesSearch",
        api=foursquare_api,
        operation_path="/places/search",
        http_method="GET",
        pict_model_file="foursquare/get-places.model",
        oas="foursquare/get-places.yaml",
        remove_headers="x-fsq-request-id,x-timer,access-control-allow-origin",
        csv_mapper="mt.foursquare.mapper.GetSearchMapper",
        formal_name="Foursquare-SearchPlaces"
    )
]

yelp_api = ApiConfig(
    name="Yelp",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="yelp",
    preparation_class="YelpPreparationTest",
    endpoint_test_class="YelpEndpointTest",
    is_ind=True
)
OPS_MAP[yelp_api] = [
    OperationConfig(
        id="getBusinessesSearch",
        api=yelp_api,
        operation_path="/businesses/search",
        http_method="GET",
        pict_model_file="yelp/get-search.model",
        oas="yelp/get-search.yaml",
        remove_headers="x-zipkin-id,x-proxied,x-served-by,x-routing-service,x-extlb,x-cache,x-cache-hits,via,x-b3-sampled,alt-svc,ratelimit-remaining,ratelimit-resettime,set-cookie,accept-ranges,date",
        csv_mapper="mt.yelp.mapper.GetSearchMapper",
        formal_name="Yelp-SearchBusinesses"
    )
]

amadeus_api = ApiConfig(
    name="AmadeusHotel",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="amadeus",
    preparation_class="AmadeusHotelPreparationTest",
    endpoint_test_class="AmadeusHotelEndpointTest",
    is_ind=True
)
OPS_MAP[amadeus_api] = [
    OperationConfig(
        id="getHotelOffers",
        api=amadeus_api,
        operation_path="/v3/shopping/hotel-offers",
        http_method="GET",
        pict_model_file="amadeus/hotel.model",
        oas="amadeus/get-hotelOffers.yaml",
        remove_json_paths="data[].offers[].id,data[].offers[].self",
        remove_headers="ama-request-id,ama-gateway-request-id",
        csv_mapper="mt.amadeus.mapper.HotelOffersMapper",
        formal_name="AmadeusHotel-GetOffers"
    )
]

youtube_api = ApiConfig(
    name="YouTube",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="youtube-ind",
    preparation_class="YoutubePreparationTest",
    endpoint_test_class="YoutubeEndpointTest",
    is_ind=True
)
OPS_MAP[youtube_api] = [
    OperationConfig(
        id="getVideos",
        api=youtube_api,
        operation_path="/youtube/v3/videos",
        http_method="GET",
        pict_model_file="youtube/get-videos.model",
        oas="youtube/get-videos.yaml",
        csv_mapper="mt.youtube.mapper.GetVideosCsvMapper",
        formal_name="YouTube-GetVideos"
    )
]

dhl_api = ApiConfig(
    name="DHL",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="dhl",
    preparation_class="DHLPreparationTest",
    endpoint_test_class="DHLEndpointTest",
    is_ind=True
)
OPS_MAP[dhl_api] = [
    OperationConfig(
        id="getFindByAddress",
        api=dhl_api,
        operation_path="/location-finder/v1/find-by-address",
        http_method="GET",
        pict_model_file="dhl/get-location.model",
        oas="dhl/get-location.yaml",
        csv_mapper="mt.dhl.mapper.FindLocationMapper",
        formal_name="DHL-FindByAddress"
    )
]

fdic_api = ApiConfig(
    name="FDIC",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="fdic",
    preparation_class="FDICPreparationTest",
    endpoint_test_class="FDICEndpointTest",
    is_ind=True
)
OPS_MAP[fdic_api] = [
    OperationConfig(
        id="getInstitutions",
        api=fdic_api,
        operation_path="/institutions",
        http_method="GET",
        pict_model_file="fdic/get-institutions.model",
        oas="fdic/get-institutions.yaml",
        csv_mapper="mt.fdic.mapper.GetInstitutionsMapper",
        formal_name="FDIC-ListInstitutions"
    )
]

ohsome_api = ApiConfig(
    name="Ohsome",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="ohsome",
    preparation_class="OhsomePreparationTest",
    endpoint_test_class="OhsomeEndpointTest",
    is_ind=True
)
OPS_MAP[ohsome_api] = [
    OperationConfig(
        id="getElementsAggregation",
        api=ohsome_api,
        operation_path="/elements/{aggregation}",
        http_method="GET",
        pict_model_file="ohsome/get-elements-agg.model",
        oas="ohsome/get-elements.yaml",
        csv_mapper="mt.ohsome.mapper.GetElementAgg",
        formal_name="Ohsome-GetElements"
    )
]

deutschebahn_api = ApiConfig(
    name="Deutschebahn",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="deutschebahn",
    preparation_class="DeutscheBahnPreparationTest",
    endpoint_test_class="DeutscheBahnEndpointTest",
    is_ind=True
)
OPS_MAP[deutschebahn_api] = [
    OperationConfig(
        id="getStations",
        api=deutschebahn_api,
        operation_path="/stations",
        http_method="GET",
        pict_model_file="dustschebahn/get-station.model",
        oas="deutschebahn/get-stations.yaml",
        csv_mapper="mt.deutschebahn.mapper.GetStationMapper",
        formal_name="DeutscheBahn-ListStations"
    )
]

itunes_api = ApiConfig(
    name="iTunes",
    jdk_version=JdkVersion.JAVA_8,
    build_tool=BuildTool.MAVEN,
    module_name="itunes",
    preparation_class="ITunesPreparationTest",
    endpoint_test_class="ITunesEndpointTest",
    is_ind=True
)
OPS_MAP[itunes_api] = [
    OperationConfig(
        id="getSearch",
        api=itunes_api,
        operation_path="/search",
        http_method="GET",
        pict_model_file="itunes/get-search.model",
        oas="ITunes/get-search.yaml",
        csv_mapper="mt.itunes.mapper.GetSearchMapper",
        formal_name="iTunes-Search"
    )
]

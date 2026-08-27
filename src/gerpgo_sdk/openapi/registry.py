from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any

from gerpgo_sdk.common.errors import ValidationError


@dataclass(frozen=True, slots=True)
class FieldSpec:
    type_name: str
    required: bool = False


@dataclass(frozen=True, slots=True)
class EndpointSpec:
    key: str
    official_name: str
    document_id: int
    method: str
    path: str
    minimum_interval_seconds: float
    fields: MappingProxyType[str, FieldSpec]
    max_page_size: int | None = None
    read_only: bool = True

    @property
    def documentation_url(self) -> str:
        return f"https://open.gerpgo.com/document?id={self.document_id}"

    def validate_payload(self, payload: dict[str, Any]) -> None:
        unknown = sorted(set(payload) - set(self.fields))
        if unknown:
            raise ValidationError(
                f"Unsupported fields for {self.official_name}: {', '.join(unknown)}",
                details={"endpoint": self.key, "unsupported_fields": unknown},
            )
        missing = sorted(
            name
            for name, field in self.fields.items()
            if field.required and (name not in payload or payload[name] in (None, "", []))
        )
        if missing:
            raise ValidationError(
                f"Missing required fields for {self.official_name}: {', '.join(missing)}",
                details={"endpoint": self.key, "missing_fields": missing},
            )
        for name, value in payload.items():
            if value is None:
                continue
            self._validate_type(name, value, self.fields[name].type_name)
        if self.key == "product-list":
            self._validate_product_pagination(payload)
        self._validate_positive_pagination(payload)
        if self.max_page_size is not None:
            page_size = payload.get("pagesize")
            if page_size is None and isinstance(payload.get("pageInfo"), dict):
                page_size = payload["pageInfo"].get("pagesize")
            if isinstance(page_size, int) and page_size > self.max_page_size:
                raise ValidationError(
                    f"pagesize cannot exceed {self.max_page_size} for {self.official_name}."
                )

    @staticmethod
    def _validate_type(name: str, value: Any, type_name: str) -> None:
        valid = True
        if type_name.startswith("array"):
            valid = isinstance(value, list)
            if valid:
                element_type = type_name.removeprefix("array<").removesuffix(">")
                for index, item in enumerate(value):
                    EndpointSpec._validate_type(f"{name}[{index}]", item, element_type)
        elif type_name == "object":
            valid = isinstance(value, dict)
        elif type_name in {"int", "long"}:
            valid = isinstance(value, int) and not isinstance(value, bool)
        elif type_name == "number":
            valid = isinstance(value, int | float) and not isinstance(value, bool)
        elif type_name == "boolean":
            valid = isinstance(value, bool)
        elif type_name in {"string", "date", "datetime"}:
            valid = isinstance(value, str)
        if not valid:
            raise ValidationError(f"Field '{name}' must have type {type_name}.")
        if type_name == "date" and isinstance(value, str):
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError as exc:
                raise ValidationError(f"Field '{name}' must use YYYY-MM-DD.") from exc
        if type_name == "datetime" and isinstance(value, str):
            try:
                datetime.fromisoformat(value)
            except ValueError as exc:
                raise ValidationError(f"Field '{name}' must use an ISO date-time value.") from exc

    @staticmethod
    def _validate_product_pagination(payload: dict[str, Any]) -> None:
        direct = "page" in payload or "pagesize" in payload
        nested = "pageInfo" in payload
        if direct and nested:
            raise ValidationError("Use direct pagination or pageInfo, not both.")
        if not direct and not nested:
            raise ValidationError("查询产品列表 requires direct pagination or pageInfo.")
        if direct:
            if not isinstance(payload.get("page"), int) or not isinstance(
                payload.get("pagesize"), int
            ):
                raise ValidationError("Direct pagination requires integer page and pagesize.")
            return
        page_info = payload.get("pageInfo")
        if not isinstance(page_info, dict) or set(page_info) != {"page", "pagesize"}:
            raise ValidationError("pageInfo must contain only integer page and pagesize fields.")
        if not isinstance(page_info["page"], int) or not isinstance(page_info["pagesize"], int):
            raise ValidationError("pageInfo page and pagesize must be integers.")

    @staticmethod
    def _validate_positive_pagination(payload: dict[str, Any]) -> None:
        page_info = payload.get("pageInfo")
        pagination: dict[str, Any] = page_info if isinstance(page_info, dict) else payload
        for name in ("page", "pagesize"):
            value = pagination.get(name)
            if isinstance(value, int | float) and not isinstance(value, bool) and value <= 0:
                raise ValidationError(f"Field '{name}' must be greater than zero.")


def _fields(required: str, optional: str = "") -> MappingProxyType[str, FieldSpec]:
    result: dict[str, FieldSpec] = {}
    for declaration, is_required in ((required, True), (optional, False)):
        for item in filter(None, (part.strip() for part in declaration.split(","))):
            name, type_name = item.split(":", 1)
            result[name] = FieldSpec(type_name, is_required)
    return MappingProxyType(result)


ENDPOINTS: MappingProxyType[str, EndpointSpec] = MappingProxyType(
    {
        "product-list": EndpointSpec(
            "product-list",
            "查询产品列表",
            53,
            "POST",
            "/purchase/goods/product/page",
            0.5,
            _fields(
                "",
                "brandList:array<string>,categoryList:array<string>,pageInfo:object,"
                "page:int,pagesize:int,skuList:array<string>,platformMskuList:array<string>,"
                "mskuList:array<string>,state:int,dateType:int,startDate:date,endDate:date",
            ),
            100,
        ),
        "product-inventory": EndpointSpec(
            "product-inventory",
            "查询产品库存",
            15,
            "POST",
            "/purchase/store/inventory/page",
            0.5,
            _fields(
                "page:int,pagesize:int",
                "productState:int,productTypeList:array<int>,state:int,warehouseIds:array<long>,"
                "productManagerAccountIdList:array<int>,sellingManagerIdList:array<long>,"
                "skuList:array<string>,asinList:array<string>,mskuList:array<string>,"
                "filterQuantity:boolean",
            ),
        ),
        "sales-performance": EndpointSpec(
            "sales-performance",
            "销售表现",
            3375,
            "POST",
            "/operation/sts/salesAnalysis/page",
            5.0,
            _fields(
                "groupByType:string,showCurrencyType:string,beginDate:date,endDate:date,"
                "page:number,pagesize:number",
                "viewType:string,sku:string,variationAsin:string,productName:string,asin:string,"
                "msku:string",
            ),
        ),
        "search-term-performance": EndpointSpec(
            "search-term-performance",
            "搜索词表现",
            100,
            "POST",
            "/operation/ads/adsKeywordAnalytical/query",
            60.0,
            _fields("page:int,pagesize:int,marketId:long,startDateData:date,endDateData:date"),
        ),
        "review": EndpointSpec(
            "review",
            "Review",
            1092,
            "POST",
            "/operation/crm/review/page",
            1.0,
            _fields(
                "page:int,pagesize:int",
                "reviewIds:array<string>,createDateBegin:date,createDateEnd:date,"
                "updateDateBegin:datetime,updateDateEnd:datetime,reviewDateBegin:date,"
                "reviewDateEnd:date,marketIds:array<long>,states:array<long>,results:array<long>,"
                "orderIds:array<string>,nameMatchType:string,asins:array<string>",
            ),
        ),
        "buyer-voice": EndpointSpec(
            "buyer-voice",
            "买家之声列表",
            1014,
            "POST",
            "/operation/crm/customerVoice/page",
            1.0,
            _fields(
                "page:int,pagesize:int",
                "pcxHealth:string,marketIds:array<int>,productName:string,skus:array<string>,"
                "mskus:array<string>,asins:array<string>",
            ),
        ),
        "profit-analysis-v2": EndpointSpec(
            "profit-analysis-v2",
            "查询财务利润分析V2",
            2256,
            "POST",
            "/finance/sts/financialAnalysis/page/V2",
            10.0,
            _fields(
                "queryType:string,costValues:int,page:int,pagesize:int,currency:string,dateType:int",
                "monthDate:string,startDate:date,endDate:date,marketIds:array<int>,"
                "categoryIds:array<string>,brands:array<string>,decimalPlaces:int,"
                "footerExpandDetails:boolean,platformCodes:array<string>,"
                "queryMskuList:array<string>,skuList:array<string>,asinList:array<string>",
            ),
        ),
        "keyword-performance": EndpointSpec(
            "keyword-performance",
            "关键词表现",
            99,
            "POST",
            "/operation/ads/adsKeywordAnalytical/page",
            60.0,
            _fields("page:int,pagesize:int,marketId:long,startDateData:date,endDateData:date"),
        ),
        "product-performance": EndpointSpec(
            "product-performance",
            "产品表现",
            131,
            "POST",
            "/operation/sts/productAnalyzeMultiIndex/page",
            60.0,
            _fields(
                "showCurrencyType:string,beginDate:string,endDate:string,page:int,pagesize:int"
            ),
        ),
        "listing-performance": EndpointSpec(
            "listing-performance",
            "商品表现",
            140,
            "POST",
            "/operation/sts/listingAnalyzeMultiIndex/page",
            5.0,
            _fields(
                "groupByType:string,showCurrencyType:string,beginDate:date,endDate:date,"
                "isShowTotal:boolean,page:int,pagesize:int",
                "marketList:array<int>,sku:string,asin:string,asinList:array<string>,"
                "msku:string,mskuList:array<string>",
            ),
        ),
        "asin-traffic-statistics": EndpointSpec(
            "asin-traffic-statistics",
            "流量统计-ASIN",
            122,
            "POST",
            "/operation/sts/traffic/page",
            60.0,
            _fields(
                "currency:string,beginDate:string,endDate:string,page:int,pagesize:int,viewType:string",
                "marketList:array<int>",
            ),
        ),
        "asin-traffic-data": EndpointSpec(
            "asin-traffic-data",
            "流量数据-ASIN",
            1018,
            "POST",
            "/operation/sts/trafficAnalysis/page",
            60.0,
            _fields(
                "currency:string,beginDate:date,endDate:date,page:int,pagesize:int",
                "marketList:array<int>",
            ),
        ),
    }
)


def get_endpoint(key: str) -> EndpointSpec:
    try:
        return ENDPOINTS[key]
    except KeyError as exc:
        raise ValidationError(f"Unsupported OpenAPI endpoint key: {key}") from exc

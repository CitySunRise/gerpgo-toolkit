from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Literal

from gerpgo_sdk.common.errors import ValidationError

EnumStatus = Literal["documented", "official_not_published", "not_applicable"]
RequestBodyMode = Literal["json", "none", "empty_object"]
EndpointGroup = Literal["business", "catalog"]


@dataclass(frozen=True, slots=True)
class EnumValue:
    value: str | int
    label: str

    def to_dict(self) -> dict[str, str | int]:
        return {"value": self.value, "label": self.label}


@dataclass(frozen=True, slots=True)
class FieldSpec:
    type_name: str
    required: bool = False
    description: str = ""
    enum_values: tuple[EnumValue, ...] = ()
    enum_status: EnumStatus = "not_applicable"
    enum_document_id: int | None = None
    dynamic_identifier: bool = False
    date_format: str | None = None
    default_value: Any = None
    default_documented: bool = False
    minimum: int | float | None = None
    maximum: int | float | None = None
    max_items: int | None = None
    recommended_maximum: int | float | None = None
    recommended_max_items: int | None = None
    constraints: tuple[str, ...] = ()
    children: tuple[tuple[str, FieldSpec], ...] = ()

    def to_contract(self, name: str, documentation_id: int) -> dict[str, Any]:
        return {
            "name": name,
            "type": self.type_name,
            "required": self.required,
            "description": self.description,
            "enum_values": [item.to_dict() for item in self.enum_values],
            "enum_status": self.enum_status,
            "enum_documentation_id": self.enum_document_id,
            "dynamic_identifier": self.dynamic_identifier,
            "date_format": self.date_format,
            "default": self.default_value if self.default_documented else None,
            "default_documented": self.default_documented,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "max_items": self.max_items,
            "recommended_maximum": self.recommended_maximum,
            "recommended_max_items": self.recommended_max_items,
            "constraints": list(self.constraints),
            "documentation_id": documentation_id,
            "children": [
                child.to_contract(child_name, documentation_id)
                for child_name, child in self.children
            ],
        }

    def help_text(self) -> str:
        parts = [self.description.rstrip(".")]
        if self.required:
            parts.append("required unless supplied by --input")
        if self.enum_values:
            help_values = self.enum_values
            if len(help_values) > 20:
                help_values = (help_values[-1], *help_values[:-1])
            choices = ", ".join(f"{item.value}= {item.label}" for item in help_values)
            parts.append(f"choices: {choices}")
        elif self.enum_status == "official_not_published":
            parts.append("official enum not published")
        if self.default_documented:
            parts.append(f"official default: {self.default_value}")
        if self.date_format:
            parts.append(f"format: {self.date_format}")
        if self.dynamic_identifier:
            parts.append("dynamic identifier; obtain from the user's Gerpgo account")
        return "; ".join(part for part in parts if part) + "."


@dataclass(frozen=True, slots=True)
class EndpointSpec:
    key: str
    official_name: str
    document_id: int
    method: str
    path: str
    minimum_interval_seconds: float
    fields: MappingProxyType[str, FieldSpec]
    pagination_mode: str = "direct"
    official_max_page_size: int | None = None
    official_recommended_page_size: int | None = None
    official_max_pages: int | None = None
    runtime_min_page_size: int | None = None
    runtime_max_page_size: int | None = None
    default_page_size: int | None = None
    default_max_pages: int = 100
    runtime_verified: bool = False
    runtime_verified_date: str | None = None
    runtime_verification_note: str | None = None
    combination_constraints: tuple[str, ...] = ()
    read_only: bool = True
    endpoint_group: EndpointGroup = "business"
    request_body_mode: RequestBodyMode = "json"
    response_key_fields: tuple[str, ...] = ()
    public_method_verified_date: str | None = None
    metadata_method_difference: str | None = None

    @property
    def documentation_url(self) -> str:
        return f"https://open.gerpgo.com/document?id={self.document_id}"

    def field(self, name: str) -> FieldSpec:
        try:
            return self.fields[name]
        except KeyError as exc:
            raise ValidationError(f"Unsupported field for {self.official_name}: {name}") from exc

    @property
    def supports_auto_pagination(self) -> bool:
        return (
            "page" in self.fields and "pagesize" in self.fields
        ) or "pageInfo" in self.fields

    @property
    def effective_runtime_min_page_size(self) -> int | None:
        if self.runtime_min_page_size is not None:
            return self.runtime_min_page_size
        page_size = self.fields.get("pagesize")
        return int(page_size.minimum) if page_size and page_size.minimum is not None else None

    @property
    def effective_runtime_max_page_size(self) -> int | None:
        if self.runtime_max_page_size is not None:
            return self.runtime_max_page_size
        page_size = self.fields.get("pagesize")
        return int(page_size.maximum) if page_size and page_size.maximum is not None else None

    def contract(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "official_name": self.official_name,
            "method": self.method,
            "path": self.path,
            "document_id": self.document_id,
            "documentation_url": self.documentation_url,
            "minimum_interval_seconds": self.minimum_interval_seconds,
            "read_only": self.read_only,
            "endpoint_group": self.endpoint_group,
            "request_body_mode": self.request_body_mode,
            "response_key_fields": list(self.response_key_fields),
            "public_method_verified_date": self.public_method_verified_date,
            "metadata_method_difference": self.metadata_method_difference,
            "pagination": {
                "mode": self.pagination_mode,
                "official_max_page_size": self.official_max_page_size,
                "official_recommended_page_size": self.official_recommended_page_size,
                "official_max_pages": self.official_max_pages,
                "runtime_min_page_size": self.effective_runtime_min_page_size,
                "runtime_max_page_size": self.effective_runtime_max_page_size,
                "default_page_size": self.default_page_size,
                "default_max_pages": self.default_max_pages,
                "runtime_verified": self.runtime_verified,
                "runtime_verified_date": self.runtime_verified_date,
                "runtime_verification_note": self.runtime_verification_note,
                "supports_auto_pagination": self.supports_auto_pagination,
            },
            "combination_constraints": list(self.combination_constraints),
            "fields": [
                field.to_contract(name, self.document_id) for name, field in self.fields.items()
            ],
        }

    def validate_payload(self, payload: dict[str, Any] | None) -> None:
        if self.request_body_mode == "none":
            if payload is not None:
                raise ValidationError(f"{self.official_name} must be sent without a request body.")
            return
        if payload is None:
            raise ValidationError(f"{self.official_name} requires a JSON request body.")
        if self.request_body_mode == "empty_object" and payload:
            raise ValidationError(f"{self.official_name} only accepts an empty JSON object.")
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
            if value is not None:
                self._validate_field(name, value, self.fields[name])
        if self.key == "product-list":
            self._validate_product_pagination(payload)
        self._validate_positive_pagination(payload)
        self._validate_combinations(payload)

    def _validate_field(self, name: str, value: Any, field: FieldSpec) -> None:
        self._validate_type(name, value, field.type_name)
        values = value if field.type_name.startswith("array<") else [value]
        if field.enum_values:
            allowed = {item.value for item in field.enum_values}
            invalid = [item for item in values if item not in allowed]
            if invalid:
                choices = ", ".join(f"{item.value} ({item.label})" for item in field.enum_values)
                raise ValidationError(
                    f"Invalid value for '{name}'. Allowed values: {choices}.",
                    details={
                        "endpoint": self.key,
                        "field": name,
                        "allowed_values": [item.to_dict() for item in field.enum_values],
                    },
                )
        if field.date_format and isinstance(value, str):
            self._validate_date_format(name, value, field.date_format)
        if isinstance(value, int | float) and not isinstance(value, bool):
            if field.minimum is not None and value < field.minimum:
                raise ValidationError(f"Field '{name}' must be at least {field.minimum}.")
            if field.maximum is not None and value > field.maximum:
                raise ValidationError(f"Field '{name}' cannot exceed {field.maximum}.")
        if isinstance(value, list) and field.max_items is not None and len(value) > field.max_items:
            raise ValidationError(
                f"Field '{name}' cannot contain more than {field.max_items} items."
            )
        if field.type_name == "object" and isinstance(value, dict) and field.children:
            children = dict(field.children)
            unknown_children = sorted(set(value) - set(children))
            if unknown_children:
                raise ValidationError(
                    f"Unsupported fields in '{name}': {', '.join(unknown_children)}."
                )
            missing_children = sorted(
                child_name
                for child_name, child in children.items()
                if child.required
                and (child_name not in value or value[child_name] in (None, "", []))
            )
            if missing_children:
                raise ValidationError(
                    f"Missing required fields in '{name}': {', '.join(missing_children)}."
                )
            for child_name, child_value in value.items():
                self._validate_field(f"{name}.{child_name}", child_value, children[child_name])

    @staticmethod
    def _validate_type(name: str, value: Any, type_name: str) -> None:
        valid = True
        if type_name.startswith("array<"):
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

    @staticmethod
    def _validate_date_format(name: str, value: str, date_format: str) -> None:
        formats = {
            "yyyy-MM-dd": "%Y-%m-%d",
            "yyyy-MM-dd HH:mm:ss": "%Y-%m-%d %H:%M:%S",
            "yyyy-MM": "%Y-%m",
        }
        parser_format = formats.get(date_format)
        if parser_format is None:
            raise ValidationError(f"Unsupported registered date format for '{name}'.")
        try:
            datetime.strptime(value, parser_format)
        except ValueError as exc:
            raise ValidationError(f"Field '{name}' must use {date_format}.") from exc

    @staticmethod
    def _validate_product_pagination(payload: dict[str, Any]) -> None:
        direct = "page" in payload or "pagesize" in payload
        nested = "pageInfo" in payload
        if direct and nested:
            raise ValidationError("Use direct pagination or pageInfo, not both.")
        if not direct and not nested:
            raise ValidationError("查询产品列表 requires direct pagination or pageInfo.")
        if direct and not {"page", "pagesize"}.issubset(payload):
            raise ValidationError("Direct pagination requires page and pagesize.")

    @staticmethod
    def _validate_positive_pagination(payload: dict[str, Any]) -> None:
        page_info = payload.get("pageInfo")
        pagination: dict[str, Any] = page_info if isinstance(page_info, dict) else payload
        for name in ("page", "pagesize"):
            value = pagination.get(name)
            if isinstance(value, int | float) and not isinstance(value, bool) and value <= 0:
                raise ValidationError(f"Field '{name}' must be greater than zero.")

    def _validate_combinations(self, payload: dict[str, Any]) -> None:
        if self.key in {"search-term-performance", "keyword-performance"} and payload.get(
            "startDateData"
        ) != payload.get("endDateData"):
            raise ValidationError("startDateData and endDateData must be the same date.")
        if (
            self.key == "sales-performance"
            and payload.get("groupByType") == "date"
            and not payload.get("viewType")
        ):
            raise ValidationError("viewType is required when groupByType is date.")
        if self.key == "profit-analysis-v2":
            date_type = payload.get("dateType")
            if date_type == 0 and (not payload.get("startDate") or not payload.get("endDate")):
                raise ValidationError("startDate and endDate are required when dateType is 0.")
            if date_type == 1 and not payload.get("monthDate"):
                raise ValidationError("monthDate is required when dateType is 1.")


def _enum(*items: tuple[str | int, str]) -> tuple[EnumValue, ...]:
    return tuple(EnumValue(value, label) for value, label in items)


CURRENCY_ENUM = _enum(
    ("YUAN", "原币种"),
    ("USD", "美元"),
    ("JPY", "日元"),
    ("GBP", "英镑"),
    ("EUR", "欧元"),
    ("CAD", "加元"),
    ("MXN", "墨西哥比索"),
    ("AUD", "澳大利亚元"),
    ("INR", "印度卢比"),
    ("CNY", "人民币"),
    ("AED", "阿联酋迪拉姆"),
    ("SGD", "新加坡元"),
    ("SAR", "沙特里亚尔"),
    ("BRL", "巴西雷亚尔"),
    ("SEK", "瑞典克朗"),
    ("TRY", "土耳其里拉"),
    ("PLN", "波兰兹罗提"),
    ("HKD", "港币"),
    ("ANG", "荷兰盾"),
    ("CHF", "瑞士法郎"),
    ("RON", "罗马尼亚新列伊"),
    ("MYR", "林吉特"),
    ("VND", "越南盾"),
    ("PHP", "菲律宾比索"),
    ("THB", "泰国铢"),
    ("IDR", "印尼卢比"),
    ("COP", "哥伦比亚比索"),
    ("CLP", "智利比索"),
    ("TWD", "新台币"),
    ("KRW", "韩国元"),
    ("CNH", "离岸人民币"),
    ("NGN", "尼日利亚奈拉"),
    ("BYN", "白俄罗斯卢布"),
    ("KZT", "哈萨克斯坦坚戈"),
    ("RUB", "俄罗斯卢布"),
    ("BGN", "保加利亚列弗"),
    ("HUF", "匈牙利福林"),
    ("EGP", "埃及镑"),
    ("ZAR", "南非兰特"),
)


def _currency_field(type_name: str, required: bool, description: str) -> FieldSpec:
    return FieldSpec(type_name, required, description, CURRENCY_ENUM, "documented", 11)


def _fields(items: dict[str, FieldSpec]) -> MappingProxyType[str, FieldSpec]:
    return MappingProxyType(items)


_PAGE = FieldSpec("int", True, "页码", minimum=1)
_PAGE_SIZE_100 = FieldSpec("int", True, "每页条数 [最大100条/页]", minimum=1, maximum=100)

ACTIVE_STATE_ENUM = _enum(("Active", "启用"), ("Inactive", "停用"))
WAREHOUSE_STATUS_ENUM = _enum(("enable", "启用"), ("disable", "停用"))
WAREHOUSE_TYPE_ENUM = _enum(
    ("SELF", "自营仓"),
    ("SUPPLIER", "供应商仓"),
    ("FBA", "Amazon.FBA"),
    ("THIRD", "三方仓"),
    ("WFS", "Walmart"),
    ("FULL", "MercadoLibre"),
    ("EBAY", "eBay"),
    ("ALIEXPRESS", "AliExpress自运营"),
    ("AMAZON_VC", "Amazon.VC"),
    ("AMAZON_AWD", "Amazon.AWD"),
    ("CDISCOUNT_FBC", "Cdiscount"),
    ("WAYFAIR_CG", "Wayfair"),
    ("EMAG_FBE", "eMAG"),
    ("TIKTOK_FBT", "Tiktok自运营"),
    ("WILDBERRIES_FBW", "Wildberries"),
    ("YANDEX_FBY", "Yandex"),
    ("OZON_FBO", "Ozon"),
)


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
                {
                    "brandList": FieldSpec(
                        "array<string>", description="品牌资料表编码", dynamic_identifier=True
                    ),
                    "categoryList": FieldSpec(
                        "array<string>", description="品类资料表编码", dynamic_identifier=True
                    ),
                    "pageInfo": FieldSpec(
                        "object",
                        description="分页对象，直接分页与分页对象必须传一种",
                        constraints=("Use pageInfo or direct page/pagesize, not both.",),
                        children=(("page", _PAGE), ("pagesize", _PAGE_SIZE_100)),
                    ),
                    "page": FieldSpec(
                        "int", description="页码，直接分页与分页对象必须传一种", minimum=1
                    ),
                    "pagesize": FieldSpec(
                        "int", description="每页条数 [最大100条/页]", minimum=1, maximum=100
                    ),
                    "skuList": FieldSpec(
                        "array<string>",
                        description="skuList（单个为模糊查询，精确查询传多个）",
                        dynamic_identifier=True,
                        constraints=("One SKU is fuzzy; multiple SKUs are exact.",),
                    ),
                    "platformMskuList": FieldSpec(
                        "array<string>", description="多平台MSKU", dynamic_identifier=True
                    ),
                    "mskuList": FieldSpec(
                        "array<string>", description="亚马逊MSKU", dynamic_identifier=True
                    ),
                    "state": FieldSpec(
                        "int",
                        description="状态 [0-正常，1-停用]",
                        enum_values=_enum((0, "正常"), (1, "停用")),
                        enum_status="documented",
                    ),
                    "dateType": FieldSpec(
                        "int",
                        description="时间类型 [0-创建时间，1-更新时间]",
                        enum_values=_enum((0, "创建时间"), (1, "更新时间")),
                        enum_status="documented",
                    ),
                    "startDate": FieldSpec(
                        "date", description="开始时间 [yyyy-MM-dd]", date_format="yyyy-MM-dd"
                    ),
                    "endDate": FieldSpec(
                        "date", description="结束时间 [yyyy-MM-dd]", date_format="yyyy-MM-dd"
                    ),
                }
            ),
            pagination_mode="direct_or_pageInfo",
            official_max_page_size=100,
            default_page_size=100,
            combination_constraints=("Use pageInfo or direct page/pagesize, not both.",),
        ),
        "product-inventory": EndpointSpec(
            "product-inventory",
            "查询产品库存",
            15,
            "POST",
            "/purchase/store/inventory/page",
            0.5,
            _fields(
                {
                    "page": _PAGE,
                    "pagesize": FieldSpec(
                        "int", True, "每页大小[最大100条/页]", minimum=1, maximum=100
                    ),
                    "productState": FieldSpec(
                        "int",
                        description="产品状态 [0-正常，1-停用]",
                        enum_values=_enum((0, "正常"), (1, "停用")),
                        enum_status="documented",
                    ),
                    "productTypeList": FieldSpec(
                        "array<int>",
                        description="产品类型 [0-成品，1-包材，2-组合产品，3-半成品]",
                        enum_values=_enum((0, "成品"), (1, "包材"), (2, "组合产品"), (3, "半成品")),
                        enum_status="documented",
                    ),
                    "state": FieldSpec(
                        "int",
                        description="商品状态 [0-异常，1-正常]",
                        enum_values=_enum((0, "异常"), (1, "正常")),
                        enum_status="documented",
                    ),
                    "warehouseIds": FieldSpec(
                        "array<long>", description="仓库id集合", dynamic_identifier=True
                    ),
                    "productManagerAccountIdList": FieldSpec(
                        "array<int>", description="产品负责人id集合", dynamic_identifier=True
                    ),
                    "sellingManagerIdList": FieldSpec(
                        "array<long>", description="销售负责人id集合", dynamic_identifier=True
                    ),
                    "skuList": FieldSpec(
                        "array<string>",
                        description="sku集合 [最大50条]",
                        dynamic_identifier=True,
                        max_items=50,
                    ),
                    "asinList": FieldSpec(
                        "array<string>",
                        description="asin集合 [最大50条]",
                        dynamic_identifier=True,
                        max_items=50,
                    ),
                    "mskuList": FieldSpec(
                        "array<string>",
                        description="msku集合 [最大50条]",
                        dynamic_identifier=True,
                        max_items=50,
                    ),
                    "filterQuantity": FieldSpec("boolean", description="过滤所有库存指标数据为0"),
                }
            ),
            official_max_page_size=100,
            default_page_size=100,
        ),
        "sales-performance": EndpointSpec(
            "sales-performance",
            "销售表现",
            3375,
            "POST",
            "/operation/sts/salesAnalysis/page",
            5.0,
            _fields(
                {
                    "groupByType": FieldSpec(
                        "string",
                        True,
                        "查询维度，msku：seller_sku、asin、父asin：variation_asin、sku、spu、国家：country、店铺：market，日期：date",
                        _enum(
                            ("seller_sku", "msku"),
                            ("asin", "asin"),
                            ("variation_asin", "父asin"),
                            ("sku", "sku"),
                            ("spu", "spu"),
                            ("country", "国家"),
                            ("market", "店铺"),
                            ("date", "日期"),
                        ),
                        "documented",
                    ),
                    "viewType": FieldSpec(
                        "string",
                        description="注意如果groupByType为date，viewType必传，DAY：日、WEEK：周、MONTH：月",
                        enum_values=_enum(("DAY", "日"), ("WEEK", "周"), ("MONTH", "月")),
                        enum_status="documented",
                        constraints=("Required when groupByType=date.",),
                    ),
                    "showCurrencyType": _currency_field(
                        "string",
                        True,
                        "显示币种，如原币种：YUAN，币种枚举查看QA说明：https://open.gerpgo.com/qa?id=11",
                    ),
                    "beginDate": FieldSpec(
                        "date", True, "开始时间，yyyy-MM-dd", date_format="yyyy-MM-dd"
                    ),
                    "endDate": FieldSpec(
                        "date", True, "结束时间，yyyy-MM-dd", date_format="yyyy-MM-dd"
                    ),
                    "sku": FieldSpec("string", description="sku", dynamic_identifier=True),
                    "variationAsin": FieldSpec(
                        "string", description="父asin", dynamic_identifier=True
                    ),
                    "productName": FieldSpec("string", description="产品名称"),
                    "asin": FieldSpec("string", description="asin", dynamic_identifier=True),
                    "msku": FieldSpec("string", description="msku", dynamic_identifier=True),
                    "page": FieldSpec("number", True, "页码", minimum=1),
                    "pagesize": FieldSpec(
                        "number",
                        True,
                        "页大小（建议不超过200）",
                        minimum=10,
                        maximum=1000,
                        recommended_maximum=200,
                    ),
                }
            ),
            official_recommended_page_size=200,
            runtime_min_page_size=10,
            runtime_max_page_size=1000,
            default_page_size=200,
            runtime_verified=True,
            runtime_verified_date="2026-08-28",
            runtime_verification_note=(
                "Runtime error 40004 reports pagesize 10~1000; 10 and 500 were accepted. "
                "Default 200 preserves the official recommendation."
            ),
            combination_constraints=("viewType is required when groupByType=date.",),
        ),
        "search-term-performance": EndpointSpec(
            "search-term-performance",
            "搜索词表现",
            100,
            "POST",
            "/operation/ads/adsKeywordAnalytical/query",
            60.0,
            _fields(
                {
                    "page": _PAGE,
                    "pagesize": FieldSpec(
                        "int", True, "每页大小 [最大100条/页]", minimum=1, maximum=100
                    ),
                    "marketId": FieldSpec("long", True, "站点ID", dynamic_identifier=True),
                    "startDateData": FieldSpec(
                        "date",
                        True,
                        "开始时间 [yyyy-MM-dd，开始时间需要等于结束时间]",
                        date_format="yyyy-MM-dd",
                    ),
                    "endDateData": FieldSpec(
                        "date",
                        True,
                        "结束时间 [yyyy-MM-dd，开始时间需要等于结束时间]",
                        date_format="yyyy-MM-dd",
                    ),
                }
            ),
            official_max_page_size=100,
            default_page_size=100,
            combination_constraints=("startDateData must equal endDateData.",),
        ),
        "review": EndpointSpec(
            "review",
            "Review",
            1092,
            "POST",
            "/operation/crm/review/page",
            1.0,
            _fields(
                {
                    "page": _PAGE,
                    "pagesize": _PAGE_SIZE_100,
                    "reviewIds": FieldSpec(
                        "array<string>", description="评论编号", dynamic_identifier=True
                    ),
                    "createDateBegin": FieldSpec(
                        "date",
                        description="记录开始时间 [yyyy-MM-dd HH:mm:ss]",
                        date_format="yyyy-MM-dd HH:mm:ss",
                    ),
                    "createDateEnd": FieldSpec(
                        "date",
                        description="记录结束时间 [yyyy-MM-dd HH:mm:ss]",
                        date_format="yyyy-MM-dd HH:mm:ss",
                    ),
                    "updateDateBegin": FieldSpec(
                        "datetime",
                        description="更新开始时间 [yyyy-MM-dd HH:mm:ss]",
                        date_format="yyyy-MM-dd HH:mm:ss",
                    ),
                    "updateDateEnd": FieldSpec(
                        "datetime",
                        description="更新结束时间 [yyyy-MM-dd HH:mm:ss]",
                        date_format="yyyy-MM-dd HH:mm:ss",
                    ),
                    "reviewDateBegin": FieldSpec(
                        "date", description="评论开始时间 [yyyy-MM-dd]", date_format="yyyy-MM-dd"
                    ),
                    "reviewDateEnd": FieldSpec(
                        "date", description="评论结束时间 [yyyy-MM-dd]", date_format="yyyy-MM-dd"
                    ),
                    "marketIds": FieldSpec(
                        "array<long>", description="站点id集合", dynamic_identifier=True
                    ),
                    "states": FieldSpec(
                        "array<long>",
                        description="Review状态 [0-未处理，1-处理中，2-已完成，3-无]",
                        enum_values=_enum((0, "未处理"), (1, "处理中"), (2, "已完成"), (3, "无")),
                        enum_status="documented",
                    ),
                    "results": FieldSpec(
                        "array<long>",
                        description=(
                            "跟踪结果 [0-无，1-无变化-客户不同意，3-已删除，"
                            "4-无变化-邮件无回复，5-分数变化-调高，6-分数变化-调低]"
                        ),
                        enum_values=_enum(
                            (0, "无"),
                            (1, "无变化-客户不同意"),
                            (3, "已删除"),
                            (4, "无变化-邮件无回复"),
                            (5, "分数变化-调高"),
                            (6, "分数变化-调低"),
                        ),
                        enum_status="documented",
                    ),
                    "orderIds": FieldSpec(
                        "array<string>", description="订单编号", dynamic_identifier=True
                    ),
                    "nameMatchType": FieldSpec(
                        "string",
                        description=(
                            "匹配方式 [fuzzyMatch-模糊匹配，exact-精准匹配，"
                            "contactBuyer-亚马逊，handAdd-手动发送]"
                        ),
                        enum_values=_enum(
                            ("fuzzyMatch", "模糊匹配"),
                            ("exact", "精准匹配"),
                            ("contactBuyer", "亚马逊"),
                            ("handAdd", "手动发送"),
                        ),
                        enum_status="documented",
                    ),
                    "asins": FieldSpec(
                        "array<string>", description="asin集合", dynamic_identifier=True
                    ),
                }
            ),
            official_max_page_size=100,
            default_page_size=100,
        ),
        "buyer-voice": EndpointSpec(
            "buyer-voice",
            "买家之声列表",
            1014,
            "POST",
            "/operation/crm/customerVoice/page",
            1.0,
            _fields(
                {
                    "pcxHealth": FieldSpec(
                        "string",
                        description=(
                            "状态 [Good-良好，Excellent-优秀，Fair-一般，Poor-不佳，Verypoor-极差]"
                        ),
                        enum_values=_enum(
                            ("Good", "良好"),
                            ("Excellent", "优秀"),
                            ("Fair", "一般"),
                            ("Poor", "不佳"),
                            ("Verypoor", "极差"),
                        ),
                        enum_status="documented",
                    ),
                    "marketIds": FieldSpec(
                        "array<int>", description="站点id集合", dynamic_identifier=True
                    ),
                    "productName": FieldSpec("string", description="产品名称, 模糊查询"),
                    "skus": FieldSpec(
                        "array<string>", description="sku集合", dynamic_identifier=True
                    ),
                    "mskus": FieldSpec(
                        "array<string>", description="msku集合", dynamic_identifier=True
                    ),
                    "asins": FieldSpec(
                        "array<string>", description="asin集合", dynamic_identifier=True
                    ),
                    "page": _PAGE,
                    "pagesize": _PAGE_SIZE_100,
                }
            ),
            official_max_page_size=100,
            default_page_size=100,
        ),
        "profit-analysis-v2": EndpointSpec(
            "profit-analysis-v2",
            "查询财务利润分析V2",
            2256,
            "POST",
            "/finance/sts/financialAnalysis/page/V2",
            10.0,
            _fields(
                {
                    "queryType": FieldSpec(
                        "string",
                        True,
                        "查询类型 [market，category，father_asin，asin，spu，sku，msku]",
                        _enum(
                            *(
                                (value, "官方未提供中文含义")
                                for value in (
                                    "market",
                                    "category",
                                    "father_asin",
                                    "asin",
                                    "spu",
                                    "sku",
                                    "msku",
                                )
                            )
                        ),
                        "documented",
                    ),
                    "costValues": FieldSpec(
                        "int",
                        True,
                        "成本取值 [0-先进先出，1-月末平均，2-自定义成本，3-混合成本]",
                        _enum((0, "先进先出"), (1, "月末平均"), (2, "自定义成本"), (3, "混合成本")),
                        "documented",
                    ),
                    "page": _PAGE,
                    "pagesize": _PAGE_SIZE_100,
                    "currency": _currency_field("string", True, "币种 [参考Q&A-通用参数-币种]"),
                    "dateType": FieldSpec(
                        "int",
                        True,
                        "时间类型 [0-按开始日期与结束日期，1-按月份]",
                        _enum((0, "按开始日期与结束日期"), (1, "按月份")),
                        "documented",
                    ),
                    "monthDate": FieldSpec(
                        "string", description="月份 [yyyy-MM]", date_format="yyyy-MM"
                    ),
                    "startDate": FieldSpec(
                        "date", description="开始时间 [yyyy-MM-dd]", date_format="yyyy-MM-dd"
                    ),
                    "endDate": FieldSpec(
                        "date", description="结束时间 [yyyy-MM-dd]", date_format="yyyy-MM-dd"
                    ),
                    "marketIds": FieldSpec(
                        "array<int>", description="站点ID集合", dynamic_identifier=True
                    ),
                    "categoryIds": FieldSpec(
                        "array<string>", description="品类编码集合", dynamic_identifier=True
                    ),
                    "brands": FieldSpec(
                        "array<string>", description="品牌编码集合", dynamic_identifier=True
                    ),
                    "decimalPlaces": FieldSpec(
                        "int", description="保留小数位 2 --8位", minimum=2, maximum=8
                    ),
                    "footerExpandDetails": FieldSpec(
                        "boolean", description="店铺特有数据是否返回详情"
                    ),
                    "platformCodes": FieldSpec(
                        "array<string>",
                        description="平台编码，默认亚马逊：AMAZON",
                        enum_status="official_not_published",
                        default_value=["AMAZON"],
                        default_documented=True,
                    ),
                    "queryMskuList": FieldSpec(
                        "array<string>",
                        description="支持msku维度-msku字段精确查询",
                        dynamic_identifier=True,
                    ),
                    "skuList": FieldSpec(
                        "array<string>",
                        description="支持msku维度/sku维度 -- sku字段精确查询",
                        dynamic_identifier=True,
                    ),
                    "asinList": FieldSpec(
                        "array<string>",
                        description="支持msku维度/asin维度 -- asin字段精确查询",
                        dynamic_identifier=True,
                    ),
                }
            ),
            official_max_page_size=100,
            default_page_size=100,
            combination_constraints=(
                "dateType=0 requires startDate and endDate; dateType=1 requires monthDate.",
            ),
        ),
        "keyword-performance": EndpointSpec(
            "keyword-performance",
            "关键词表现",
            99,
            "POST",
            "/operation/ads/adsKeywordAnalytical/page",
            60.0,
            _fields(
                {
                    "page": _PAGE,
                    "pagesize": _PAGE_SIZE_100,
                    "marketId": FieldSpec("long", True, "站点ID", dynamic_identifier=True),
                    "startDateData": FieldSpec(
                        "date",
                        True,
                        "开始时间 [yyyy-MM-dd，开始时间需要等于结束时间]",
                        date_format="yyyy-MM-dd",
                    ),
                    "endDateData": FieldSpec(
                        "date",
                        True,
                        "结束时间 [yyyy-MM-dd，开始时间需要等于结束时间]",
                        date_format="yyyy-MM-dd",
                    ),
                }
            ),
            official_max_page_size=100,
            default_page_size=100,
            combination_constraints=("startDateData must equal endDateData.",),
        ),
        "product-performance": EndpointSpec(
            "product-performance",
            "产品表现",
            131,
            "POST",
            "/operation/sts/productAnalyzeMultiIndex/page",
            60.0,
            _fields(
                {
                    "showCurrencyType": _currency_field(
                        "string", True, "显示币种类型 [参考Q&A-通用参数-币种]"
                    ),
                    "beginDate": FieldSpec(
                        "string", True, "开始时间 [yyyy-MM-dd]", date_format="yyyy-MM-dd"
                    ),
                    "endDate": FieldSpec(
                        "string", True, "结束时间 [yyyy-MM-dd]", date_format="yyyy-MM-dd"
                    ),
                    "page": _PAGE,
                    "pagesize": FieldSpec(
                        "int",
                        True,
                        "每页条数 [最大100条/页]",
                        minimum=10,
                        maximum=1000,
                    ),
                }
            ),
            official_max_page_size=100,
            runtime_min_page_size=10,
            runtime_max_page_size=1000,
            default_page_size=100,
            runtime_verified=True,
            runtime_verified_date="2026-08-28",
            runtime_verification_note=(
                "Runtime error 40004 reports pagesize 10~1000; 10 and 100 were accepted, "
                "while 500 returned an API error. Default 100 is verified."
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
                {
                    "groupByType": FieldSpec(
                        "string",
                        True,
                        "查询维度 [asin-ASIN维度，seller_sku-MSKU维度]",
                        _enum(("asin", "ASIN维度"), ("seller_sku", "MSKU维度")),
                        "documented",
                    ),
                    "showCurrencyType": _currency_field(
                        "string", True, "显示币种 [参考Q&A-通用参数-币种]"
                    ),
                    "beginDate": FieldSpec(
                        "date", True, "开始时间 [yyyy-MM-dd]", date_format="yyyy-MM-dd"
                    ),
                    "endDate": FieldSpec(
                        "date", True, "结束时间 [yyyy-MM-dd]", date_format="yyyy-MM-dd"
                    ),
                    "isShowTotal": FieldSpec(
                        "boolean", True, "是否显示合计 [显示合计: true; 不显示合计： false]"
                    ),
                    "page": _PAGE,
                    "pagesize": FieldSpec(
                        "int",
                        True,
                        "每页条数 [最大100条/页]",
                        minimum=10,
                        maximum=1000,
                    ),
                    "marketList": FieldSpec(
                        "array<int>", description="站点ID列表", dynamic_identifier=True
                    ),
                    "sku": FieldSpec("string", description="sku", dynamic_identifier=True),
                    "asin": FieldSpec("string", description="asin", dynamic_identifier=True),
                    "asinList": FieldSpec(
                        "array<string>",
                        description="asin集合（一次建议不超过20）",
                        dynamic_identifier=True,
                        recommended_max_items=20,
                    ),
                    "msku": FieldSpec("string", description="msku", dynamic_identifier=True),
                    "mskuList": FieldSpec(
                        "array<string>",
                        description="msku集合（一次建议不超过20）",
                        dynamic_identifier=True,
                        recommended_max_items=20,
                    ),
                }
            ),
            official_max_page_size=100,
            runtime_min_page_size=10,
            runtime_max_page_size=1000,
            default_page_size=100,
            runtime_verified=True,
            runtime_verified_date="2026-08-28",
            runtime_verification_note=(
                "Runtime error 40004 reports pagesize 10~1000; 10 and 100 were accepted, "
                "while 500 returned an API error. Default 100 is verified."
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
                {
                    "marketList": FieldSpec(
                        "array<int>", description="站点ID数组", dynamic_identifier=True
                    ),
                    "currency": _currency_field("string", True, "币种 [参考Q&A-通用参数-币种]"),
                    "beginDate": FieldSpec(
                        "string", True, "开始时间 [yyyy-MM-dd]", date_format="yyyy-MM-dd"
                    ),
                    "endDate": FieldSpec(
                        "string", True, "结束时间 [yyyy-MM-dd]", date_format="yyyy-MM-dd"
                    ),
                    "page": _PAGE,
                    "pagesize": FieldSpec(
                        "int",
                        True,
                        "每页条数 [最大100条/页]",
                        minimum=10,
                        maximum=1000,
                    ),
                    "viewType": FieldSpec(
                        "string",
                        True,
                        "查询维度类型 [day-日，week-周，month-月]",
                        _enum(("day", "日"), ("week", "周"), ("month", "月")),
                        "documented",
                    ),
                }
            ),
            official_max_page_size=100,
            runtime_min_page_size=10,
            runtime_max_page_size=1000,
            default_page_size=500,
            runtime_verified=True,
            runtime_verified_date="2026-08-28",
            runtime_verification_note=(
                "Runtime error 40004 reports pagesize 10~1000; 10 and 500 were accepted."
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
                {
                    "marketList": FieldSpec(
                        "array<int>", description="站点ID数组", dynamic_identifier=True
                    ),
                    "currency": _currency_field("string", True, "币种 [参考Q&A-通用参数-币种]"),
                    "beginDate": FieldSpec(
                        "date", True, "开始时间 [yyyy-MM-dd]", date_format="yyyy-MM-dd"
                    ),
                    "endDate": FieldSpec(
                        "date", True, "结束时间 [yyyy-MM-dd]", date_format="yyyy-MM-dd"
                    ),
                    "page": _PAGE,
                    "pagesize": FieldSpec(
                        "int",
                        True,
                        "每页条数 [最大100条/页]",
                        minimum=10,
                        maximum=1000,
                    ),
                }
            ),
            official_max_page_size=100,
            runtime_min_page_size=10,
            runtime_max_page_size=1000,
            default_page_size=500,
            runtime_verified=True,
            runtime_verified_date="2026-08-28",
            runtime_verification_note=(
                "Runtime error 40004 reports pagesize 10~1000; 10 and 500 were accepted."
            ),
        ),
        "catalog-amazon-shops": EndpointSpec(
            "catalog-amazon-shops",
            "查询亚马逊店铺信息",
            153,
            "POST",
            "/middle/base/market/page",
            1.0,
            _fields(
                {
                    "page": _PAGE,
                    "pagesize": _PAGE_SIZE_100,
                    "condition": FieldSpec(
                        "object",
                        True,
                        "查询条件",
                        children=(
                            (
                                "recordDateStart",
                                FieldSpec(
                                    "datetime",
                                    description="起始新增时间 [yyyy-MM-dd HH:mm:ss]",
                                    date_format="yyyy-MM-dd HH:mm:ss",
                                ),
                            ),
                            (
                                "recordDateEnd",
                                FieldSpec(
                                    "datetime",
                                    description="结束新增时间 [yyyy-MM-dd HH:mm:ss]",
                                    date_format="yyyy-MM-dd HH:mm:ss",
                                ),
                            ),
                            (
                                "marketIds",
                                FieldSpec(
                                    "array<int>",
                                    description="站点ID集合",
                                    dynamic_identifier=True,
                                ),
                            ),
                        ),
                    ),
                }
            ),
            official_max_page_size=100,
            endpoint_group="catalog",
            response_key_fields=(
                "marketId",
                "marketName",
                "store",
                "countryCode",
                "countryName",
                "areaName",
                "state",
            ),
        ),
        "catalog-users": EndpointSpec(
            "catalog-users",
            "查询所有用户列表",
            25,
            "POST",
            "/middle/base/allUser/list",
            1.0,
            _fields({}),
            endpoint_group="catalog",
            request_body_mode="none",
            response_key_fields=("id", "username", "name", "status"),
            public_method_verified_date="2026-08-28",
            metadata_method_difference="公开文档页面标示 POST；详情元数据仍标示 Get。",
        ),
        "catalog-warehouses": EndpointSpec(
            "catalog-warehouses",
            "查询仓库信息列表",
            1035,
            "POST",
            "/purchase/store/multiTypeWarehouse/page",
            0.5,
            _fields(
                {
                    "model": FieldSpec(
                        "object",
                        True,
                        "查询参数",
                        children=(
                            (
                                "warehouseIdList",
                                FieldSpec(
                                    "array<long>",
                                    description="仓库ID集合",
                                    dynamic_identifier=True,
                                ),
                            ),
                            (
                                "warehouseName",
                                FieldSpec("string", description="仓库名称（模糊匹配）"),
                            ),
                            (
                                "status",
                                FieldSpec(
                                    "string",
                                    description="状态 [enable-启用，disable-停用]",
                                    enum_values=WAREHOUSE_STATUS_ENUM,
                                    enum_status="documented",
                                ),
                            ),
                            (
                                "typeList",
                                FieldSpec(
                                    "array<string>",
                                    description=(
                                        "仓库类型集合 [SELF-自营仓，SUPPLIER-供应商仓，"
                                        "FBA-Amazon.FBA，THIRD-三方仓，WFS-Walmart，"
                                        "FULL-MercadoLibre，EBAY-eBay，"
                                        "ALIEXPRESS-AliExpress自运营，AMAZON_VC-Amazon.VC，"
                                        "AMAZON_AWD-Amazon.AWD，CDISCOUNT_FBC-Cdiscount，"
                                        "WAYFAIR_CG-Wayfair，EMAG_FBE-eMAG，"
                                        "TIKTOK_FBT-Tiktok自运营，"
                                        "WILDBERRIES_FBW-Wildberries，YANDEX_FBY-Yandex，"
                                        "OZON_FBO-Ozon]"
                                    ),
                                    enum_values=WAREHOUSE_TYPE_ENUM,
                                    enum_status="documented",
                                ),
                            ),
                            (
                                "startDate",
                                FieldSpec(
                                    "datetime",
                                    description="创建开始时间 [yyyy-MM-dd HH:mm:ss]",
                                    date_format="yyyy-MM-dd HH:mm:ss",
                                ),
                            ),
                            (
                                "endDate",
                                FieldSpec(
                                    "datetime",
                                    description="创建结束时间 [yyyy-MM-dd HH:mm:ss]",
                                    date_format="yyyy-MM-dd HH:mm:ss",
                                ),
                            ),
                        ),
                    ),
                    "page": _PAGE,
                    "pagesize": _PAGE_SIZE_100,
                }
            ),
            official_max_page_size=100,
            endpoint_group="catalog",
            response_key_fields=("id", "name", "type", "status", "country", "platformCode"),
        ),
        "catalog-brands": EndpointSpec(
            "catalog-brands",
            "查询品牌资料",
            1752,
            "POST",
            "/purchase/goods/brand/page",
            0.5,
            _fields(
                {
                    "code": FieldSpec("string", description="品牌编码模糊查询"),
                    "name": FieldSpec("string", description="品牌名称模糊查询"),
                    "state": FieldSpec(
                        "string",
                        description="状态 [Active-启用，Inactive-停用]",
                        enum_values=ACTIVE_STATE_ENUM,
                        enum_status="documented",
                    ),
                    "page": FieldSpec("int", True, "第几页", minimum=1),
                    "pagesize": FieldSpec("int", True, "每页显示多少条", minimum=1),
                }
            ),
            endpoint_group="catalog",
            response_key_fields=("code", "name", "state"),
        ),
        "catalog-categories": EndpointSpec(
            "catalog-categories",
            "查询品类信息",
            54,
            "POST",
            "/purchase/goods/category/page",
            0.5,
            _fields(
                {
                    "state": FieldSpec(
                        "string",
                        description="状态 [Active-启用，Inactive-停用]",
                        enum_values=ACTIVE_STATE_ENUM,
                        enum_status="documented",
                    ),
                    "page": _PAGE,
                    "pagesize": _PAGE_SIZE_100,
                    "valueList": FieldSpec(
                        "array<string>",
                        description="品类编码集合",
                        dynamic_identifier=True,
                    ),
                }
            ),
            official_max_page_size=100,
            endpoint_group="catalog",
            response_key_fields=("value", "name", "state", "parentCategory"),
        ),
        "catalog-multiplatform-shops": EndpointSpec(
            "catalog-multiplatform-shops",
            "查询多平台店铺信息",
            67,
            "POST",
            "/platform/multiplatform/multiShop/query",
            0.5,
            _fields({}),
            endpoint_group="catalog",
            request_body_mode="empty_object",
            response_key_fields=(
                "shopId",
                "shopName",
                "platformId",
                "countryCode",
                "regionName",
                "regionCnName",
                "status",
            ),
            public_method_verified_date="2026-08-28",
            metadata_method_difference="公开文档页面标示 POST；详情元数据仍标示 Get。",
        ),
        "catalog-amazon-shop-names": EndpointSpec(
            "catalog-amazon-shop-names",
            "根据亚马逊店铺id查询店铺名称",
            1177,
            "POST",
            "/middle/base/marketNames/query",
            0.1,
            _fields(
                {
                    "markerIds": FieldSpec(
                        "array<int>",
                        True,
                        "店铺id集合",
                        dynamic_identifier=True,
                    )
                }
            ),
            endpoint_group="catalog",
            response_key_fields=("data",),
            public_method_verified_date="2026-08-28",
            metadata_method_difference="公开文档页面标示 POST；详情元数据仍标示 Get。",
        ),
        "catalog-amazon-shop-warehouses": EndpointSpec(
            "catalog-amazon-shop-warehouses",
            "根据亚马逊店铺id查询仓库信息",
            1179,
            "POST",
            "/middle/base/warehouseIds/query",
            1.0,
            _fields(
                {
                    "marketIdList": FieldSpec(
                        "array<int>",
                        True,
                        "店铺id集合",
                        dynamic_identifier=True,
                    )
                }
            ),
            endpoint_group="catalog",
            response_key_fields=("marketId", "warehouseId"),
            public_method_verified_date="2026-08-28",
            metadata_method_difference="公开文档页面标示 POST；详情元数据仍标示 Get。",
        ),
    }
)


def get_endpoint(key: str) -> EndpointSpec:
    try:
        return ENDPOINTS[key]
    except KeyError as exc:
        raise ValidationError(f"Unsupported OpenAPI endpoint key: {key}") from exc

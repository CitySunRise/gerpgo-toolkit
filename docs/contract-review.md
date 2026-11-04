# Contract review, 2026-11-04

Sources: public [directory](https://open.gerpgo.com/document?id=596), its
`/api/openAdmin/doc/tree` and `/api/openAdmin/doc/detail?id=...` metadata.
All 14 top-level categories and the STA subtree were fetched, including writes.
The checked-in snapshot contains only schemas and descriptions, no request or
response examples, captured ERP traffic, internal ERP URLs or account data.

The current public page renderer, linked by the public HTML as
`/js/chunk-4621e76a.5851b1ee.js`, creates the request-method label as literal
`POST` (`Le=...createTextVNode...(" POST ")`). This independently confirms the
existing discrepancy with Get detail metadata. Registered overrides record the
public-method verification date and metadata difference. The two PostParam
documents remain blocked because their transport needs separate verification.

The 26 newly considered queries with absent rate periods remain blocked. No
refill period is inferred from token-bucket capacity. Five v0.2 queries already
have verified local intervals of 60 seconds. Their current official token-bucket
metadata is stored separately and exactly verified (capacity 3, period null).
The local interval is an implementation guard, not a statement of official refill
frequency. Request estimates for these endpoints use that local interval.

Read/write classification was reviewed by business operation, not HTTP method.
49 writes are denied by document ID. In particular 6681 submits an inspector,
planned inspection date and inspection mode, so it is a scheduling write.
102 reads strategy templates; 101/104 read coupon/deal lists using nextId/extObj.

The SDK owns all fields and enums. Unambiguous bracket tables and reviewed prose
layouts are converted from the public descriptions by prepare_catalog.py into
the SDK snapshot. The generator never uses official example payloads. Missing
Chinese meanings remain explicitly unpublished; e.g. document 5766 lists raw
invoice status 3 without a label, which is not invented. The VC API authorization
state meanings are kept exactly as published even where the naming is surprising.
Unrecognized prose tables block registration rather than disabling enum validation.

Document 2453's itemType enum explicitly includes 2=调拨单. Its query therefore
supplies the official transfer-carton capability. 4645 supports inbound order and
lock-order filtering; 6025 supports related orders. These are not assumed to be
semantically identical to core's transfer-only serial query or initial-batch view.
No Web business migration is justified by a verified missing official capability.

Refresh metadata with snapshot_official_catalog.py, prepare it with
prepare_catalog.py, and regenerate the inventory with render_endpoint_inventory.py.
Review the resulting diff before accepting a refreshed snapshot. The live official
verifier compares methods, paths, all nested request fields, descriptions, enums,
rates and published response keys. A snapshot refresh never makes CI accept drift
without a source change and review.

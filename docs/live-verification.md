# Read-only verification, 2026-11-04

Follow-up: [2026-11-05 verification of the remaining 202 endpoints](live-verification-2026-11-05.md).
The scope and statements below describe the original November 4 pass only.

These eight endpoints returned successful envelopes and normal data structures
using the initialized prod profile. Only status and structure flags were emitted.
No real business values, identifiers, credentials, headers, Trace IDs or exports
were written to the repository. Zero rows may still represent success.

| Interface / official document | Live result | Parameter categories | Structure |
|---|---|---|---|
| 查询调拨单列表 (1020) | success | pagination, single-day creation date | normal |
| 查询调拨单详情 (1021) | success | order from the same scoped list | normal |
| 查询发货单详情-装箱清单 (2453) | success | same scoped order, official document type | normal |
| 批次库存(实物查询)分页列表查询 (4645) | success | pagination, single-day creation date | normal |
| 批次流水 (6025) | success | pagination, single-day operation date | normal |
| 分时策略NEW (102) | success | pagination, one page of templates | normal |
| 获取本位币币种 (66) | success | none | normal |
| 查询平台定义 (8655) | success | none | normal |

All other 202 registered endpoints in endpoint-inventory.md are **not live-verified
in this pass**. They were not called without a selected business scope/identifier;
neither permissions nor real response shape is claimed verified. This includes
STA shipment/boxing queries, for which no inbound plan/shipment was selected.
The 28 unregistered read candidates are blocked as listed in the inventory.

Local checks do not prove Windows runtime compatibility. The existing GitHub
Actions matrix runs macOS and Windows with Python 3.11/3.12/3.13; its run status
must be reported separately from local results.

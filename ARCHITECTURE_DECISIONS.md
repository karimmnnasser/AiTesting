# 🏗️ Jarvis AI - Architecture Decision Records (ADR)

## التاريخ: 2026-06-08
## المشاركون: Qwen + ChatGPT + كريم (المطور)

---

## ADR-001: Tool Registry Pattern
**الحالة**: مقبول ✅
**القرار**: استخدام Tool Registry Pattern (Hybrid)

## ADR-002: Result Pattern
**الحالة**: مقبول ✅
**القرار**: استخدام Result Pattern بدلاً من strings

## ADR-003: Database Layer
**الحالة**: مقبول ✅
**القرار**: SQLite + Repository Pattern (بدون ORM)

## ADR-004: Default Provider
**الحالة**: مقبول ✅
**القرار**: Groq هو المزود الافتراضي

## ADR-005: Confirmation System
**الحالة**: مقبول ✅
**القرار**: Defense in Depth (أداة + Security Layer)

## ADR-006: Planner Agent
**الحالة**: مؤجل ⏳
**القرار**: تأجيل Planner Agent لما بعد Phase 1

## ADR-007: JSON Contract
**الحالة**: مقبول ✅
**الصيغة**: {"action": "...", "parameters": {...}}

## ADR-008: Phase 0 Scope
**الحالة**: مقبول ✅
**القرار**: البدء بـ write_file و read_file فقط

---

## ADR-009: Phase 1 Tool Execution Contract
**Status**: Accepted
**Date**: 2026-06-12

**Decision**: Standardize the execution contract between `ToolResponse`, `Executor`, and `Tool Registry` while preserving existing tools.

**Details**:
- `ToolResponse` now supports the existing `message` field plus `action`, `data`, `error`, `needs_confirmation`, and `parameters`.
- `ToolResponse.ok()`, `ToolResponse.fail()`, and `ToolResponse.needs_confirmation_response()` provide a single response factory API.
- `tools.registry.execute_tool()` supports both class-based tools with `execute(ToolRequest)` and function-based tools with direct keyword parameters.
- `Executor.execute()` always returns `ToolResponse`, normalizing raw function results and class-based tool responses.
- Dangerous tools still require confirmation by default. Confirmed execution is available through `Executor.execute(request, confirmed=True)` for the UI confirmation flow.

**Validation**:
- Added `tests/test_phase1_contracts.py`.
- Verified every registered tool is covered by the phase-one contract tests.
- Dangerous tools are tested through confirmation checks and safe invalid confirmed calls, without executing destructive actions.

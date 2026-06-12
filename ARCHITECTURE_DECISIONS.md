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

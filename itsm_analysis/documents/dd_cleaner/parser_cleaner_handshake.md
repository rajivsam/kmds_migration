# 📑 Data Dictionary: Provisional Entity Assignment Report
**Generation Timestamp:** `2026-07-02 05:25:07`
**Source Blueprint:** `itsm_dd.csv`

### 🏗️ Structural Assessment
- **Inferred Dataset Type:** `cross-sectional`
> ⚠️ **Note:** This inference is an automated suggestion based on schema patterns and may be incorrect. The `dataset_type` must be explicitly confirmed or defined in `config.yaml` before the Cleaner phase begins.

### 📊 Classification Summary
- **unassigned**: 5 fields

### ⚠️ Orphans in Data Dictionary
> These attributes exist in the dictionary but were **not found** in the raw data file. They have been excluded from the assignments below.

- `incident_state`
- `active`
- `reassignment_count`
- `reopen_count`
- `sys_mod_count`
- `made_sla`
- `caller_id`
- `opened_by`
- `sys_created_by`
- `sys_created_at`
- `sys_updated_by`
- `sys_updated_at`
- `contact_type`
- `location`
- `category`
- `subcategory`
- `u_symptom`
- `cmdb_ci`
- `impact`
- `urgency`
- `priority`
- `assigned_to`
- `knowledge`
- `u_priority_confirmation`
- `notify`
- `problem_id`
- `rfc`
- `vendor`
- `caused_by`
- `close_code`
- `resolved_by`

---

### 📋 Detailed Assignments
| Attribute          | Assignment   | Logical Type   | Physical Type   | Flag: Geographic   |
|--------------------|--------------|----------------|-----------------|--------------------|
| `number`           | `unassigned` | `categorical`  | `str`           | `False`            |
| `opened_at`        | `unassigned` | `datetime`     | `datetime`      | `False`            |
| `assignment_group` | `unassigned` | `categorical`  | `str`           | `False`            |
| `resolved_at`      | `unassigned` | `datetime`     | `datetime`      | `False`            |
| `closed_at`        | `unassigned` | `datetime`     | `datetime`      | `False`            |

---
*Report generated via automated dd-parser post-processing.*
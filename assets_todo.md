# 📋 HRlens Asset Management — Modular Test Suite Tracker (`assets_todo.md`)

This tracker organizes all dedicated domain test suites covering functional workflows, master data seeding, security isolation, boundary analysis, assignment governance, and condition lifecycles.

---

## 🧭 Modular Functional Test Matrix

| # | Functional Domain | Scope & Verifications | Test Suite File | Status |
|:---:|---|---|---|:---:|
| **1** | **Masters & Seeding** | - 10 Categories, 10 Subcategories, 10 Corporate Vendors<br>- Branch Groups mapped for all 9 branches | [`test_assets_master_api.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/api/Assets/test_assets_master_api.py)<br>[`test_asset_master.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/asset/test_asset_master.py)<br>[`test_branch_group.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/asset/test_branch_group.py) | `[x] PASSED ✅` |
| **2** | **Procurement & Ingestion** | - Invoice PDF upload & line-item amount auto-reconciliation<br>- Procurement Step 1 validation<br>- Manual Asset Entry & QR Code generation | [`test_asset_procurement_flow.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/asset/test_asset_procurement_flow.py)<br>[`test_procurement_validation.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/asset/test_procurement_validation.py)<br>[`test_asset_entry.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/asset/test_asset_entry.py) | `[x] PASSED ✅` |
| **3** | **Branch Scoping & Isolation** | - Cross-branch asset visibility isolation<br>- Branch-scoped dropdown filtering (Varanasi vs Agra vs Noida) | [`test_branch_asset_visibility_isolation_spec.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/asset/test_branch_asset_visibility_isolation_spec.py) | `[x] PASSED ✅` |
| **4** | **Warranty 30-Day Expiry BVA & Dashboard Count** | - 4-Point Boundary Value Analysis (`Day 0`, `Day 1`, `Day 30`, `Day 31`)<br>- **Condition Rule**: (Condition: `Repair Required` \| `Damaged`) AND Warranty Expiry $\le$ 30 Days<br>- Active Dashboard Count & Alert Banner verification | [`test_asset_warranty_30_days_spec.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/asset/test_asset_warranty_30_days_spec.py) | `[x] PASSED ✅` |
| **5** | **Assignment & Governance** | - Direct Assignment accept/reject sub-flows<br>- Employee request & fulfillment<br>- Duplicate request prevention & concurrency locks | [`test_asset_assignment_workflow_spec.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/asset/test_asset_assignment_workflow_spec.py) | `[x] PASSED ✅` |
| **6** | **Return & 4-Condition Outcomes** | - Mandatory media attachments (**4 photos $\le$ 5MB + 1 video 10s**)<br>- All 4 outcomes: `Good`, `Damaged`, `Repair Required`, `Lost` | [`test_asset_return_comprehensive_spec.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/asset/test_asset_return_comprehensive_spec.py)<br>[`test_asset_condition_lifecycle_outcomes_spec.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/asset/test_asset_condition_lifecycle_outcomes_spec.py) | `[x] PASSED ✅` |
| **7** | **End-to-End Asset Lifecycle** | - Unified lifecycle from procurement through assignment, maintenance, and disposal | [`test_branch_scoped_it_asset_lifecycle_spec.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/asset/test_branch_scoped_it_asset_lifecycle_spec.py)<br>[`test_asset_lifecycle_flow.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/asset/test_asset_lifecycle_flow.py) | `[x] PASSED ✅` |

---

## 📝 Execution Commands

### 🔹 1. Warranty 30-Day 4-Point Boundary Test
```powershell
venv\Scripts\pytest.exe tests/hrlense_portal/ui/asset/test_asset_warranty_30_days_spec.py -k "varanasi" -v -s
```

### 🔹 2. Assignment & Governance Workflows (Accept / Reject)
```powershell
venv\Scripts\pytest.exe tests/hrlense_portal/ui/asset/test_asset_assignment_workflow_spec.py -v -s
```

### 🔹 3. Return & 4-Condition Lifecycle Outcomes
```powershell
venv\Scripts\pytest.exe tests/hrlense_portal/ui/asset/test_asset_condition_lifecycle_outcomes_spec.py -k "test_unified and varanasi" -v -s
```

### 🔹 4. Branch-Scoped Full Lifecycle
```powershell
venv\Scripts\pytest.exe tests/hrlense_portal/ui/asset/test_branch_scoped_it_asset_lifecycle_spec.py -k "Varanasi" -v -s
```

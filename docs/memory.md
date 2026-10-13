# Argus — Memory Architecture & Compounding Intelligence

**Version:** 1.0.0  
**Classification:** Core System Architecture  
**Status:** Approved for Implementation

---

## 1. Foundational Doctrine: Memory Stores *HOW*, Never *WHAT*

The primary point of failure in corporate AI implementations is the hallucination of stale data stored in conversational or vector memory. In enterprise finance, recalling a 2023 EBITDA figure when asked about 2024 is fatal.

### The Invariant Principle:
> **Memory stores HOW (procedural rules, layout fingerprints, human corrections, accounting conventions, entity aliases).**  
> **Memory NEVER stores WHAT (financial fact values, balances, and numerical quantities).**

Financial facts live exclusively in the PostgreSQL **Fact Store**, versioned, time-stamped, and tied directly to pixel-level evidence coordinates. Memory provides the cognitive heuristics that accelerate future extraction and eliminate repetitive human review.

---

## 2. Memory Taxonomy

```
+-----------------------------------------------------------------------------------------+
|                                    ARGUS MEMORY STACK                                   |
+-----------------------------------------------------------------------------------------+
|  1. WORKING MEMORY (Job-Scoped)                                                         |
|  - Lifetime: Duration of a single document processing job                               |
|  - Scope: Intermediate OCR bboxes, parser voter candidates, routing decisions           |
|  - Storage: Redis cache & transient Postgres job state                                  |
+-----------------------------------------------------------------------------------------+
|  2. EPISODIC MEMORY (Audit & Operational History)                                       |
|  - Lifetime: Append-only, immutable permanence                                          |
|  - Scope: Every tool call, agent action, reviewer correction, and verification check    |
|  - Storage: PostgreSQL `audit_events` and `agent_runs` tables                            |
+-----------------------------------------------------------------------------------------+
|  3. SEMANTIC MEMORY (Curated Institutional Knowledge)                                   |
|  - Lifetime: Curated, versioned, tenant-isolated                                        |
|  - Scope: Entity alias registries, fiscal calendars, currency defaults, metric glossary |
|  - Storage: PostgreSQL `entity_registry` and `semantic_glossary` tables                  |
+-----------------------------------------------------------------------------------------+
|  4. PROCEDURAL MEMORY (Compounding Layout Templates)                                    |
|  - Lifetime: Evolutionary, self-refining with human feedback                            |
|  - Scope: Layout fingerprints, column mapping rules, subtotal quirks, learned overrides |
|  - Storage: PostgreSQL `layout_templates` and `template_rules` tables                   |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Layout Fingerprinting & Template Memory

Financial document publishers (e.g., standard SEC 10-K filings, Bloomberg sheets, Morgan Stanley equity research) exhibit consistent visual layouts. Argus turns reviewer corrections into compounding assets by indexing and matching layouts.

```
       [New Ingested Document Page]
                     |
                     v
       +----------------------------+
       |   Compute Page Hashes      |
       | - Perceptual Image Hash    |
       | - Table Structural N-Grams |
       +-------------+--------------+
                     |
                     v
       +----------------------------+
       | Query `layout_templates`   |
       | with Cosine / Hamming Sim  |
       +-------------+--------------+
                     |
         +-----------+-----------+
         |                       |
     [Match >= 0.88]         [Match < 0.88]
         |                       |
         v                       v
+------------------+   +-------------------+
| Retrieve Learned |   | Cold Extraction   |
| Rules & Quirks   |   | Full Dual-Engine  |
+--------+---------+   | Ensemble Run      |
         |             +-------------------+
         v
+---------------------------------------------------+
| Apply Template Rules:                             |
| - Pre-mapped Column Semantics                     |
| - Unit/Scale Defaults ("In Millions")             |
| - Subtotal Notes ("Row 14 references Note 6")     |
+---------------------------------------------------+
```

### 3.1 Dual-Vector Fingerprint Formula
A layout fingerprint is a composite hash:
1. **Perceptual Render Hash ($H_{img}$):** Block-mean difference perceptual hash (pHash) computed from a $512 \times 512$ monochrome render of the page canvas.
2. **Structural Topology Hash ($H_{struct}$):** Normalized string encoding row/column grid dimensions, relative coordinates, and header text 3-grams:
   $$\text{Hash} = \text{MD5}(\text{GridDimensions} \parallel \text{HeaderNGrams} \parallel \text{RelativeCellSpacing})$$

### 3.2 Confidence Ladder & Auto-Application
To ensure safety, learned rules do not immediately auto-apply blindly:
- **Observation Tier (1 Human Correction):** Rule is saved in *Suggest Mode*. The Review Console displays: *"Suggested fix based on similar document from Publisher X"*.
- **Verified Tier ($\ge 2$ Independent Confirmations):** Rule auto-applies during Stage S4 (Canonicalize) and tags elements with `template-applied (v{version})`.
- **Template Drift Protection:** If a matched template yields an arithmetic failure in Stage S6, the fingerprint match is automatically down-weighted, falling back to clean cold extraction.

---

## 4. Correction Propagation Policy

When a human reviewer corrects an extraction error in the Review Console, that correction must not evaporate into a single isolated cell.

```
  [Reviewer Corrects Cell: "(1,245)" -> "-1245.00"]
                          |
                          v
  +-----------------------------------------------+
  | Spatial & Semantic Cluster Search             |
  | Scan all cells in same column / matching docs |
  +-----------------------+-----------------------+
                          |
                          v
  +-----------------------------------------------+
  | Batch Correction Proposal Generated           |
  | "Apply this rule to 18 identical cells?"      |
  +-----------------------+-----------------------+
                          |
           +--------------+--------------+
           |                             |
      [Rejected]                    [Accepted]
           |                             |
           v                             v
    [Logged Only]               +---------------------------------+
                                | 1. Mutate cells -> New Doc Ver  |
                                | 2. Invalidate dependent metrics |
                                | 3. Persist new `template_rule`  |
                                | 4. Emit append-only Audit Event |
                                +---------------------------------+
```

### 4.1 Invalidation Cascade
When any cell value is modified by a reviewer or template propagation:
1. The document is bumped to a new immutable version (e.g., `v1` $\to$ `v2`).
2. An append-only record is entered in `audit_events` with `reviewer_id`, `reason`, `old_value`, `new_value`.
3. All `DerivedMetric` objects in the database that consume this cell's `fact_id` in their calculation DAG are marked `STALE` and scheduled for deterministic re-calculation.

---

## 5. Semantic Memory: Entity & Convention Registry

Financial reporting is plagued by inconsistent terminology. Semantic memory provides tenant-isolated institutional harmonization.

### 5.1 Entity Alias Registry
| Canonical Entity | Known Aliases / Variations | Scope |
| :--- | :--- | :--- |
| **Apple Inc.** | `AAPL`, `Apple`, `Apple Computer`, `The Company` (within Apple 10-K) | Global + Tenant |
| **Microsoft Corp.** | `MSFT`, `Microsoft`, `The Registrant` | Global + Tenant |
| **Alphabet Inc.** | `GOOGL`, `GOOG`, `Google LLC` | Global + Tenant |

### 5.2 Reporting Quirks & Conventions
- **Fiscal Calendar Definitions:** e.g., Apple's fiscal year ends on the last Saturday of September; Nvidia's fiscal year ends on the last Sunday of January.
- **Unit Conventions:** Tenant-level or publisher-level rules specifying whether numbers in unlabeled columns default to Thousands, Millions, or Exact USD.

---

## 6. Analyst Conversation Memory

When analysts interact with Argus via natural language Q&A, the session memory retains:
1. **Analytical Intent & Context:** The focus of inquiry (e.g., *"We are analyzing Q3 liquidity and free cash flow"*).
2. **Referenced Fact IDs:** Pointer lists to previously retrieved facts.
3. **Prohibited:** The conversation memory is **strictly prohibited from storing numerical values as plain text tokens**. When subsequent answers require prior figures, the agent retrieves the live `fact_id` directly from the PostgreSQL store.

---

## 7. Hard System Invariants (M1 – M4)

- **M1: No Fact Values in Memory:** Memory stores rules, layouts, aliases, and templates. Storing numerical values in memory is an architectural violation.
- **M2: Complete Auditability & Reversibility:** Every rule, override, or template change can be disabled, rolled back, and inspected through the audit log.
- **M3: Human Gate for Global Rules:** Rules that apply across multiple documents require explicit human reviewer confirmation.
- **M4: Strict Tenant Isolation:** Layout templates and entity registries are partitioned by `tenant_id`. No cross-tenant rule leakage is permitted.

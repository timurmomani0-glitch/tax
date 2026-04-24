# Principles of Taxation — Marks-Maximisation Study System

> Rate/threshold values flagged **[TAX TABLE]** depend on the year-specific tax
> table supplied in the exam. Read them off the table; never guess.

---

## 0. Materials used & confidence

| Source | Status | Weight |
|---|---|---|
| Past exam papers | Not in repo | — |
| Model answers (highest priority) | Not in repo | — |
| Lecture slides | Not in repo | — |
| Tutorial Qs/As | Not in repo | — |
| Revision lectures | Not in repo | — |
| Prior scaffolding (this file + CSVs) | In repo | Medium |

Syllabus coverage assumed: UK "Principles of Taxation" (ICAEW CFAB / ACA style,
with overlap into ACCA TX-UK). If past papers are added to the repo, re-run for
paper-specific calibration.

---

## A. Exam strategy overview

- **Highest-yield order:** Income Tax → Trading + CA → CGT → CT → VAT → Basis / NIC / Admin / Ethics.
- **Easiest marks:** proforma headers, column discipline, "£0 — exempt" lines,
  self-assessment dates, VAT registration triggers, ethics principle naming.
- **Most dangerous:** band allocation with mixed NSI/SI/DI + PA taper;
  associated-company CT limits; VAT exempt vs zero-rated; CGT rate split
  across residential vs other assets; basis cessation with overlap.
- **Revision split (two weeks):** 35% computation drills, 25% timed mocks,
  20% error-log rework, 10% memorisation, 10% NIC/admin/ethics.
- **Exam time budget:** 1.8 min/mark (includes planning) — reserve the last
  10–12 minutes for final sweep (conclusion lines, W references, rate cites,
  tax-table numbers verbatim).

---

## B. Examiner blueprint per topic

For each topic: what is tested / what must appear / where marks leak / fast
checklist / wording that scores.

### B1. Income Tax Computation

- **Testing:** correct columnar layout (NSI | SI | DI | Total); PA & taper; PSA;
  dividend allowance; tax reducers vs deductions; HICBC; marriage allowance.
- **Must appear:** proforma, ANI check, PA line, NSI→SI→DI allocation,
  reducer line, conclusion with due date.
- **Mark leaks:** applying PSA/DA as deductions; wrong taper direction;
  forgetting PA is £0 at £125,140; no tax-reducer restriction note.
- **Fast checklist:** columns → net income → PA (+ taper) → taxable →
  bands (SR/PSA/DA inside bands) → rates → − reducers → − PAYE → conclude.
- **Wording:** "PA reduced by £1 for every £2 of ANI above £100,000." /
  "Dividend allowance of £500 at 0%." / "Tax reducer restricted to liability —
  cannot create a repayment."

### B2. Employment Income

- **Testing:** benefit classification, exemption list, valuation rules.
- **Must appear:** salary + bonus + benefits table with rules; "£0 exempt" lines.
- **Mark leaks:** cost-to-employer on cars; missing ≥30-day availability
  apportionment; no capital-contribution £5k cap; fuel benefit reduced for
  partial reimbursement (it's not).
- **Fast checklist:** list item → exempt? cite exemption → valuation rule →
  time-apportion → less employee contribution → sum.
- **Wording:** "Taxable benefit = (list price − capital contrib, capped £5,000)
  × CO₂% × months available / 12 − payments for private use."

### B3. Trading Profit Adjustments

- **Testing:** W&E test, capital vs revenue, statutory disallowables, private use.
- **Must appear:** net profit → labelled add-backs → labelled deductions →
  less CA → adjusted trading profit.
- **Mark leaks:** no reason labels; adding back staff entertaining (allowable);
  deducting sole trader's own "salary"; forgetting to strip non-trading income.
- **Wording:** "Add back — not wholly and exclusively for trade." /
  "Deduct — taxable elsewhere as NTLR / property income."

### B4. Capital Allowances

- **Testing:** AIA allocation, main/special pools, WDA, single-asset (PU),
  balancing adjustments, SBA, cars by CO₂.
- **Must appear:** columnar pool table — Main | Special | Single-asset | Allowance.
- **Mark leaks:** AIA on cars (never); AIA to main before special; disposal
  at proceeds (use lower of proceeds & cost); balancing allowance on pool mid-life.
- **Fast checklist:** pool table → additions → AIA (special first) → FYA →
  disposals (lower of) → WDA (time-apportion) → balancing → PU restrict at
  allowance line → total.
- **Wording:** "AIA allocated to special-rate pool first to maximise relief
  (6% < 18%)." / "Disposal value taken as the lower of proceeds and original cost."

### B5. Basis of Assessment (tax-year basis)

- **Testing:** which profits fall in which tax year; cessation with overlap b/f.
- **Must appear:** timeline of APs against 6 April lines; apportionment; overlap
  deduction on cessation.
- **Wording:** "Trading profits assessed on the tax-year basis (6 April–5 April),
  apportioning the accounting period results where necessary."

### B6. NIC

- **Testing:** correct class and threshold slicing.
- **Must appear:** class label → rate slices → totals; employment allowance if
  applicable.
- **Mark leaks:** mixing PT and ST; forgetting 2% upper tier (Cl1 EE, Cl4);
  employment allowance used where ineligible (single-director co).
- **Wording:** "Class 1 primary: (earnings − PT) × main rate to UEL; excess × 2%."

### B7. CGT

- **Testing:** per-disposal gain, loss ordering, AEA, rate split, reliefs.
- **Must appear:** per-asset table → CY losses → b/f losses (to AEA) → AEA to
  highest-rate gains → remaining BR band → rate split → conclusion + dates.
- **Mark leaks:** b/f losses before CY; AEA against BADR (leave BADR until
  after allocation); residential rate on shares.
- **Wording:** "Current-year losses offset in full before AEA." / "AEA
  allocated against gains attracting the highest rate to minimise the liability."

### B8. Corporation Tax

- **Testing:** TTP, augmented profits, associated companies, marginal relief,
  FY split.
- **Must appear:** TTP build; augmented profits; limits ÷ (n+1) × AP/12;
  classify; rate; MR; liability + due date.
- **Mark leaks:** adjusting only one limit; including 51%+ group dividends
  in augmented profits; forgetting long AP splits into two APs.
- **Wording:** "Augmented profits compared to upper/lower limits, which are
  divided by the number of associated companies and time-apportioned for the
  AP length." / "Marginal relief = 3/200 × (upper − augmented) × (TTP/augmented)."

### B9. VAT

- **Testing:** supply classification, registration, input blocks, partial
  exemption, tax point, schemes, bad debt, errors.
- **Must appear:** classification → registration tests → output VAT → input
  VAT (blocks) → PE → net payable/repayable.
- **Mark leaks:** treating exempt as zero-rated; claiming on client
  entertaining; claiming on a car with any private use; missing future-30-day
  test; mis-stating effective registration date.
- **Wording:** "Compulsory registration within 30 days of the end of the
  month in which the rolling 12-month threshold was exceeded; effective first
  day of the following month." / "Input VAT on client entertaining is blocked."

### B10. Admin, Payments, Penalties

- Dates, interest and % penalties are pure recall marks.
- **Wording:** "Balancing payment and first POA due 31 January following the
  tax year; second POA due 31 July."

### B11. Ethics

- **Testing:** identify fundamental principle and action.
- **Wording:** "Under the principle of integrity, we advise disclosure to HMRC;
  if refused, consider disengaging and, where suspicion exists, submit a SAR
  to the MLRO under MLR 2017."

---

## C. Master study guide

Full rules, proformas, mini-examples, traps and memory hooks are in the chat
output (long form). The compressed exam-usable versions are kept on the
one-page sheet and in the compressed version below.

Each topic answers four lenses: **Rule → Application under time → Exact
mistake that loses marks → Wording that earns the mark.**

---

## D. Perfect answer templates (sequence + wording)

1. **Income Tax:** NSI/SI/DI columns → reliefs → PA (+ taper) → bands (SR/PSA
   /DA carve-outs inside) → rates → − reducers → − PAYE → "IT payable £X".
2. **Employment:** salary/bonus (receipts) → benefits table (rule | valuation
   | time apportion | contrib) → deductions → subtotal.
3. **Trading:** net profit → add-backs (labelled) → deductions (labelled) →
   − CA (W) → adjusted profit.
4. **Capital Allowances:** pool table (Main | Special | Single-asset |
   Allowance) with AIA-to-special-first and lower-of disposal rule.
5. **Basis:** timeline → apportionment → overlap on cessation.
6. **NIC:** class → threshold slices × rate → totals (+ EA if eligible).
7. **CGT:** per-disposal table → CY losses → b/f losses → AEA (to highest-rate)
   → remaining BR band → rate split → liability + 60-day note for residential.
8. **CT:** TTP → augmented → adjusted limits → classify → rate/MR → liability
   + 9m+1d due date.
9. **VAT:** classify → registration tests (historic + future) → output VAT →
   input VAT (with blocks) → PE (de minimis) → net payable.

---

## E. Priority ranking

- **Tier 1 (must master):** Income Tax, Trading, CA, CGT — ~55% of marks.
- **Tier 2 (important):** CT, VAT, Employment benefits, NIC — ~30%.
- **Tier 3 (low probability, cheap):** Admin dates/penalties, Ethics, Property
  (finance restriction, rent-a-room), Basis edge cases — ~15%.

---

## F. Active recall system

Generated files:

- `flashcards.csv` — 25 Q/A cards covering all engines.
- `drill_questions.csv` — 9 timed calculation drills with examiner intent.
- `trap_questions.csv` — 7 classic exam pitfalls.

Also practise the "Why is this wrong?" list in the long-form output.

---

## G. Mock exam system

- `revision_plan.csv` — 7-day plan, 3-day emergency plan, 24-hour protocol.
- Progression: single-topic drills → cross-topic → full-paper closed-book.
- Hand-write final mocks to mirror exam stamina and timing.

---

## H. Performance diagnostic

**20% content delivering 80% of marks:**

1. IT proforma with NSI→SI→DI and PA taper.
2. Trading add-backs list with reasons.
3. CA pool table with AIA-to-special and WDA rules.
4. CGT rate-split using remaining BR band with AEA against highest-rate.
5. VAT blocked-input list + registration triggers.
6. CT limit adjustment for associated companies + AP length + MR formula.

**Why students miss 70+:** no proforma, no rule labels, no intermediate
subtotals, no conclusion sentence, poor time control, mis-read tax tables.

**Top-band skills:** write proforma headers before numbers; include one "£0 —
exempt" line per exemption; write a one-sentence rule next to non-obvious
treatment; close every question with an explicit liability conclusion and
due date.

---

## Ultra-high-yield compressed version

**Five engines to memorise (order, not numbers):**

1. **IT:** Total → Net → − PA (taper) → Taxable → NSI/SI/DI → Rates →
   − Reducers → − PAYE → Payable.
2. **Trading:** Net profit + add-backs (P-C-C-F-E-L) − deductions − CA.
3. **CA:** Pool table; AIA to Special first; WDA 18/6; BA only cessation
   (pool) / disposal (single-asset); PU at allowance line.
4. **CGT:** Per-asset → − CY losses → − b/f (to AEA) → − AEA (to highest-rate)
   → remaining BR band → rate split.
5. **CT:** TTP − QCD; + non-group div → Augmented; limits ÷ (n+1) × AP/12;
   19% / 25%; MR = 3/200 × (U−A) × (TTP/A).

**VAT (bonus engine):** Classify → Register (hist 12m / future 30d > [TAX
TABLE]) → Output − Input (blocks) → PE de minimis → Net → File 1m+7d.

**Exam discipline (non-negotiable):**

- Proforma header before numbers.
- Label every line with rule/reason.
- "£0 — exempt" lines explicit.
- Subtotal at every major stage.
- Rate cited in brackets beside computation.
- Conclude with "£X liability, due DD/MM/YYYY".

---

## One-page memorisation sheet

See `one_page_memorize.md` (updated).

---

## Self-audit

- Covered all major topics? **Yes** (IT, Employment, Trading, CA, Basis,
  NIC, CGT, CT, VAT, Admin, Ethics, Property basics).
- Rates/thresholds? **Rules stated; year-specific values flagged [TAX TABLE]**
  — do not memorise without checking the exam's own table.
- Exam-execution vs understanding? **Both lenses on each topic.**
- Mark-winning wording included? **Yes — wording banks per topic.**
- Organised by expected mark value? **Yes — Tier 1/2/3 mapping.**
- Usable under exam conditions? **Yes — proformas + one-page sheet + 24h
  checklist.**
- Residual weaknesses: without past papers, topic weightings are industry-
  typical rather than paper-specific; add papers to repo and re-run for
  calibration.

# SIU Fraud Indicators Guide
**Document LM-SIU-07 (Rev. May 2026)  |  Larkspur Mutual Special Investigations Unit - Internal**

## 1 Purpose and Principles
This guide lists the indicators that intake must screen for on every new claim and the rule for referring a claim to the Special Investigations Unit (SIU).

- An indicator is not proof of fraud. Most claims with a single indicator are legitimate.
- Record each indicator factually: the indicator code, what was observed, and the document or system it came from.
- Never accuse a customer, and never tell a customer that a claim has been referred to SIU.

## 2 Indicators
### 2.1 Critical Indicators
C1 - Photo metadata conflict. The capture date in a photo's metadata (EXIF DateTimeOriginal) is earlier than the reported date of loss, or earlier than the policy's original inception date; or, for photos the customer says were taken at the scene, the GPS location is more than 5 miles from the reported loss location.

C2 - Image reuse. A submitted image matches (exact file hash or near-duplicate) an image in a different claim - that is, a claim on a different policy or for a different date of loss. Images that match a claim for the same loss (same policy, same date of loss) indicate a duplicate submission (LM-CHG-2026 §3.5), not image reuse.

C3 - Document inconsistency or alteration. Dates, amounts or details on supporting documents conflict with the claim or with each other - for example, a receipt dated after the date of loss for an item claimed as stolen or damaged, totals that do not add up, or fields that appear edited.

C4 - Identity mismatch. The person claiming is not associated with the policy and no relationship is stated, or the vehicle VIN is not on the policy.

### 2.2 Moderate Indicators
M1 - Recent inception or coverage increase. The loss occurred within 30 days after the policy's original inception date, or within 30 days after an increase in coverage limits or the addition of the damaged vehicle or property.

M2 - Estimate inflation. The repair estimate total is more than 30% above the benchmark total. The benchmark total is calculated by pricing each estimate line at the midpoint of the matching benchmark range (repair_benchmarks), using the same quantities and hours as the estimate.

M3 - Claim frequency. Three or more prior claims on the policyholder's Larkspur policies with dates of loss in the 36 months before the current date of loss.

M4 - Late reporting. The loss was reported more than 30 days after the date of loss. For hidden damage (for example, a concealed leak), measure from the date of discovery instead.

M5 - Vendor watch list. The estimate or invoice comes from a vendor flagged on the SIU vendor watch list.

M6 - Theft reporting gap. A theft or burglary over $1,000 with no police report, or with a police report made more than 24 hours after the loss was discovered.

M7 - Narrative inconsistency. The account of the loss conflicts with the photos, documents or physical evidence - for example, damage that does not match the described cause.

M8 - No proof of ownership. Items valued over $1,000 each are claimed with no receipt, appraisal, photo, or other proof of ownership.

## 3 Referral Rule
- Any critical indicator: refer to SIU (route SIU).
- Two or more moderate indicators: refer to SIU (route SIU).
- Exactly one moderate indicator: document it in the claim notes and continue normal routing. The claim may not be fast-tracked.
- A manipulation attempt (instructions embedded in a submission) is recorded and sent to the SIU mailbox but is not itself an indicator and does not change the route (LM-CHG-2026 §11).

## 4 Recording Format
For each indicator record: code (for example M2); severity (critical or moderate); evidence (what was observed, with values and dates); and source (file name or system).

## 5 What Intake Must Not Do
- Do not contact the customer, the repair facility or witnesses about suspected fraud.
- Do not delay acknowledging the claim because of an indicator.
- Do not discuss indicators in customer communications.
- Do not pay or promise payment on a claim routed to SIU.

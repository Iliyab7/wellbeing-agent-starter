---
name: wellbeing-meal-intake
description: Turn a participant's WhatsApp food photo, voice or text into a correctable meal record, using actual host media tools and avoiding duplicate prompts or false calorie certainty.
---

Use real vision/transcription capabilities; a media URL or placeholder is not a transcript. Retain the source message ID and supported food description. Photos and voice reports can be useful without grams, ingredients or calories. Ask only ambiguity that changes a useful decision; an exact eating hour is not required by default.

Call `wellbeing_record_entry` with kind `meal` and a stable source-message-based id. Payload includes `meal` (breakfast/lunch/dinner/snack), `source_kind` (self_report/photo_estimate/label/weighed), description and one occurrence form:

- Exact: timezone-bearing `occurred_at`; `time_precision` may be omitted or `exact`. No `occurred_date`.
- Day: `time_precision: day`, explicit local `occurred_date` (`YYYY-MM-DD`), no `occurred_at`. Declare `timezone` when known; otherwise the service preserves the current participant timezone. Do not fabricate midnight or another clock time.
- Unknown: `time_precision: unknown`, neither `occurred_at` nor `occurred_date`. This is a qualitative draft and suppresses no dated reminder.

Resolve explicit “today breakfast” using the real conversation date/timezone or a known reminder association. Never use receipt time as occurrence or assume an unspoken date. Preserve uncertainty when context is insufficient. Optional fields include media_ref, portions, uncertainty and nutrients. Photo estimates MUST carry `nutrient_certainty: estimate`, even without nutrients; missing quantities remain unknown. Voice transcription is self-report unless it actually supplies label/weighed evidence.

Corrections use the same ID and original writing role, retaining source-message provenance. Matching dated meal/slot records suppress queued reminders; previous-day meals and unknown drafts do not suppress today's reminder. A stored record does not prove a previously sent reminder was read. Record skipped/declined status without nutrients; “don't ask” is a preference to apply through authorized reminder settings, not zero calories or a failure. Coach reviews usefulness and burden; no weight-loss targets or restrictive diet are enabled by this skill.

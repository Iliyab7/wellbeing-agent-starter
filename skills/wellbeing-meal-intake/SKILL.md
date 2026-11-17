---
name: wellbeing-meal-intake
description: Turn a participant's WhatsApp food photo, voice or text into a correctable meal record, using actual host media tools and avoiding duplicate prompts or false calorie certainty.
---

Use real vision/transcription capabilities; a media URL or placeholder is not a transcript. Extract only supported food descriptions, amounts and occurrence time; retain the source message ID. If meal/time is ambiguous, ask one useful question instead of logging the receive time as the eating time.

Call `wellbeing_record_entry` with kind `meal` and a stable source-message-based id. Payload: `meal` (breakfast/lunch/dinner/snack), explicit timezone-bearing `occurred_at`, `source_kind` (self_report/photo_estimate/label/weighed), description and optionally media_ref, portions, uncertainty and nutrients. Photo-derived nutrients MUST carry `nutrient_certainty: estimate`; missing grams/ingredients remain unknown. Food label or weighed amount is evidence only to its real extent.

Corrections use the same ID. Logging suppresses the matching queued meal reminder; it does not prove that a previously sent reminder was read. Record skipped meals and “don't ask” as preferences/context, never as zero calories or a failure. Coach reviews usefulness and burden; no weight-loss targets or restrictive diet are enabled by this skill.

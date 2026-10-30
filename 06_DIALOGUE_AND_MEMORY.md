# 06 — Dialogue Management and Conversation Memory

## 1. Principle

Conversation control is deterministic application logic. The LLM proposes intent and slot values; the dialogue manager decides what to ask, what is missing, whether to confirm, when to run rules and how to persist state.

## 2. Conversation states

Initial state enum:

- `NEW`
- `GREETING`
- `DISCOVERING_INTENT`
- `COLLECTING_PROFILE`
- `CONFIRMING_CRITICAL_FACTS`
- `READY_TO_EVALUATE`
- `EVALUATING`
- `PRESENTING_RESULTS`
- `FOLLOW_UP`
- `WAITING_FOR_FARMER`
- `COMPLETED`
- `PAUSED`
- `FAILED_RETRYABLE`

State transitions must be explicit and unit-tested. A user message cannot directly set the state; only the dialogue manager can.

*Milestone M3 implemented DialogueState and DialogueStateMachine in `app/core/dialogue/state_machine.py` with explicit transition graph enforcement. See `docs/M3_DIALOGUE_AND_PERSISTENT_MEMORY.md`.*

## 3. Required flow

```text
NEW -> GREETING -> DISCOVERING_INTENT
                         |
                         v
                 COLLECTING_PROFILE
                         |
             required slot missing?
                  /             \
                yes              no
                 |                |
         ask one question     confirm critical facts
                 |                |
           WAITING_FOR_FARMER <- -
                 |
            merge response
                 |
         COLLECTING_PROFILE
                 |
             all required?
                 v
          READY_TO_EVALUATE
                 |
             EVALUATING
                 |
          PRESENTING_RESULTS
                 |
             FOLLOW_UP
```

## 4. Slot structure

Each slot must hold more than just a value:

```json
{
  "slot": "land_area",
  "raw_value": "ಮೂರುವರೆ ಎಕರೆ",
  "value": 3.5,
  "unit": "acre",
  "normalized_value": 3.5,
  "normalized_unit": "acre",
  "status": "CONFIRMED",
  "provenance": "USER_STATED",
  "source_turn_id": "turn_002",
  "normalizer_version": "kn-agri-lexicon-0.1.0",
  "updated_at": "2026-10-30T12:00:00Z"
}
```

Allowed `status`: `MISSING`, `PROPOSED`, `CONFIRMED`, `CONFLICTED`, `UNKNOWN`, `NOT_APPLICABLE`.  
Allowed provenance values: `USER_STATED`, `USER_CONFIRMED`, `OFFICIAL_SOURCE`, `SYSTEM_DERIVED`. Never use `OFFICIAL_SOURCE` unless an actual authorized source integration provides the evidence.

## 5. Required slot selection

Each scheme rule definition declares its required slots. A discovery request may initially require only:

- state;
- district;
- assistance need.

Additional slots are asked only when the candidate scheme or category needs them. For example:

- crop insurance typically needs crop, season and notified area/season applicability;
- irrigation support needs the requested irrigation type and relevant land/location conditions from the approved scheme definition;
- income support needs official scheme's currently verified criteria and relevant exclusions;
- equipment assistance needs equipment category and conditions defined by the demo rule set.

Do not ask all fields in a universal fixed form.

## 6. One question at a time

Question selection algorithm:

1. determine current intent;
2. load candidate schemes and their declared required slots;
3. merge already-confirmed profile facts and current utterance;
4. choose the highest-priority missing slot for which a question is meaningful;
5. ask one plain Kannada question;
6. wait and preserve state.

Question templates must be stored separately and reviewed by a Kannada speaker. Avoid asking personal information not required for the current path.

## 7. Corrections and conflicts

Examples:

- Farmer: “ನಾಲ್ಕು ಎಕರೆ.”
- Assistant: confirms four acres.
- Farmer: “ಇಲ್ಲ, ಮೂರೂವರೆ ಎಕರೆ.”
- System: identify correction intent; replace active slot with 3.5 acres; status becomes `PROPOSED` until read-back/confirmation if needed; invalidate prior recommendation run that used 4 acres.

If a new utterance conflicts with an old fact but is not clearly a correction, ask which value is current. Do not silently overwrite verified evidence.

## 8. Context retrieval policy

For every turn, load:

- farmer's current confirmed agricultural profile;
- active conversation state;
- current conversation slots;
- short summary if necessary;
- up to a limited number (configurable, default 6) of recent retained turns;
- only scheme content relevant to the current intent.

Do not pass the full lifetime conversation history to the LLM. Do not use a vector database for the MVP.

## 9. Context hierarchy and conflict resolution

1. Explicit current-turn correction.
2. Explicit current-turn user statement.
3. Confirmed slot in active conversation.
4. Confirmed profile fact with timestamp.
5. Unconfirmed extraction proposal.
6. No data (`UNKNOWN`).

A government-verified fact can outrank a self-reported fact only when the integration is real, authorized, current and auditable. No government integration is assumed in MVP.

## 10. Memory retention

- Store structured slots as the canonical memory.
- Store transcripts/message content only according to a clear consent and retention policy.
- Do not store raw audio by default.
- Summary must be derived from retained data and must not contain hidden sensitive inferences.
- Deleting a farmer profile must delete or irreversibly anonymize linked content according to the approved retention policy.

## 11. Follow-up examples

- “ನಿಮ್ಮ ಜಮೀನು ಯಾವ ಜಿಲ್ಲೆಯಲ್ಲಿ ಇದೆ?”
- “ನೀವು ಯಾವ ಬೆಳೆ ಬೆಳೆದಿದ್ದೀರಿ?”
- “ಈ ಬೆಳೆ ಯಾವ ಹಂಗಾಮಿನಲ್ಲಿ ಬೆಳೆದಿದ್ದೀರಿ?”
- “ಜಮೀನು ನಿಮ್ಮ ಹೆಸರಿನಲ್ಲಿದೆಯೇ ಅಥವಾ ಬಾಡಿಗೆಗೆ ಕೃಷಿ ಮಾಡುತ್ತಿದ್ದೀರಾ?”

These are example wording only. Final spoken Kannada must be reviewed for dialect neutrality, clarity and respectful phrasing.

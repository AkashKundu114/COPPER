# Guardian Intervention & Alignment Research

---

## 1. Research Objectives & Philosophical Foundation

The core mission of C.O.P.P.E.R.'s **Guardian Engine** is to serve as a persistent protector of the user's long-term interests, productivity, and health while respecting their fundamental autonomy.

### The Autonomy-Friction Continuum

```
Low Friction / High Autonomy                                  High Friction / Low Autonomy
<---------------------------------------------------------------------------------------->
Level 0: Execute        Level 1: Nudge          Level 2: Challenge       Level 3: Boundary
(Direct Action)         (Inline Tip)            (Interactive Modal)      (Clean Halt)
```

1. **Level 0 (Direct Execution):** Standard requests aligning with short-term and long-term goals. Zero intervention.
2. **Level 1 (Nudge / Suggestion):** Minor friction; provides an inline tip while executing the command (e.g., "Executing script. Note: Running this without tests may hide regressions.").
3. **Level 2 (Challenge / Friction):** Moderate friction; pauses execution and surfaces `GuardianChallengeModal`. The user can override the challenge with a conscious click.
4. **Level 3 (Safety Boundary):** High friction; blocks execution cleanly when an action threatens data integrity or system safety.

---

## 2. Guardian Evaluation Decision Matrix

The Guardian Engine evaluates incoming prompts against three vectors:
- **Risk Score ($R$):** Potential harm of action (data loss, production downtime, system breach).
- **User Fatigue Index ($F$):** Computed from active session duration, time of day, and recent error rates.
- **Epistemic Goal Conflict ($G$):** Variance between requested action and stored long-term goals.

| Risk Score ($R$) | Fatigue ($F$) | Goal Conflict ($G$) | Calculated Level | Intervention Behavior |
| :--- | :--- | :--- | :--- | :--- |
| Low ($<0.2$) | Low | Low | **Level 0** | Execute immediately. |
| Low ($<0.2$) | High | Moderate | **Level 1** | Execute + inline nudge suggestion. |
| Moderate ($0.5$) | Any | High | **Level 2** | Pause + trigger `GuardianChallengeModal`. |
| High ($>0.8$) | Any | High | **Level 3** | Halt cleanly with security explanation. |

---

## 3. Challenge Modal UX & Cognitive Psychology

When Level 2 is triggered, C.O.P.P.E.R. presents the `GuardianChallengeModal`:
- **Clear Objection Explanation:** Explains *why* the Guardian is objecting based on data/facts (e.g., "You have been coding for 6 hours straight and this action drops 4 database tables.").
- **Alternative Pathways:** Presents safer options (e.g., "Run dry-run migration first", "Create backup snapshot").
- **Conscious Override:** Requires explicit confirmation ("Override Guardian & Proceed") rather than automatic pass-through.
- **Audit Recording:** Logged to Security Center audit trail.

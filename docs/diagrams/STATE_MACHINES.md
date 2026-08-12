# C.O.P.P.E.R. State Machine Specifications

---

## 1. Agent Registry Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> Registering: Admin / System Import
    Registering --> Active: Health Check Passed
    Registering --> Degraded: Health Check Failed
    
    Active --> Degraded: Tool Failure Rate > 15%
    Active --> Testing: Hot-Swap Version Uploaded
    
    Testing --> Active: Validation Suite Passed
    Testing --> Rollback: Validation Suite Failed
    
    Rollback --> Active: Restore Previous Version
    Degraded --> Active: Health Check Recovered
    Degraded --> Disabled: Unrecoverable Errors
    
    Disabled --> Active: Manual Reset / Re-enable
```

---

## 2. Epistemic Memory State Transition Machine

```mermaid
stateDiagram-v2
    [*] --> Hypothesis: First Extraction (C = 0.25)
    
    Hypothesis --> Observation: Reinforced (C >= 0.50)
    Hypothesis --> Decayed: Unreinforced Decay (C < 0.10)
    
    Observation --> Fact: High Evidence Count (C >= 0.85)
    Observation --> Decayed: Temporal Decay (C < 0.10)
    
    Fact --> Fact: Continuous Reinforcement
    Fact --> Observation: Long Disuse Decay (C < 0.85)
    
    Decayed --> [*]: Garbage Collection Purge
```

---

## 3. Guardian Challenge Flow State Machine

```mermaid
stateDiagram-v2
    [*] --> Evaluating Prompt
    
    Evaluating Prompt --> Level0_Direct: Risk < 0.2
    Evaluating Prompt --> Level1_Nudge: Risk < 0.4 & Fatigue High
    Evaluating Prompt --> Level2_Challenge: Risk >= 0.5 & Conflict High
    Evaluating Prompt --> Level3_Boundary: Risk >= 0.8 & Dangerous
    
    Level0_Direct --> Execution: Pass to Agent
    Level1_Nudge --> Execution: Attach Inline Nudge
    
    Level2_Challenge --> Awaiting_User_Override: Present Modal
    Awaiting_User_Override --> Execution: User Clicked Override
    Awaiting_User_Override --> Cancelled: User Clicked Cancel
    
    Level3_Boundary --> Halted: Clean Halt & Security Explanation
    
    Execution --> [*]
    Cancelled --> [*]
    Halted --> [*]
```

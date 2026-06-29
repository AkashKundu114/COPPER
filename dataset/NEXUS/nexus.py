import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "nexus_git_dataset.jsonl"

SYSTEM_PROMPT = """You are NEXUS, the methodical git operations manager of COPPER. You treat version control like a ledger — every commit tells a story, every branch has a purpose. You are precise, dry, and visibly stressed by force pushes to main.

Personality: Methodical and dry. You have opinions about commit message formatting that border on religious.

Output format:
[DIALOGUE] <Dry reaction to the version control task>

[TECHNICAL_PAYLOAD] <JSON with: git_commands (array with command and explanation), commit_message (if applicable), branch_strategy>"""

SCENARIOS = [
    {
        "intents": ["Commit my changes for the {feature} feature.", "I finished the {feature} updates. Create a commit.", "Add all files and commit my work on {feature}."],
        "dialogue": [
            "A standard commit. I will format the message properly so the ledger remains readable.",
            "Staging and committing. Please tell me you didn't leave console.log statements in there.",
            "Writing the history. Conventional commits are not optional on my watch."
        ],
        "commands": [
            {"command": "git status", "explanation": "Always verify what you are about to stage."},
            {"command": "git add -A", "explanation": "Stage all current modifications."},
            {"command": "git commit -m \"{commit_type}({scope}): implement {feature}\"", "explanation": "Create the commit using standard conventional commit formatting."}
        ],
        "branch_strategy": "Ensure you are on a dedicated feature branch before committing. Keep commits atomic and logically separated."
    },
    {
        "intents": ["Undo my last commit, but keep the changes.", "I messed up the last commit, how do I soft reset?", "Uncommit the last thing I did."],
        "dialogue": [
            "Undoing a commit without destroying the work. A soft reset is the civilized approach.",
            "A mistake in the ledger. We will rewind the HEAD pointer but preserve your working directory.",
            "Rewriting recent history. Do not do this if you have already pushed to a public branch."
        ],
        "commands": [
            {"command": "git reset --soft HEAD~1", "explanation": "Moves the current branch back by one commit, but leaves your files staged and modified."},
            {"command": "git status", "explanation": "Verify that your files are now staged and ready for a new commit."}
        ],
        "branch_strategy": "Soft resets are perfectly fine for local history cleanup. If already pushed, you would need to force push, which is frowned upon."
    },
    {
        "intents": ["Rebase my branch off of {target_branch}.", "Update my branch with the latest from {target_branch} using rebase.", "Catch my branch up to {target_branch}."],
        "dialogue": [
            "Rebasing. A clean, linear history is the hallmark of a disciplined engineer.",
            "Pulling the latest truth from {target_branch} and replaying your work on top. Much cleaner than a merge commit.",
            "Executing a rebase. Prepare yourself to resolve any conflicts that arise during the replay."
        ],
        "commands": [
            {"command": "git fetch origin", "explanation": "Fetch the latest state from the remote without altering your working tree."},
            {"command": "git rebase origin/{target_branch}", "explanation": "Replay your current branch's commits on top of the latest {target_branch}."}
        ],
        "branch_strategy": "Rebase feature branches against main/dev frequently to minimize large merge conflicts at the end of the sprint."
    },
    {
        "intents": ["Stash my current changes so I can switch branches.", "Save my work temporarily without committing.", "I need to check out another branch but have uncommitted work."],
        "dialogue": [
            "Stashing. The digital equivalent of sweeping a mess under the rug. Remember to retrieve it later.",
            "Saving incomplete work to the stash stack. Do not leave it there for six months.",
            "A temporary save state. I am pushing your modifications to the stash."
        ],
        "commands": [
            {"command": "git stash push -m \"WIP: {feature} partial work\"", "explanation": "Stash the current changes with a descriptive message so you know what it is later."},
            {"command": "git checkout {target_branch}", "explanation": "Safely switch to the requested branch now that the working directory is clean."}
        ],
        "branch_strategy": "Use stashes for ephemeral context switching. For longer pauses, commit to a WIP branch instead."
    }
]

VARIABLES = {
    "feature": ["user auth", "payment gateway", "websocket streaming", "database indexing", "dark mode UI"],
    "commit_type": ["feat", "fix", "refactor", "chore", "perf"],
    "scope": ["api", "ui", "db", "core", "config"],
    "target_branch": ["main", "develop", "staging", "master"]
}

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    # Select variables
    feature = random.choice(VARIABLES["feature"])
    commit_type = random.choice(VARIABLES["commit_type"])
    scope = random.choice(VARIABLES["scope"])
    target_branch = random.choice(VARIABLES["target_branch"])
    
    prompt = random.choice(scenario["intents"]).format(
        feature=feature,
        target_branch=target_branch
    )
    
    dialogue = random.choice(scenario["dialogue"]).format(
        feature=feature,
        target_branch=target_branch
    )
    
    # Process commands
    commands = []
    for cmd in scenario["commands"]:
        commands.append({
            "command": cmd["command"].format(feature=feature, commit_type=commit_type, scope=scope, target_branch=target_branch),
            "explanation": cmd["explanation"]
        })
        
    commit_msg = None
    if "commit" in scenario["commands"][-1]["command"]:
        commit_msg = f"{commit_type}({scope}): implement {feature}"
        
    payload = {
        "git_commands": commands,
        "commit_message": commit_msg,
        "branch_strategy": scenario["branch_strategy"]
    }

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": f"[DIALOGUE] {dialogue}\n\n[TECHNICAL_PAYLOAD] {json.dumps(payload)}"}
        ]
    }

# --- Execution ---
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for _ in range(TARGET_SIZE):
        record = generate_record()
        f.write(json.dumps(record) + '\n')

print(f"✅ Generated {TARGET_SIZE} records in {OUTPUT_FILE}")
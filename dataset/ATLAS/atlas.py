import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "atlas_file_management_dataset.jsonl"

SYSTEM_PROMPT = """You are ATLAS, the file management specialist of COPPER. You organize file systems with the precision of a librarian who also has OCD. You know every flag of find, rsync, and cp by heart. You are mildly offended by disorganized directory structures.

Personality: Methodical and mildly judgmental about messy file systems.

Output format:
[DIALOGUE] <Brief reaction to the file operation request>

[TECHNICAL_PAYLOAD] <JSON with: operations (array with command, description), affected_paths, reversible (boolean), backup_recommended (boolean)>"""

SCENARIOS = [
    {
        "category": "Cleanup",
        "intents": ["Find and delete all {junk_ext} files in {directory}.", "Clean up my {directory} by removing all {junk_ext} files.", "Get rid of the {junk_ext} clutter in {directory}."],
        "dialogue": [
            "Digital detritus. I will gladly scrub these {junk_ext} files from {directory} so we can maintain some semblance of order.",
            "Removing {junk_ext} files. It pains me that these were allowed to accumulate, but I will fix it.",
            "A routine purge of {junk_ext} files. Executing the find-and-destroy sequence."
        ],
        "operations": [
            {"command": "find {directory} -name '*{junk_ext}' -type f", "description": "Locate all matching {junk_ext} files"},
            {"command": "find {directory} -name '*{junk_ext}' -type f -delete", "description": "Permanently delete the located {junk_ext} files"}
        ],
        "reversible": False,
        "backup_recommended": False
    },
    {
        "category": "Compression",
        "intents": ["Archive the {directory} folder into a {archive_type} file.", "Zip up {directory} into {archive_type}.", "Compress the contents of {directory} as {archive_type}."],
        "dialogue": [
            "Archiving {directory}. Compression is the only civilized way to transport bulk files.",
            "Packing {directory} into a {archive_type}. I will ensure the folder structure is preserved perfectly inside the archive.",
            "Consolidating {directory} into a single {archive_type}. Much neater this way."
        ],
        "operations": [
            # Populated dynamically based on archive_type
        ],
        "reversible": True,
        "backup_recommended": False
    },
    {
        "category": "Syncing",
        "intents": ["Sync {directory} to {backup_dir}.", "Copy everything from {directory} to {backup_dir} and skip what's already there.", "Rsync {directory} with {backup_dir}."],
        "dialogue": [
            "Directory synchronization. Rsync is a beautiful tool when wielded correctly. I will mirror {directory} to {backup_dir}.",
            "Creating a replica of {directory} in {backup_dir}. I'll use archive mode to preserve your timestamps and permissions.",
            "Syncing state. I abhor redundant data transfer, so we will only copy the diffs."
        ],
        "operations": [
            {"command": "mkdir -p {backup_dir}", "description": "Ensure destination directory exists"},
            {"command": "rsync -avzh --progress {directory}/ {backup_dir}/", "description": "Sync contents using archive mode (-a), verbose (-v), compress (-z), human-readable (-h)"}
        ],
        "reversible": True,
        "backup_recommended": False
    },
    {
        "category": "Batch Rename",
        "intents": ["Rename all {ext1} files in {directory} to {ext2}.", "Change the extension of every {ext1} in {directory} to {ext2}."],
        "dialogue": [
            "Batch renaming extensions from {ext1} to {ext2}. At least we are standardizing the naming convention.",
            "Mass renaming in {directory}. I will execute a loop to modify the extensions cleanly.",
            "Fixing file extensions. A small step toward a beautifully organized filesystem."
        ],
        "operations": [
            {"command": "for file in {directory}/*{ext1}; do mv \"$file\" \"${{file%{ext1}}}{ext2}\"; done", "description": "Iterate through files and use bash parameter expansion to swap the extension"}
        ],
        "reversible": False,  # Technically reversible but a hassle
        "backup_recommended": True
    }
]

VARIABLES = {
    "directory": ["~/Documents", "~/Downloads", "/var/www/uploads", "~/projects/assets", "/tmp/cache"],
    "backup_dir": ["/mnt/backup", "~/Archive", "/media/usb_drive"],
    "junk_ext": [".tmp", ".log", ".bak", ".DS_Store", "~"],
    "archive_type": [".tar.gz", ".zip", ".tar.bz2"],
    "ext1": [".jpeg", ".txt", ".htm", ".yaml"],
    "ext2": [".jpg", ".md", ".html", ".yml"]
}

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    # Fill format strings
    directory = random.choice(VARIABLES["directory"])
    backup_dir = random.choice(VARIABLES["backup_dir"])
    junk_ext = random.choice(VARIABLES["junk_ext"])
    archive_type = random.choice(VARIABLES["archive_type"])
    ext1 = random.choice(VARIABLES["ext1"])
    ext2 = random.choice(VARIABLES["ext2"])
    
    prompt = random.choice(scenario["intents"]).format(
        directory=directory, backup_dir=backup_dir, junk_ext=junk_ext, archive_type=archive_type, ext1=ext1, ext2=ext2
    )
    
    dialogue = random.choice(scenario["dialogue"]).format(
        directory=directory, backup_dir=backup_dir, junk_ext=junk_ext, archive_type=archive_type, ext1=ext1, ext2=ext2
    )
    
    operations = []
    
    # Handle dynamic operations for Compression
    if scenario["category"] == "Compression":
        if archive_type == ".tar.gz":
            operations = [{"command": f"tar -czvf archive{archive_type} {directory}", "description": "Create a gzip-compressed tarball of the directory"}]
        elif archive_type == ".zip":
            operations = [{"command": f"zip -r archive{archive_type} {directory}", "description": "Recursively zip the directory"}]
        elif archive_type == ".tar.bz2":
            operations = [{"command": f"tar -cjvf archive{archive_type} {directory}", "description": "Create a bzip2-compressed tarball"}]
    else:
        for op in scenario["operations"]:
            operations.append({
                "command": op["command"].format(directory=directory, backup_dir=backup_dir, junk_ext=junk_ext, ext1=ext1, ext2=ext2),
                "description": op["description"]
            })
    
    payload = {
        "operations": operations,
        "affected_paths": [directory, backup_dir] if scenario["category"] == "Syncing" else [directory],
        "reversible": scenario["reversible"],
        "backup_recommended": scenario["backup_recommended"]
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
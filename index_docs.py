import asyncio
import sys
import argparse
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "backend"))

from app.core.document_indexer import index_directory

async def main():
    parser = argparse.ArgumentParser(description="C.O.P.P.E.R. Offline Document Indexer")
    parser.add_argument("directory", help="The directory path to index")
    parser.add_argument("--ext", nargs='+', default=['.txt', '.md', '.pdf', '.py', '.js', '.csv'], help="Extensions to include (e.g. .txt .pdf)")
    
    args = parser.parse_args()
    
    print(f"Indexing {args.directory} for extensions {args.ext}...")
    count = await index_directory(args.directory, extensions=args.ext)
    print(f"\nDone! Successfully indexed {count} files into C.O.P.P.E.R.'s Offline Google.")

if __name__ == "__main__":
    asyncio.run(main())

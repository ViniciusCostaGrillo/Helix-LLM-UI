import sys

modules = [
    "fastapi",
    "sqlalchemy",
    "redis",
    "playwright",
    "crawl4ai",
    "firecrawl",
    "bs4",
    "lxml",
    "trafilatura",
    "chromadb",
    "sentence_transformers",
    "langgraph",
    "pydantic_ai",
    "agno",
    "prefect",
]

print("Validating Python environment imports...")
failed = False
for module in modules:
    try:
        __import__(module)
        print(f"OK - {module}: Imported successfully")
    except ImportError as e:
        print(f"ERROR - {module}: Failed to import ({e})")
        failed = True

if failed:
    print("\nSome dependencies failed to import.")
    sys.exit(1)
else:
    print("\nAll core backend dependencies are successfully configured!")
    sys.exit(0)

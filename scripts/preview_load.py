from src.app.ingest.loader import load_urls

def main() -> None:
    docs = load_urls()
    print(f"#docs: {len(docs)}")

    if not docs:
        print("No documents loaded.")
        return
    
    preview = docs[0].page_content[:500]
    print("Preview (first 500 chars):")
    print(preview)

if __name__ == "__main__":
    main()
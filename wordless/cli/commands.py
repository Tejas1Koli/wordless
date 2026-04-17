"""Command handlers for Wordless CLI."""

from pathlib import Path
from wordless.indexer.parser import index_repo
from wordless.indexer.embedder import embed
from wordless.indexer.store import upsert
from wordless.indexer.callgraph import build_callgraph
from wordless.search import search_code
from wordless import config
from wordless.config_manager import set_config


class IndexManager:
    """Manages indexing and searching operations."""

    def __init__(self):
        self.current_repo = None
        self.callgraph = None
        # Load last indexed repo from config if available
        self.current_repo = config.REPO_PATH

    def index(self, repo_path: str) -> None:
        """Parse, embed, and store a repository."""
        repo_path = Path(repo_path).resolve()
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository path not found: {repo_path}")

        print(f"📍 Indexing {repo_path}...")
        
        # Step 1: Parse code locally
        print("  1️⃣ Parsing Python files...")
        chunks = index_repo(str(repo_path))
        
        if not chunks:
            print("⚠️  No Python files found to index.")
            return

        print(f"     ✓ Found {len(chunks)} chunks")
        
        # Step 2: Build call graph locally
        print("  2️⃣ Building call graph...")
        callgraph = build_callgraph(str(repo_path))
        
        # Step 3: Enrich chunks with call graph relationships
        print("  3️⃣ Enriching with relationships...")
        from wordless.indexer.callgraph import expand
        for chunk in chunks:
            related = expand(chunk.name, callgraph, hops=config.DEFAULT_HOPS)
            chunk.related_functions = list(related)
        
        # Step 4: Embed and store via cloud gateway
        print(f"  4️⃣ Embedding via gateway ({config.GATEWAY_URL})...")
        embeddings = embed([c.source for c in chunks])
        
        print("  5️⃣ Storing in vector DB...")
        upsert(chunks, embeddings)
        
        self.current_repo = str(repo_path)
        self.callgraph = callgraph
        
        # Save repo path to config
        set_config("repo_path", str(repo_path))
        print("✅ Indexing complete. Ready to search.")

    def search(self, query: str, hops: int = None) -> str:
        """Search indexed code and return results."""
        if not self.current_repo:
            return "❌ Error: No repo indexed. Run 'wordless index <path>' first."
        
        if not self.callgraph:
            # Rebuild callgraph if needed
            self.callgraph = build_callgraph(self.current_repo)
            if not self.callgraph:
                return "❌ Error: Failed to build call graph."

        if hops is None:
            hops = config.DEFAULT_HOPS

        return search_code(query, self.callgraph, hops=hops)

    def status(self) -> str:
        """Return current indexing status."""
        if self.current_repo:
            return f"📦 Indexed repo: {self.current_repo}"
        return "📦 No repo indexed yet. Run: wordless index <path>"

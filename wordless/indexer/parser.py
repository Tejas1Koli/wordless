from tree_sitter import Language, Parser
import tree_sitter_python as tspython
from pathlib import Path
from dataclasses import dataclass

@dataclass
class CodeChunk:
    name: str
    type: str        # "function" or "class"
    source: str
    file: str
    line: int

def extract_chunks(file_path: str) -> list[CodeChunk]:
    PY_LANGUAGE = Language(tspython.language())
    parser = Parser(PY_LANGUAGE)
    
    source = Path(file_path).read_bytes()
    tree = parser.parse(source)
    
    chunks = []
    cursor = tree.walk()
    
    def visit(node):
        if node.type in ("function_definition", "class_definition"):
            name_node = node.child_by_field_name("name")
            name = name_node.text.decode() if name_node else "unknown"
            chunks.append(CodeChunk(
                name=name,
                type="function" if node.type == "function_definition" else "class",
                source=source[node.start_byte:node.end_byte].decode(),
                file=file_path,
                line=node.start_point[0] + 1,
            ))
        for child in node.children:
            visit(child)
    
    visit(tree.root_node)
    return chunks

def index_repo(repo_path: str) -> list[CodeChunk]:
    chunks = []
    SKIP = {"__pycache__", ".venv", "venv", "node_modules", "site-packages", 
            ".git", "dist", "build", ".tox", "egg-info", ".eggs"}
    
    for path in Path(repo_path).rglob("*.py"):
        if any(p in SKIP for p in path.parts):
            continue
        try:
            chunks.extend(extract_chunks(str(path)))
        except Exception:
            continue
    return chunks
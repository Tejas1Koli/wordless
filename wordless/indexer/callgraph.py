import ast
from pathlib import Path
from collections import defaultdict

# maps function name → set of functions it calls
CallGraph = dict[str, set[str]]

def build_callgraph(repo_path: str) -> CallGraph:
    graph: CallGraph = defaultdict(set)
    SKIP = {"__pycache__", "site-packages", "dist-packages", ".git", "node_modules"}
    repo = Path(repo_path)

    for path in repo.rglob("*.py"):
        if any(p in SKIP for p in path.parts):
            continue
        # skip venv
        if any((Path(*path.parts[:i+1]) / "pyvenv.cfg").exists()
               for i in range(len(path.parts))):
            continue
        try:
            tree = ast.parse(path.read_text())
        except Exception:
            continue

        # Relative file path for cleaner keys
        rel_file = str(path.relative_to(repo))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                caller = f"{rel_file}::{node.name}"
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            # Simple call: assume same file (or builtin)
                            callee_name = child.func.id
                            # Try to find it in same file, else store as-is
                            graph[caller].add(f"{rel_file}::{callee_name}")
                        elif isinstance(child.func, ast.Attribute):
                            # Attribute call: store as-is (hard to resolve without import analysis)
                            graph[caller].add(child.func.attr)
    return dict(graph)

def expand(name: str, graph: CallGraph, hops: int = 3) -> set[str]:
    """Get all functions within N hops of name."""
    visited = set()
    frontier = {name}
    
    # build reverse graph (callers)
    reverse: CallGraph = defaultdict(set)
    for caller, callees in graph.items():
        for callee in callees:
            reverse[callee].add(caller)
    
    for _ in range(hops):
        next_frontier = set()
        for fn in frontier:
            next_frontier |= graph.get(fn, set())   # callees
            next_frontier |= reverse.get(fn, set())  # callers
        frontier = next_frontier - visited
        visited |= frontier
    
    return visited
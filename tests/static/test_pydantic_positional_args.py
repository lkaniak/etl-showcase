import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOTS = [
    REPO_ROOT / "packages" / "etl" / "src",
    REPO_ROOT / "apps" / "etl-usage-example" / "src",
    REPO_ROOT / "services" / "external-api-example" / "src",
]


def _iter_python_files():
    for root in SOURCE_ROOTS:
        yield from root.rglob("*.py")


def _base_name(base: ast.expr) -> str | None:
    if isinstance(base, ast.Name):
        return base.id
    if isinstance(base, ast.Attribute):
        return base.attr
    return None


def _call_name(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _parse_source_files() -> dict[Path, ast.Module]:
    trees: dict[Path, ast.Module] = {}
    for path in _iter_python_files():
        trees[path] = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return trees


def _collect_pydantic_model_names(trees: dict[Path, ast.Module]) -> set[str]:
    class_bases: dict[str, set[str]] = {}
    for tree in trees.values():
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = {name for base in node.bases if (name := _base_name(base))}
                class_bases.setdefault(node.name, set()).update(bases)

    model_names = {name for name, bases in class_bases.items() if "BaseModel" in bases}

    changed = True
    while changed:
        changed = False
        for name, bases in class_bases.items():
            if name not in model_names and bases & model_names:
                model_names.add(name)
                changed = True

    return model_names


def test_pydantic_models_are_constructed_with_keyword_arguments():
    """Statically catch `Model("a", "b")` calls that raise
    `TypeError: BaseModel.__init__() takes 1 positional argument` in pydantic v2.

    This runs on plain source text (no imports, no Docker, no DB) so it fails fast
    for every new pydantic model call added to packages/etl, apps/etl-usage-example,
    or services/external-api-example.
    """
    trees = _parse_source_files()
    model_names = _collect_pydantic_model_names(trees)
    assert model_names, "Expected to find at least one pydantic BaseModel subclass in source"

    violations = []
    for path, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = _call_name(node.func)
                if name in model_names and node.args:
                    rel_path = path.relative_to(REPO_ROOT)
                    violations.append(f"{rel_path}:{node.lineno} -> {name}(...) uses positional arguments")

    assert not violations, (
        "Pydantic BaseModel subclasses must be constructed with keyword arguments only.\n"
        "Positional args break at runtime in pydantic v2 and silently pass type checkers.\n"
        "Offending calls:\n" + "\n".join(violations)
    )

"""
ETABS CHM → Python API Index Builder
=====================================
Reads all extracted HTML pages from the ETABS v1 CHM, parses each method/property,
converts C# signatures to Python calling conventions, and builds a searchable
JSON index + sentence-transformer embeddings saved to etabs_api_index.json
and etabs_api_embeddings.npy.

Run once:
    python build_api_index.py

Output:
    src/etabs_mcp/etabs_api_index.json   (bundled into exe via spec)
    src/etabs_mcp/etabs_api_embeddings.npy
"""

import json
import os
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Tag

CHM_HTML_DIR = Path(r"C:\Users\USER\Documents\etabs-mcp\chm_extracted\html")
OUT_JSON = Path(r"C:\Users\USER\Documents\etabs-mcp\src\etabs_mcp\etabs_api_index.json")
OUT_NPY  = Path(r"C:\Users\USER\Documents\etabs-mcp\src\etabs_mcp\etabs_api_embeddings.npy")

# ── C# → Python type mapping ────────────────────────────────────────────────
CS_TO_PY = {
    "int": "int", "Integer": "int", "Int32": "int", "Int64": "int",
    "double": "float", "Double": "float", "single": "float",
    "float": "float", "Float": "float",
    "bool": "bool", "Boolean": "bool",
    "string": "str", "String": "str",
    "void": "None",
    "double[]": "list[float]", "Double[]": "list[float]",
    "int[]": "list[int]", "Int32[]": "list[int]",
    "string[]": "list[str]", "String[]": "list[str]",
    "bool[]": "list[bool]", "Boolean[]": "list[bool]",
    "object": "Any", "Object": "Any",
}

SKIP_TITLES = {"index", "contents", "search", "namespace", "assembly", "overview"}


def cs_type_to_py(cs_type: str) -> str:
    cs_type = cs_type.strip().replace("ref ", "").replace("ByRef ", "").replace("out ", "")
    return CS_TO_PY.get(cs_type, cs_type)


def extract_code_text(tag: Tag) -> str:
    """Extract text from a <pre> tag stripping all child span tags."""
    return tag.get_text(separator=" ", strip=True)


def parse_page(html_path: Path) -> dict | None:
    try:
        content = html_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    soup = BeautifulSoup(content, "html.parser")

    # Title
    title_tag = soup.find("title")
    if not title_tag:
        return None
    title = title_tag.get_text(strip=True)

    # Skip non-method pages
    title_lower = title.lower()
    if any(s in title_lower for s in SKIP_TITLES):
        return None
    if "namespace" in title_lower or "assembly" in title_lower:
        return None

    # Microsoft Help ID → gives us the full qualified name
    help_id_meta = soup.find("meta", attrs={"name": "Microsoft.Help.Id"})
    help_id = help_id_meta["content"] if help_id_meta else ""

    # Container meta → class path (e.g. ETABSv1)
    container_meta = soup.find("meta", attrs={"name": "container"})
    container = container_meta["content"] if container_meta else "ETABSv1"

    # F1 meta → e.g. "ETABSv1.cSapModel.Analyze.RunAnalysis"
    f1_meta = soup.find("meta", attrs={"name": "Microsoft.Help.F1"})
    qualified_name = f1_meta["content"] if f1_meta else ""

    # Extract object and method name from qualified name
    # e.g. "ETABSv1.cPointElm.GetSpringCoupled"
    parts = qualified_name.replace("ETABSv1.", "").split(".")
    if len(parts) >= 2:
        class_name = ".".join(parts[:-1])  # e.g. "cSapModel.Analyze"
        method_name = parts[-1]
    elif len(parts) == 1:
        class_name = parts[0]
        method_name = ""
    else:
        class_name = ""
        method_name = title.split(" ")[0]

    # Clean class name: cSapModel → model, cAnalyze → model.Analyze, etc.
    model_path = class_name_to_model_path(class_name)

    # Extract C# syntax from the first code snippet (tab 1 = C#)
    cs_code = ""
    code_div = soup.find("div", id=re.compile(r".*_code_Div1"))
    if code_div:
        pre = code_div.find("pre")
        if pre:
            cs_code = extract_code_text(pre)

    # Extract parameters from <dl>
    params_cs = []
    dl = soup.find("dl")
    if dl:
        dts = dl.find_all("dt")
        dds = dl.find_all("dd")
        for dt, dd in zip(dts, dds):
            param_name = dt.get_text(strip=True)
            param_text = dd.get_text(strip=True)
            # Extract type from "Type:SystemString" or "Type:SystemDouble[]"
            type_match = re.search(r"Type:System(\w+(?:\[\])?)", param_text)
            if not type_match:
                type_match = re.search(r"Type:\s*(\w+(?:\[\])?)", param_text)
            param_type = type_match.group(1) if type_match else "Any"
            params_cs.append({"name": param_name, "cs_type": param_type,
                               "py_type": cs_type_to_py(param_type)})

    # Extract remarks / description text
    desc = ""
    intro = soup.find("span", class_="introStyle")
    if intro:
        desc = intro.get_text(strip=True)
    if not desc:
        # Try first paragraph in topic content
        topic = soup.find("div", id="TopicContent")
        if topic:
            p = topic.find("p")
            if p:
                desc = p.get_text(strip=True)[:300]

    if not method_name and not qualified_name:
        return None

    # Build Python calling convention
    py_call = build_python_call(model_path, method_name, params_cs, cs_code)

    return {
        "title": title,
        "qualified_name": qualified_name,
        "class": class_name,
        "model_path": model_path,
        "method": method_name,
        "description": desc,
        "params": params_cs,
        "cs_signature": cs_code[:300],
        "python_call": py_call,
        "file": html_path.name,
    }


def class_name_to_model_path(class_name: str) -> str:
    """Convert cSapModel.cAnalyze → model.Analyze, cPointObj → model.PointObj, etc."""
    # Remove leading 'c' prefix from each segment, keep SapModel → model
    segments = class_name.split(".")
    result = []
    for seg in segments:
        if seg in ("cSapModel", "SapModel"):
            result.append("model")
        elif seg.startswith("c") and len(seg) > 1 and seg[1].isupper():
            result.append(seg[1:])  # cAnalyze → Analyze
        else:
            result.append(seg)
    return ".".join(result)


def build_python_call(model_path: str, method: str, params: list, cs_sig: str) -> str:
    """Generate the Python calling convention string."""
    # Identify output (ref/ByRef) params — they come back in the result tuple
    input_params = []
    output_params = []

    # Parse cs_sig to find ref/ByRef params
    ref_params = set(re.findall(r"(?:ref|ByRef|out)\s+\w+\s+(\w+)", cs_sig, re.IGNORECASE))

    for p in params:
        if p["name"] in ref_params or p["name"].startswith("ret") or p["cs_type"] in ("int", "Integer") and p["name"] == "ret":
            output_params.append(p)
        else:
            input_params.append(p)

    # Build call
    in_args = ", ".join(p["name"] for p in input_params)
    call = f"{model_path}.{method}({in_args})" if model_path else f"model.{method}({in_args})"

    # Build return description
    if output_params:
        out_names = ", ".join(p["name"] for p in output_params)
        ret_str = f"# returns [{out_names}, ret_code]"
    else:
        ret_str = "# returns ret_code (0 = success)"

    return f"result = {call}\n{ret_str}"


def build_search_text(entry: dict) -> str:
    """Build text for embedding."""
    parts = [
        entry.get("title", ""),
        entry.get("description", ""),
        entry.get("qualified_name", ""),
        entry.get("python_call", ""),
        " ".join(p["name"] for p in entry.get("params", [])),
    ]
    return " ".join(p for p in parts if p).strip()


def main():
    print(f"Scanning {CHM_HTML_DIR} ...")
    html_files = list(CHM_HTML_DIR.glob("*.htm")) + list(CHM_HTML_DIR.glob("*.html"))
    print(f"Found {len(html_files)} HTML files")

    entries = []
    skipped = 0
    for i, f in enumerate(html_files):
        if i % 100 == 0:
            print(f"  Parsing {i}/{len(html_files)} ...", end="\r")
        entry = parse_page(f)
        if entry and entry["method"]:
            entries.append(entry)
        else:
            skipped += 1

    print(f"\nParsed {len(entries)} API entries, skipped {skipped}")

    # Save JSON
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON -> {OUT_JSON}  ({OUT_JSON.stat().st_size//1024} KB)")

    # Build embeddings
    print("\nBuilding embeddings (sentence-transformers all-MiniLM-L6-v2) ...")
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        texts = [build_search_text(e) for e in entries]
        print(f"  Encoding {len(texts)} entries ...")
        embeddings = model.encode(texts, batch_size=64, show_progress_bar=True,
                                  convert_to_numpy=True, normalize_embeddings=True)
        np.save(OUT_NPY, embeddings.astype("float32"))
        print(f"Saved embeddings -> {OUT_NPY}  shape={embeddings.shape}")
    except ImportError as e:
        print(f"WARNING: sentence-transformers not available ({e}) — skipping embeddings")
        print("Install with: pip install sentence-transformers")

    print("\nDone! Run: python -m PyInstaller mcpb/etabs-mcp.spec --noconfirm")


if __name__ == "__main__":
    main()

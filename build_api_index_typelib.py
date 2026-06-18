"""
ETABS OAPI Type Library → API Index Builder
============================================
Extracts all COM interfaces, methods, and properties directly from
ETABSv1.dll's embedded type library — no CHM required.

Produces the same etabs_api_index.json format as build_api_index.py
so it's a drop-in replacement for search_docs.

Run:
    py build_api_index_typelib.py
    # or point to a specific DLL:
    py build_api_index_typelib.py --dll "C:\\path\\to\\ETABSv1.dll"

Output:
    src/etabs_mcp/etabs_api_index.json

Requirements:
    pip install comtypes
    (comtypes is already a dependency of etabs-mcp)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ── Output path ──────────────────────────────────────────────────────────────
OUT_JSON = Path(__file__).parent / "src" / "etabs_mcp" / "etabs_api_index.json"

# ── Default type library path (ETABS 23) ─────────────────────────────────────
# ETABSv1.tlb  = ETABS-specific interfaces only (~315 KB)
# CSiAPIv1.tlb = full CSi API including SAP2000/SAFE shared interfaces (~853 KB)
DEFAULT_DLL = Path(r"C:\Program Files\Computers and Structures\ETABS 23\NativeAPI\x64\ETABSv1.tlb")

# ── VARTYPE → Python type ─────────────────────────────────────────────────────
# https://docs.microsoft.com/en-us/windows/win32/api/oaidl/ne-oaidl-varenum
VT_TO_PY: dict[int, str] = {
    0:  "None",   # VT_EMPTY
    1:  "None",   # VT_NULL
    2:  "int",    # VT_I2
    3:  "int",    # VT_I4
    4:  "float",  # VT_R4
    5:  "float",  # VT_R8
    8:  "str",    # VT_BSTR
    11: "bool",   # VT_BOOL
    16: "int",    # VT_I1
    17: "int",    # VT_UI1
    18: "int",    # VT_UI2
    19: "int",    # VT_UI4
    20: "int",    # VT_I8
    21: "int",    # VT_UI8
    22: "int",    # VT_INT
    23: "int",    # VT_UINT
    24: "None",   # VT_VOID
    25: "int",    # VT_HRESULT
}
VT_ARRAY = 0x2000
VT_BYREF = 0x4000
VT_PTR   = 26


def vt_to_py(vt: int) -> tuple[str, bool]:
    """Return (python_type_str, is_byref)."""
    is_byref = bool(vt & VT_BYREF)
    is_array = bool(vt & VT_ARRAY)
    base = vt & ~(VT_BYREF | VT_ARRAY | 0x1000)
    py = VT_TO_PY.get(base, "Any")
    if is_array:
        py = f"list[{py}]"
    return py, is_byref


def class_name_to_model_path(class_name: str) -> str:
    """Convert cSapModel → model, cPointObj → model.PointObj, etc."""
    segments = class_name.split(".")
    result = []
    for seg in segments:
        if seg in ("cSapModel", "SapModel"):
            result.append("model")
        elif seg.startswith("c") and len(seg) > 1 and seg[1].isupper():
            result.append(seg[1:])
        else:
            result.append(seg)
    return ".".join(result)


def build_python_call(model_path: str, method: str, params: list[dict]) -> str:
    """Build a Python calling convention string."""
    input_params  = [p for p in params if not p["is_byref"]]
    output_params = [p for p in params if p["is_byref"]]

    in_args = ", ".join(p["name"] for p in input_params)
    base = model_path if model_path else "model"
    call = f"{base}.{method}({in_args})"

    if output_params:
        out_names = ", ".join(p["name"] for p in output_params)
        ret_str = f"# returns [{out_names}, ret_code]"
    else:
        ret_str = "# returns ret_code (0 = success)"

    return f"result = {call}\n{ret_str}"


def build_cs_signature(method: str, params: list[dict], ret_py: str) -> str:
    parts = []
    for p in params:
        prefix = "ref " if p["is_byref"] else ""
        parts.append(f"{prefix}{p['cs_type']} {p['name']}")
    return f"{ret_py} {method}({', '.join(parts)})"


def extract_from_typelib(dll_path: Path) -> list[dict]:
    """Load ETABSv1.dll type library and enumerate all interface methods."""
    try:
        import comtypes.typeinfo
    except ImportError:
        print("ERROR: comtypes not installed. Run: pip install comtypes")
        sys.exit(1)

    print(f"Loading type library from: {dll_path}")
    try:
        tlib = comtypes.typeinfo.LoadTypeLibEx(str(dll_path))
    except Exception as e:
        print(f"ERROR: Could not load type library: {e}")
        sys.exit(1)

    n_types = tlib.GetTypeInfoCount()
    print(f"Found {n_types} type definitions in library")

    entries: list[dict] = []
    skipped = 0

    for i in range(n_types):
        try:
            typeinfo = tlib.GetTypeInfo(i)
            attr = typeinfo.GetTypeAttr()
        except Exception:
            skipped += 1
            continue

        # TKIND: 0=enum, 1=struct, 2=module, 3=interface, 4=dispinterface, 5=coclass, 6=alias, 7=union
        if attr.typekind not in (3, 4):  # only interfaces and dispinterfaces
            continue

        try:
            class_name = tlib.GetDocumentation(i)[0]
            class_doc  = tlib.GetDocumentation(i)[1] or ""
        except Exception:
            continue

        if not class_name or not class_name.startswith("c"):
            continue  # skip non-ETABS interfaces (IUnknown, IDispatch, etc.)

        model_path = class_name_to_model_path(class_name)

        for j in range(attr.cFuncs):
            try:
                fdesc = typeinfo.GetFuncDesc(j)
            except Exception:
                skipped += 1
                continue

            # Skip property put/putref — only get and regular methods
            # INVOKE_FUNC=1, INVOKE_PROPERTYGET=2, INVOKE_PROPERTYPUT=4, INVOKE_PROPERTYPUTREF=8
            if fdesc.invkind in (4, 8):
                continue

            try:
                docs = typeinfo.GetDocumentation(fdesc.memid)
                method_name = docs[0]
                method_doc  = docs[1] or ""
            except Exception:
                skipped += 1
                continue

            if not method_name:
                continue

            # --- Parameter info ---
            params: list[dict] = []
            n_params = fdesc.cParams

            for k in range(n_params):
                try:
                    elem = fdesc.lprgelemdescParam[k]
                    vt = int(elem.tdesc.vt)
                    py_type, is_byref = vt_to_py(vt)

                    # Try to get cs_type name
                    if vt & VT_BYREF:
                        base_vt = vt & ~VT_BYREF
                        cs_type = VT_TO_PY.get(base_vt & ~VT_ARRAY, "Any")
                        if vt & VT_ARRAY:
                            cs_type += "[]"
                    else:
                        cs_type = VT_TO_PY.get(vt & ~VT_ARRAY, "Any")
                        if vt & VT_ARRAY:
                            cs_type += "[]"

                    # Param names come from GetNames
                    try:
                        names = typeinfo.GetNames(fdesc.memid, n_params + 1)
                        param_name = names[k + 1] if k + 1 < len(names) else f"p{k}"
                    except Exception:
                        param_name = f"p{k}"

                    params.append({
                        "name": param_name,
                        "cs_type": cs_type,
                        "py_type": py_type,
                        "is_byref": is_byref,
                    })
                except Exception:
                    params.append({"name": f"p{k}", "cs_type": "Any",
                                   "py_type": "Any", "is_byref": False})

            # --- Return type ---
            try:
                ret_vt = int(fdesc.elemdescFunc.tdesc.vt)
                ret_py, _ = vt_to_py(ret_vt)
            except Exception:
                ret_py = "int"

            qualified_name = f"ETABSv1.{class_name}.{method_name}"
            python_call    = build_python_call(model_path, method_name, params)
            cs_sig         = build_cs_signature(method_name, params, ret_py)

            # Strip is_byref from exported params (not needed in JSON consumer)
            clean_params = [
                {"name": p["name"], "cs_type": p["cs_type"], "py_type": p["py_type"]}
                for p in params
            ]

            entries.append({
                "title":          f"{class_name}.{method_name} Method",
                "qualified_name": qualified_name,
                "class":          class_name,
                "model_path":     model_path,
                "method":         method_name,
                "description":    method_doc,
                "params":         clean_params,
                "cs_signature":   cs_sig,
                "python_call":    python_call,
                "source":         "typelib",
            })

    return entries


def merge_with_chm(typelib_entries: list[dict], chm_json_path: Path) -> list[dict]:
    """
    Merge typelib entries with existing CHM entries.
    CHM entries are preferred when they exist (they have better param names
    from the <dl> HTML). Typelib fills in any methods missing from the CHM.
    """
    if not chm_json_path.exists():
        print("No existing CHM index found — using typelib only.")
        return typelib_entries

    with open(chm_json_path, encoding="utf-8") as f:
        chm_entries = json.load(f)

    chm_keys = {(e["class"], e["method"]) for e in chm_entries}
    new_from_typelib = [
        e for e in typelib_entries
        if (e["class"], e["method"]) not in chm_keys
    ]

    print(f"CHM entries:      {len(chm_entries)}")
    print(f"Typelib entries:  {len(typelib_entries)}")
    print(f"New from typelib: {len(new_from_typelib)}  (not in CHM)")

    merged = chm_entries + new_from_typelib
    merged.sort(key=lambda e: (e["class"], e["method"]))
    return merged


def main():
    parser = argparse.ArgumentParser(description="Build ETABS API index from type library")
    parser.add_argument("--dll", default=str(DEFAULT_DLL),
                        help="Path to ETABSv1.dll")
    parser.add_argument("--merge", action="store_true", default=True,
                        help="Merge with existing CHM index (default: True)")
    parser.add_argument("--typelib-only", action="store_true",
                        help="Use typelib only, ignore CHM index")
    parser.add_argument("--out", default=str(OUT_JSON),
                        help="Output JSON path")
    args = parser.parse_args()

    dll_path = Path(args.dll)
    if not dll_path.exists():
        print(f"ERROR: DLL not found: {dll_path}")
        print("Specify with --dll path/to/ETABSv1.dll")
        sys.exit(1)

    entries = extract_from_typelib(dll_path)
    print(f"\nExtracted {len(entries)} methods from type library")

    out_path = Path(args.out)

    if not args.typelib_only:
        entries = merge_with_chm(entries, out_path)
        print(f"Merged total: {len(entries)} entries")
    else:
        entries.sort(key=lambda e: (e["class"], e["method"]))

    # Stats
    by_class = {}
    for e in entries:
        by_class.setdefault(e["class"], 0)
        by_class[e["class"]] += 1
    top = sorted(by_class.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\nTop 10 classes:")
    for cls, n in top:
        print(f"  {n:4d}  {cls}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    size_kb = out_path.stat().st_size // 1024
    print(f"\nSaved -> {out_path}  ({size_kb} KB, {len(entries)} entries)")
    print("\nNext: run  .\\build.ps1  to bundle the updated index into the exe")


if __name__ == "__main__":
    main()

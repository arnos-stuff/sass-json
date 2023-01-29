import re
import sys
import json
import rich
import shutil


from deepdiff import DeepDiff
from pathlib import Path
from typing import Dict, Any, Union, Tuple, List, Optional

from .utils import (
    run_shell, console,
    run_shell_print_status as runshp,
    PathLike
)

__all__ = ["read_sass", "write_sass", "write_json", "read_json", "rawparse"]

def find_nested_brackets(raw: str) -> str:
    """Find the nested brackets in a string"""
    # remove newlines and tabs
    starts = re.findall(r"(\{)([^\}]*)(\{)", raw)
    ends = re.findall(r"(\})([^\{]*)(\})", raw)
    nesteds = []
    for s, e in zip(starts, ends):
        start = "".join(s) 
        end = "".join(e)
        nesteds.append(f"{start} ... {end}")
    return nesteds

def exists_in_list(index: int, list: List) -> bool:
    """Check if an index exists in a list"""
    try:
        list[index]
        return True
    except IndexError:
        return False

def read_sass(sass_file: PathLike) -> Dict[str, Any]:
    """Read a sass file and return the contents as a dictionary"""
    sassObj = rawparse(sass_file)

    # parse the keys and values
    if len(sassObj["keys"]) != len(sassObj["values"]):
        console.print(
            """⚠️ Number of keys and values don't match.
        This is probably because you have [red]nested brackets.[/red]
        This will lower the performance of this run.
        """,
            style="bold yellow",
        )
        nested_check = [
            {"index": idx, "count": val.count("{"), "value": val }
            for idx, val in enumerate(sassObj["values"])
        ]

        easy_nodes = []
        nested_nodes = []
        for node in nested_check:
            if node["count"] == 1:
                easy_nodes.append([
                    node["index"],
                    sassObj["keys"][node["index"]],
                    sassObj["values"][node["index"]],
                ])
            else:
                nested_nodes.append([
                    node["index"],
                    sassObj["keys"][node["index"]],
                    sassObj["values"][node["index"]],
                ])

        if len(nested_nodes) > 0:
            console.print(
                f"""⚠️ [red]{len(nested_nodes)} nested brackets[/red] found in the file.
            """,
                style="bold yellow",
            )
        else:
            console.print(
                """⚠️ No nested brackets found in the file.
                Cannot parse the file. You may have missed a bracket somewhere.
                """,
                style="bold yellow",
            )
            sys.exit(1)

        # parse the easy nodes
        for eznode in easy_nodes:
            eznode[2] = parse_value(eznode[2])
        
        # parse the nested nodes
        for node in nested_nodes:
            node[2] = parse_nested(node[2])
    else:
        return [
            {"keys": parse_value(rawval), "values": parse_value(rawval)}
            for key, rawval in zip(sassObj["keys"], sassObj["values"])
        ]

    sassReturn = []

    nst_idx = 0
    for idx in range(len(sassObj["values"])):
        if exists_in_list(idx, easy_nodes):
            node_idx, node_key, node_val = easy_nodes[idx]
            sassReturn.append(
                {
                    "key": node_key,
                    "value": node_val,
                    "index": node_idx,
                    "type": "key-value",
                }
            )
        elif exists_in_list(nst_idx, nested_nodes):
            node_idx, node_key, node_val = nested_nodes[nst_idx]
            sassReturn.append(
                {
                    "key": node_key,
                    "value": node_val,
                    "index": node_idx,
                    "type": "nested",
                }
            )
            nst_idx += 1
        else:
            raise ValueError(f"""Something went wrong while parsing the file:
            Could not attribute a node to a nested node or a simple node.

            Node index: {idx}
            Nested node index: {nst_idx}

            Simple node count: {len(easy_nodes)}
            Nested node count: {len(nested_nodes)}

            Predecessors:
                - Nested node index: {nested_nodes[nst_idx - 3:nst_idx]}


                - Simple node index: {easy_nodes[idx - 3:idx]}

            """)
        
    if len(sassReturn) != len(sassObj["values"]):
        console.print("Something went wrong while parsing the file")
        sys.exit(1)
    return sassReturn


def parse_value(rawval: str) -> Dict[str, Any]:
    """Parse a value and return the contents as a dictionary"""
    # remove newlines and tabs
    rawval = re.sub(r"[\n\t]", "", rawval)
    # sanity check
    if (
        re.search(r"[\w\.\-\#\[\]\=\:\'\"]", rawval) is None
        or re.search(r"[\{\}]", rawval) is None
        or rawval.count("{") != rawval.count("}")
    ):
        raise ValueError(f"""Invalid value:
        Either:
            - you have more opening than closing brackets (or converse)
            - you have missed a bracket somewhere
            - you have brackets without any key-value pair within them
        
        Value:
        {rawval}
        """)
    # split the value in two parts:
    start_idx = rawval.find("{")
    end_idx = rawval.rfind("}")
    values = rawval[start_idx + 1 : end_idx]
    if re.findall(r"\{", values) or re.findall(r"\}", values):
        raise ValueError("Nested brackets not supported yet")

    valueObj = []
    for line in values.split(";"):
        if not line:
            continue

        content = line.split(":")
        if len(content) == 2 and not isinstance(content, str):
            key, value = content
            valueObj += [{
                "type": "key-value", "key":key.strip(), "value": value.strip()
            }]
        else:
            _value = content[0].strip() if isinstance(content, list) else content.strip()
            if _value.startswith("@include"):
                valueObj += [{"type": "include", "value": _value.strip()}]
            elif _value.startswith("@extend"):
                valueObj += [{"type": "extend", "value": _value.strip()}]
            elif _value.startswith("@media"):
                valueObj += [{"type": "media", "value": _value.strip()}]
            elif _value.startswith("@"):
                valueObj += [{"type": "at-rule", "value": _value.strip()}]
            elif _value.strip() != "":
                raise ValueError(f"Invalid value: {line}")
    return valueObj

def parse_nested(rawval: str) -> Dict[str, Any]:
    """Parse a nested value and return the contents as a dictionary"""
    # remove newlines and tabs
    rawval = re.sub(r"[\n\t]", "", rawval)
    start_idx = rawval.find("{")
    end_idx = rawval.rfind("}")
    values = rawval[start_idx + 1 : end_idx-1]
    if values.count("{") > 1 or values.count("}") > 1:
        raise ValueError(f"We don't support doubly nested brackets yet !\n {values}")

    keys, values = get_key_values(values)

    nestedObj = []
    for key, val in zip(keys, values):
        nested_content = parse_value(val)
        if len(nested_content) > 1:
            nestedObj += [
                {
                    "type": "nested",
                    "key": key,
                    "value": nested_content,
                }
            ]
        else:
            nestedObj += [
                {
                    "type": nested_content[0]["type"],
                    "key": key,
                    "value": nested_content[0]["value"],
                }
            ]
        
    return nestedObj

def get_key_values(raw: str) -> Tuple[List[str], List[str]]:
    keys = re.findall(r"([\w#\. ,\>\-\:\n\[\=\'\"\]\*\@]+?)\s*{", raw)
    values = re.findall(r"({.*?})", raw, flags=re.DOTALL)

    keys = list(
        map(
            lambda x: [
                xx.strip() for xx in re.split("([\n,]+?)", x)
                if xx.strip() not in {"", ","}
                ],
            keys
        )
    )
    return keys, values

def rawparse(sass_file: PathLike) -> Dict[str, Any]:
    """Read a sass file and return the contents as a dictionary"""
    with open(sass_file, "r") as f:
        raw = f.read()

    # ignore comments
    raw = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
    raw = re.sub(r"//.*?\n", "", raw)

    current = raw

    # split in two parts:
    # 1. the part before the first @import
    # 2. the part after the last successive @import

    file_imports = re.findall(r"(@import .*?;\n)" , raw, flags=re.DOTALL)
    current = re.sub(r"(@import .*?;\n)" , "", raw)

    # return {
    #     "imports": [
    #         fimp.strip() for fimp in file_imports
    #         ],
    #     "body": current,
    # }

    # split the body in two parts:
    # keys and values, values being bracketed by {} and keys being
    # listed before the first bracket

    keys, values = get_key_values(current)

    return {
        "imports": [
            fimp.strip() for fimp in file_imports
            ],
        "keys": keys,
        "values": values,
    }




def parse(raw: str) -> str:
    """Parse a sass file and return the contents"""
    return raw
import re
from typing import Dict, Tuple, List, Iterator, Optional, Any

# Overall nested dictionary:
# Module -> Type -> Field -> { "field": { "type": ..., "restrict-to": ... }, "meta": { ... } }
ModuleDict = Dict[str, Dict[str, Dict[str, Dict[str, Any]]]]

def parse_files(asn_files: List[str]) -> ModuleDict:
  """
  Process all ASN.1 files and merge the metadata dictionaries.
  """
  overall_data: ModuleDict = {}
  for filename in asn_files:
    file_data = process_file(filename)
    for mod, types in file_data.items():
      overall_data.setdefault(mod, {}).update(types)
  return overall_data

def process_file(filename: str) -> ModuleDict:
  """
  Process a single ASN.1 file and return a nested dictionary of metadata.
  """
  with open(filename, "r") as f:
    lines = f.readlines()

  entries = list(iter_entries_from_lines(lines))
  data: ModuleDict = {}
  for module, typ, field, entry in entries:
    data.setdefault(module, {}).setdefault(typ, {})[field] = entry
  return data


def iter_entries_from_lines(lines: List[str]) -> Iterator[Tuple[str, str, str, Dict[str, Any]]]:
  """
  Given the lines from an ASN.1 file, yield tuples of
     (module, type, field, { "field": {...}, "meta": {...} })
  using an iterator-based style.
  """
  current_module = "UnknownModule"
  current_type = "UnknownType"
  in_sequence = False

  line_iter = iter(lines)
  for raw_line in line_iter:
    line = raw_line.strip()
    if not line:
      continue

    if (module_name := parse_module_line(line)) is not None:
      current_module = module_name
      continue

    if (type_name := parse_type_line(line)) is not None:
      current_type = type_name
      in_sequence = True
      continue

    if in_sequence and line == "}":
      in_sequence = False
      current_type = "UnknownType"
      continue

    if in_sequence and line.startswith("-- [Meta]"):
      meta_lines: List[str] = []
      for candidate in line_iter:
        candidate = candidate.strip()
        if candidate.startswith("-- @"):
          meta_lines.append(candidate)
        else:
          field_line = candidate
          break
      else:
        continue  # No field definition found.

      meta = parse_generic_meta_block(meta_lines)
      if not meta:
        continue

      field_parsed = parse_field_line(field_line)
      if field_parsed is None:
        continue
      field_name, field_type, integer_restrict_to = field_parsed
      field_info: Dict[str, Any] = {"type": field_type}
      if field_type == "INTEGER" and integer_restrict_to is not None:
        field_info["restrict-to"] = integer_restrict_to
      yield (current_module, current_type, field_name, {"field": field_info, "meta": meta})
  return



def parse_module_line(line: str) -> Optional[str]:
  """Extract the module name from a module definition line."""
  m = re.match(r"^([\w-]+)\s+DEFINITIONS", line)
  return m.group(1) if m else None


def parse_type_line(line: str) -> Optional[str]:
  """Extract the type name from a SEQUENCE type definition line."""
  m = re.match(r"^([\w-]+)\s*::=\s*SEQUENCE\s*{", line)
  return m.group(1) if m else None


def parse_meta_value(val: str) -> Any:
  """
  Parse a meta value string.
  - If the value is enclosed in parentheses, parse it as a tuple of floats.
  - If it's enclosed in quotes, return the string without quotes.
  - Otherwise, try to convert to a float; if that fails, return the stripped string.
  """
  val = val.strip()
  if val.startswith("(") and val.endswith(")"):
    inner = val[1:-1].strip()
    parts = [p.strip() for p in inner.split(",")]
    try:
      return tuple(float(p) for p in parts)
    except ValueError:
      return val
  elif (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
    return val[1:-1]
  else:
    try:
      return float(val)
    except ValueError:
      return val


def parse_generic_meta_block(meta_lines: List[str]) -> Dict[str, Any]:
  """
  Parse a list of meta lines.
  Expected each meta line to be in the format:
     -- @Key value
  For example:
     -- @Scale 0.1
     -- @Range (-12.8, 12.7)
     -- @Description 'Ascent rate'
     -- @Units 'm/s'
  Keys are used as provided and values are parsed via `parse_meta_value`.
  """
  meta: Dict[str, Any] = {}
  for line in meta_lines:
    m = re.match(r"--\s*@(\w+)\s+(.*)", line)
    if m:
      key = m.group(1)
      value_str = m.group(2)
      meta[key] = parse_meta_value(value_str)
  return meta


def parse_field_line(line: str) -> Optional[Tuple[str, str, Optional[Tuple[int, int]]]]:
  """
  Parse a field definition line.
  Expected format, for example:
     voltage Stat32u,
     ascent-rate INTEGER (-128..127),
  Returns a tuple of:
     (field_name, field_type, integer_restrict_to)
  where integer_restrict_to is only provided if field_type is "INTEGER" and a restriction is given.
  """
  m = re.match(r"^([\w-]+)\s+([\w-]+)(?:\s*\(([-0-9]+)\.\.([-0-9]+)\))?,?", line)
  if m is None:
    return None
  field_name = m.group(1)
  field_type = m.group(2)
  integer_restrict_to: Optional[Tuple[int, int]] = None
  if field_type == "INTEGER" and m.group(3) and m.group(4):
    integer_restrict_to = (int(m.group(3)), int(m.group(4)))
  return field_name, field_type, integer_restrict_to


# Example usage:
if __name__ == "__main__":
  from argparse import ArgumentParser
  from glob import glob
  from json import dumps

  parser = ArgumentParser()
  parser.add_argument("file_pattern", type=str)
  args = parser.parse_args()

  metadata_dict = parse_files(glob(args.file_pattern))
  print(dumps(metadata_dict, indent=2))

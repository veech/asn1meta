import re
from typing import Dict, Tuple, List, Iterator, Optional
from typing import TypedDict
from glob import glob

# Define our metadata structures.


class FieldMetadata(TypedDict):
  scale: float
  range: Tuple[float, float]


class FieldMetadataOpt(FieldMetadata, total=False):
  range_constraint: Tuple[int, int]


# Overall nested dictionary: Module -> Type -> Field -> Metadata.
ModuleDict = Dict[str, Dict[str, Dict[str, FieldMetadataOpt]]]


def parse_module_line(line: str) -> Optional[str]:
  """Extract the module name from a module definition line."""
  m = re.match(r"^([\w-]+)\s+DEFINITIONS", line)
  return m.group(1) if m else None


def parse_type_line(line: str) -> Optional[str]:
  """Extract the type name from a SEQUENCE type definition line."""
  m = re.match(r"^(\w+)\s*::=\s*SEQUENCE\s*{", line)
  return m.group(1) if m else None


def parse_meta_block_lines(scale_line: str, range_line: str) -> Optional[FieldMetadataOpt]:
  """
  Parse the meta block lines for scale and range.
  Expected formats:
    -- #Scale 0.1
    -- #Range (-12.8, 12.7)
  """
  scale_m = re.match(r"--\s*#Scale\s+([0-9.]+)", scale_line)
  range_m = re.match(r"--\s*#Range\s*\(\s*([-0-9.]+)\s*,\s*([-0-9.]+)\s*\)", range_line)
  if scale_m is None or range_m is None:
    return None
  try:
    scale_val = float(scale_m.group(1))
    phys_min = float(range_m.group(1))
    phys_max = float(range_m.group(2))
  except ValueError:
    return None
  return {"scale": scale_val, "range": (phys_min, phys_max)}


def parse_field_line(line: str) -> Optional[Tuple[str, Optional[Tuple[int, int]]]]:
  """
  Parse a field definition line.
  Expected format: 'ascent-rate INTEGER (-128..127),' (the trailing comma is optional).
  Returns (field_name, range_constraint) where range_constraint is optional.
  """
  m = re.match(r"^([\w-]+)\s+INTEGER(?:\s*\(([-0-9]+)\.\.([-0-9]+)\))?,?", line)
  if m is None:
    return None
  field_name = m.group(1)
  range_constraint = (int(m.group(2)), int(m.group(3))) if (m.group(2) and m.group(3)) else None
  return field_name, range_constraint


def iter_entries_from_lines(lines: List[str]) -> Iterator[Tuple[str, str, str, FieldMetadataOpt]]:
  """
  Given the lines from an ASN.1 file, yield tuples of
     (module, type, field, meta
     data)
  using a functional style with an iterator.
  """
  current_module = "UnknownModule"
  current_type = "UnknownType"
  in_sequence = False

  # Create an iterator over the lines.
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

    # Process meta block if inside a SEQUENCE.
    if in_sequence and line.startswith("-- @Meta"):
      try:
        # Consume next two lines for meta block.
        scale_line = next(line_iter).strip()
        range_line = next(line_iter).strip()
      except StopIteration:
        continue
      meta = parse_meta_block_lines(scale_line, range_line)
      if meta is None:
        continue
      # Consume next non-empty line for the field definition.
      field_line = next((l.strip() for l in line_iter if l.strip()), None)
      if field_line is None:
        continue
      field_parsed = parse_field_line(field_line)
      if field_parsed is None:
        continue
      field_name, range_constraint = field_parsed
      if range_constraint is not None:
        meta["range_constraint"] = range_constraint
      yield (current_module, current_type, field_name, meta)
  return


def process_file(filename: str) -> ModuleDict:
  """
  Process a single ASN.1 file and return a nested dictionary of metadata.
  """
  with open(filename, "r") as f:
    lines = f.readlines()

  entries = list(iter_entries_from_lines(lines))
  data: ModuleDict = {}
  for module, typ, field, metadata in entries:
    data.setdefault(module, {}).setdefault(typ, {})[field] = metadata
  return data


def parse_asn_files(file_pattern: str = "*.asn") -> ModuleDict:
  """
  Process all ASN.1 files matching the given glob pattern and merge the metadata dictionaries.
  """
  overall_data: ModuleDict = {}
  for filename in glob(file_pattern):
    file_data = process_file(filename)
    for mod, types in file_data.items():
      overall_data.setdefault(mod, {}).update(types)
  return overall_data


# Example usage:
if __name__ == "__main__":
  from argparse import ArgumentParser
  parser = ArgumentParser()
  parser.add_argument("file_pattern", type=str)
  args = parser.parse_args()

  metadata_dict = parse_asn_files(args.file_pattern)
  print(metadata_dict)

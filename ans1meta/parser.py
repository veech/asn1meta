import glob
import re
from typing import Dict, Tuple, List
from typing import TypedDict


class FieldMetadata(TypedDict):
  scale: float
  range: Tuple[float, float]


class FieldMetadataOpt(FieldMetadata, total=False):
  range_constraint: Tuple[int, int]


# Nested dictionary: Module -> Type -> Field -> Metadata
ModuleDict = Dict[str, Dict[str, Dict[str, FieldMetadataOpt]]]


def parse(file_pattern: str = "*.asn") -> ModuleDict:
  """
  Parse ASN.1 files matching the given glob pattern to extract field metadata.

  Expects meta blocks in the format:

      -- @Meta
      -- #Scale 0.1
      -- #Range -12.8, 12.7

  Immediately followed by a field definition like:

      ascent-rate INTEGER (-128..127)

  The metadata dictionary returned has the following structure:

  {
    'MODULE': {
       'TYPE': {
           'ascent-rate': {
              'scale': 0.1,
              'range': (-12.8, 12.7),
              'range_constraint': (-128, 127)  # if present
           }
       }
    }
  }

  :param file_pattern: Glob pattern to match ASN.1 files.
  :return: A nested dictionary with parsed metadata.
  """
  data: ModuleDict = {}
  current_module: str = "UnknownModule"
  current_type: str = "UnknownType"
  in_sequence: bool = False

  # Regular expressions for module, type, and field definitions
  module_re = re.compile(r"^(\w+)\s+DEFINITIONS")
  type_re = re.compile(r"^(\w+)\s*::=\s*SEQUENCE\s*{")
  field_re = re.compile(r"^([\w-]+)\s+INTEGER(?:\s*\(([-0-9]+)\.\.([-0-9]+)\))?")

  # Iterate through all files matching the pattern
  for filename in glob.glob(file_pattern):
    with open(filename, "r") as f:
      lines: List[str] = f.readlines()

    # Process each line with an index-based loop for lookahead.
    i = 0
    while i < len(lines):
      line = lines[i].strip()
      if not line:
        i += 1
        continue

      # Check for a module definition
      mod_match = module_re.match(line)
      if mod_match:
        current_module = mod_match.group(1)
        if current_module not in data:
          data[current_module] = {}
        i += 1
        continue

      # Check for a type (SEQUENCE) definition
      type_match = type_re.match(line)
      if type_match:
        current_type = type_match.group(1)
        if current_module not in data:
          data[current_module] = {}
        if current_type not in data[current_module]:
          data[current_module][current_type] = {}
        in_sequence = True
        i += 1
        continue

      # Check for end of a sequence block (assumes a line with a sole "}")
      if in_sequence and line == "}":
        in_sequence = False
        current_type = "UnknownType"
        i += 1
        continue

      # Look for the meta block indicator while inside a SEQUENCE
      if in_sequence and line.startswith("-- @Meta"):
        # Expect next two lines for scale and range
        if i + 2 < len(lines):
          scale_line = lines[i + 1].strip()
          range_line = lines[i + 2].strip()
          scale_match = re.match(r"--\s*#Scale\s+([0-9.]+)", scale_line)
          range_match = re.match(r"--\s*#Range\s+([-0-9.]+)\s*,\s*([-0-9.]+)", range_line)
          if scale_match and range_match:
            scale_val: float = float(scale_match.group(1))
            phys_min: float = float(range_match.group(1))
            phys_max: float = float(range_match.group(2))
            # Look for the field definition on the next non-empty line
            j = i + 3
            while j < len(lines) and not lines[j].strip():
              j += 1
            if j < len(lines):
              field_line = lines[j].strip()
              field_match = field_re.match(field_line)
              if field_match:
                field_name = field_match.group(1)
                metadata: FieldMetadataOpt = {
                    "scale": scale_val,
                    "range": (phys_min, phys_max)
                }
                if field_match.group(2) and field_match.group(3):
                  metadata["range_constraint"] = (
                      int(field_match.group(2)), int(field_match.group(3))
                  )
                # Store the metadata in the nested dictionary
                data[current_module][current_type][field_name] = metadata
                # Skip ahead past the meta block and field definition
                i = j + 1
                continue
        # If meta block not fully parsed, just move to the next line.
        i += 1
        continue

      # For all other lines, just proceed.
      i += 1

  return data


# Example usage:
if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser(description="Parse ASN.1 files to extract field metadata.")
  parser.add_argument("file_pattern", help="Glob pattern to match ASN.1 files")
  args = parser.parse_args()

  metadata_dict = parse(args.file_pattern)
  print(metadata_dict)

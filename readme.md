# ANS1Meta

ANS1Meta is a Python package that allows you to define and parse metadata for ASN.1 type definitions. It provides a simple way to annotate ASN.1 fields with additional information like scaling factors and physical value ranges.

## Installation

```bash
pip install ans1meta
```

## Usage

ANS1Meta allows you to add metadata to your ASN.1 fields using special comment blocks. The metadata is parsed and made available through a simple Python API.

### Defining Metadata

To add metadata to an ASN.1 field, use the following format in your `.asn` files:

```asn1
MyModule DEFINITIONS ::= BEGIN

    MyType ::= SEQUENCE {
        -- @Meta
        -- #Scale 0.1
        -- #Range -12.8, 12.7
        speed-value INTEGER (-128..127),

        -- Other fields...
    }

END
```

The metadata block consists of:

- `-- @Meta`: Marks the start of a metadata block
- `-- #Scale <value>`: Defines the scaling factor for the field
- `-- #Range <min>, <max>`: Defines the physical value range

The metadata block must be immediately followed by the field definition.

### Parsing Metadata

```python
from ans1meta import parse

# Parse all .asn files in the current directory
metadata = parse("*.asn")

# The returned dictionary structure:
# {
#     'MyModule': {
#         'MyType': {
#             'speed-value': {
#                 'scale': 0.1,
#                 'range': (-12.8, 12.7),
#                 'range_constraint': (-128, 127)  # Optional, from INTEGER constraints
#             }
#         }
#     }
# }
```

### Command Line Usage

The package also provides a command-line interface:

```bash
python -m ans1meta "*.asn"
```

## Metadata Structure

The parsed metadata for each field includes:

- `scale`: The scaling factor to convert between integer and physical values
- `range`: Tuple of (min, max) representing the physical value range
- `range_constraint`: Optional tuple of (min, max) from the INTEGER constraints

## License

This project is licensed under the MIT License.

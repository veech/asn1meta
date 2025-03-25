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
        -- [Meta]
        -- @Scale 0.1
        -- @Range (-12.8, 12.7)
        -- @Units 'm/s'
        -- @Description 'Speed value'
        speed-value INTEGER (-128..127),

        -- Other fields...
    }

END
```

The metadata block consists of:

- `-- [Meta]`: Marks the start of a metadata block
- `-- @Key value`: Generic format for metadata entries
- Common metadata keys include:
  - `@Scale`: Defines the scaling factor for the field
  - `@Range`: Defines the physical value range (as a tuple)
  - `@Units`: Specifies the units for the field
  - `@Description`: Provides a description of the field

The metadata block must be immediately followed by the field definition.

### Parsing Metadata

```python
from ans1meta import parse_asn_files

# Parse all .asn files in the current directory
metadata = parse_asn_files("*.asn")

# The returned dictionary structure:
# {
#     'MyModule': {
#         'MyType': {
#             'speed-value': {
#                 'field': {
#                     'type': 'INTEGER',
#                     'constraint': (-128, 127)
#                 },
#                 'meta': {
#                     'Scale': 0.1,
#                     'Range': (-12.8, 12.7),
#                     'Units': 'm/s',
#                     'Description': 'Speed value'
#                 }
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

The parsed metadata for each field is organized into two main sections:

- `field`: Contains the ASN.1 field information
  - `type`: The ASN.1 type of the field
  - `constraint`: Optional tuple of (min, max) from INTEGER constraints
- `meta`: Contains all user-defined metadata
  - Any key-value pairs defined in the `@Key value` format

## License

This project is licensed under the MIT License.

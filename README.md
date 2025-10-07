# TWIG-STIX

## STIX Data Cleaning - School Enrollment XML Files 

## Overview 

TWIG-STIX (Tidy Workflow for Integrating & Governing STIX) is a Python-based solution for cleaning and preprocessing student enrollment data exported from school boards in STIX XML format.

This project provides a Python-based solution for **cleaning and preprocessing student enrollment data** exported from school boards in **STIX XML format**. These XML files contain heirarchial information about schools, students, and associated fields, including personal details and contact information.

The cleaning process ensures that the data is structured, consistent, and complaint with expected STIX schema, ready for downstream analysis or to upload into Panorama or other STIX-interoperable systems.

## Features

* XML Parsing: Uses xmltodict and lxml to read hiearchical XML files
* Standardization & Cleaning: 
    * Fixes malformed or missing phone numbers
    * Corrects street numbers and unit numbers exceeding allowed lengths.
    * Ensures postal codes follow proper formats 
* Export: Saves cleaned files as XML (_CLEAN.xml) while preserving initial hierarchical structure

## Naming Conventions and Component Definitions 

To ensure that files can be properly ingested into the pipeline and understood by both humans and machines, this project adopts a standard naming convention: 

```
{DATE}_{BOARDACRONYM}_{BOARDNUMBER}_{SCHOOLTYPE}_{DATASET}_{STAGE}.{EXT}
```

```
20251007_UCDSB_67130_elementary_enrollment_clean.xml
```

### Component Definitions 

| Field           | Description                                        | Example                                          | Notes                                                                      |
| --------------- | -------------------------------------------------- | ------------------------------------------------ | -------------------------------------------------------------------------- |
| **DATE**        | File creation or processing date (ISO8601, `YYYYMMDD`) | `20251007`                                       | Use the STIX `<CreateDate>` metadata when available; otherwise system date |
| **BOARDNUMBER** | Unique board identifier                            | `67130`                                          | Always numeric; zero-pad if needed; Use the STIX metadata when available 
| **BOARDACRONYM** | Unique acronym for board  | `UGDSB`, `WCDSB`
| **SCHOOLTYPE**  | Level of school                                    | `elementary`, `secondary`                        | Always lowercase                                                           |
| **DATASET**     | File purpose or type                               | `enrollment` | Short, clear, no spaces                                                    |
| **STAGE**       | Step in the workflow                               | `raw`, `clean`, `validated`   | Indicates progress through data pipeline                                   |
| **EXT**         | File extension                                     | `xml`, `csv`, `yaml`, `json`                     | Match actual format                                                        |

## Usage

1. Place all STIX xml enrollment files in a folder e.g. STIXfix
2. Activate your python venv
3. Run the cleaning script: 

```
python stix_fix.py
```

## Assumptions Using Automated Method 

* All invalid postal codes are discarded - validity of postal codes checked by ensuring that the alphanumeric code follows the correct format
* Phone numbers with string characters (words) are discarded
* Phone numbers with special characters - special characters are removed first 
* Phone numbers are then checked to ensure that they are 10 characters long 
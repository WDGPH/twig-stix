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
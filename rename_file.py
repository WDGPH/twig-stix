import xml.etree.ElementTree as ET
import re
import sys
import xmltodict
import os

# Using the metadata, rename the file to our standard naming convention

path = sys.argv[1]
school_type = sys.argv[2]  # 'Elementary' or 'Secondary'

# Check for valid school type
if school_type not in ['elementary', 'secondary']:
    print("Error: school_type must be 'elementary' or 'secondary'")
    sys.exit(1)

tree = ET.parse(path)
root = tree.getroot()

with open(path, 'r', encoding='utf-8') as file:
    dict_data = xmltodict.parse(file.read())

metadata = dict_data['ns1:SchoolUpload']['ns1:Metadata']

print(metadata)
create_date = metadata['ns1:CreateDate']
board_number = metadata['ns1:SchoolBoard']['ns1:BoardNumber']

# Format date as YYYYMMDD
create_date_formatted = re.sub(r'(\d{4})-(\d{2})-(\d{2}).*', r'\1\2\3', create_date)

new_filename = f"{create_date_formatted}_{board_number}_{school_type}_STIX.xml"

print(f"Renaming file to: {new_filename}")
os.rename(path, new_filename)

# Verify the rename
if os.path.exists(new_filename):
    print(f"File successfully renamed to: {new_filename}")
else:
    print("Error: File rename failed.")

# Remove the old file if it still exists
if os.path.exists(path):
    os.remove(path)
    print(f"Old file {path} removed.")
import xml.etree.ElementTree as ET
import re
import sys
import xmltodict
import logging

path = sys.argv[1]
school_number = sys.argv[2]  # School number to extract
logfile = path.replace('.xml','.log')

tree = ET.parse(path)
root = tree.getroot()

with open(path, 'r', encoding='utf-8') as file:
    dict_data = xmltodict.parse(file.read())

logging.basicConfig(level=logging.INFO, filename=logfile, filemode='w',)

# start logging file
logging.info(f"Processing file: {path}")

# Get keys at the second level
records = dict_data['ns1:SchoolUpload']['ns1:School']

student_list = []
counter = 0
ns = {"ns1": "http://ontario.ca"}

logging.info(f"Total number of schools in the file: {len(records)}")
logging.info(f"Extracting school with number: {school_number}")



for school in root.findall(".//ns1:School", ns):
    school_record = school.find("ns1:SchoolNumber", ns)
    if school_record is not None and school_record.text == school_number: 
        logging.info(f"Found and removing school with number: {school_number}")
        

logging.info(f"Total number of schools after removal: {len(root.findall('.//ns1:School', ns))}")
# Check to make sure the schools were removed
for school in root.findall(".//ns1:School", ns):
    school_number = school.find("ns1:SchoolNumber", ns)
    if school_number is not None and school_number.text in remove_school_numbers:
        logging.info(f"School with number {school_number.text} was not removed.")
    else:
        logging.info(f"School with number {school_number.text} is present.")


# Write the modified XML back to a file
output_path = path.replace('.xml','_cleaned.xml')
tree.write(output_path, encoding='utf-8', xml_declaration=True)
logging.info(f"Cleaned XML file written to: {output_path}")
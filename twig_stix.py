import re
import sys
import xmltodict
import logging
from lxml import etree

def rename_file(metadata, school_type):
    if school_type not in ['elementary', 'secondary']:
        print("Error: school_type must be 'elementary' or 'secondary'")
        sys.exit(1)
    
    # create_date = metadata['ns1:CreateDate']
    # # board_number = metadata['ns1:SchoolBoard']['ns1:BoardNumber']
    # board_name = metadata['ns1:SchoolBoard']['ns1:Name']
    
    # Remove spaces and special characters from board name
    # board_name_clean = re.sub(r'[^A-Za-z0-9]', '', board_name)

    # # Format date as YYYYMMDD
    # create_date_formatted = re.sub(r'(\d{4})-(\d{2})-(\d{2}).*', r'\1\2\3', create_date)



def clean_phone(text: str) -> str:
    digits = re.sub(r"\D", "", text)
    if digits.startswith("1") and len(digits) > 10:
        digits = digits[1:]

    # then readd hyphenated format
    if len(digits) < 10:
        logging.warning(f"Phone number '{text}' has less than 10 digits. Setting to empty.")
        return ""
    
    elif len(digits) > 10:
        # Check for x and 3 digits after with regex
        if not re.match(r'.*x\d{1,4}$', text):
            logging.warning(f"Phone number '{text}' has more than 10 digits and no valid extension. Truncating to 10 digits.")
            digits = digits[:10]
        else:
            digits = digits[:3] + '-' + digits[3:6] + '-' + digits[6:10] + 'x' +  digits[10:]
    if len(digits) == 10:
        digits = digits[:3] + '-' + digits[3:6] + '-' + digits[6:10]

        # Check for valid area codes (just a few common ones for Ontario)
        # FIXME get list of valid area codes
        invalid_area_codes = ['163','081']

        if digits.startswith(tuple(invalid_area_codes)):
            logging.warning(f"Phone number '{text}' has invalid area code. Setting to empty.")
            return ""
        
        if digits == '519-000-0000':
            logging.warning(f"Phone number '{text}' is all zeros. Setting to empty.")
            return ""

    # Allow extensions
    return digits

def check_metadata_schema(record):
    # Check for missing required fields
    required_fields = ['ns1:CreateDate', 'ns1:CreateTime', 
                    'ns1:CreatedBy', 'ns1:ContactNumber', 
                    'ns1:ContactEmail', 
                    'ns1:FullUpload', 'ns1:SchoolBoard',
                    'ns1:BoardNumber', 'ns1:Name']
    for field in required_fields:
        if field not in record:
            logging.warning(f"Record {record.get('ns1:SchoolNumber', 'Unknown')} is missing required fields: {', '.join(required_fields)}")
            record[field] = ""  # Add empty field if missing
    return record

def remove_school_by_number(school_number, root, ns):
    logging.info(f"Removing school with number: {school_number}")
    for school in root.findall(".//ns1:School", ns):
        school_number = school.find("ns1:SchoolNumber", ns)
        if school_number is not None and school_number.text == school_number: 
            logging.info(f"Found and removing school with number: {school_number}")
            root.remove(school)
    
    return root

path = sys.argv[1]
logfile = path.replace('.xml','.log')

parser = etree.XMLParser(remove_blank_text=True)
tree = etree.parse(path, parser)
root = tree.getroot()

with open(path, 'r', encoding='windows-1252') as file:
    dict_data = xmltodict.parse(file.read())

logging.basicConfig(level=logging.INFO, filename=logfile, filemode='w',)

# Check metadata schema
dict_data['ns1:Metadata'] = check_metadata_schema(dict_data.get('ns1:Metadata', {}))

# Start by calculating the total number of entries
records = dict_data['ns1:SchoolUpload']['ns1:School']
ns = {"ns1": "http://ontario.ca"}
total_students = 0
school_records_to_remove = []
for record in records:
    try:
        student_info = record['ns1:Students']['ns1:Student']
        total_students += len(student_info)
    except TypeError:
        logging.info(f"Record {record.get('ns1:SchoolNumber', 'Unknown')} has no students.")
        school_records_to_remove.append(record.get('ns1:SchoolNumber', None))
        # Remove these records from the XML

for i in school_records_to_remove:
    logging.info(f"Removing school with number: {i}")
    for school in root.findall(".//ns1:School", ns):
        school_number = school.find("ns1:SchoolNumber",ns)
        if school_number is not None and school_number.text == i: 
            logging.info(f"Found and removing school with number: {i}")
            root.remove(school)

logging.info(f"Total students to process: {total_students}")

# start logging file
logging.info(f"Processing file: {path}")
logging.info(f"Logging to file: {logfile}")


# loop through all phone numbers and clean them
for elem in root.iter():
    row_num = elem.sourceline
    if row_num == 912:
        print(elem.tag, elem.text)
    if 'Phone' in elem.tag:
        original_phone = elem.text
        if original_phone:
            cleaned_phone = clean_phone(original_phone)
            if cleaned_phone != original_phone:
                logging.info(f"Row {row_num}: Cleaned phone number from '{original_phone}' to '{cleaned_phone}'")
                elem.text = cleaned_phone
            if not cleaned_phone:
                logging.warning(f"Row {row_num}: Phone number '{original_phone}' could not be cleaned and was set to empty.")
                elem.text = ""

    if 'StreetNumber' in elem.tag:
        street_number = elem.text
        parent = elem.getparent()
        street_name = None

        # Look for sibling StreetName in same parent
        if parent is not None:
            for sibling in parent:
                if 'StreetName' in sibling.tag:
                    street_name = sibling.text
                    break
        if street_number and len(street_number) > 6:
            logging.warning(f"Row {row_num}: Street number '{street_number}' exceeds maximum length of 6.")

            # Ask user to input a corrected street number
            new_street_number = input(f"Please enter a corrected street number for '{street_number}'"
                                      f"\nStreet Name:{street_name} (or press Enter to skip): "
                                     ).strip()
            # Ask user whether to update the street name as well
            new_street_name = None
            if street_name:
                update_name = input(f"Do you want to update the street name '{street_name}' as well? (y/n): ").strip().lower()
                if update_name == 'y':
                    new_street_name = input(f"Please enter the corrected street name for '{street_name}': ").strip()

            if new_street_number:
                if new_street_number == "":
                    elem.text = ""
                else:
                    elem.text = new_street_number
                logging.info(f"Row {row_num}: Updated street number to '{new_street_number}'.")
            if new_street_name and parent is not None:
                for sibling in parent:
                    if 'StreetName' in sibling.tag:
                        sibling.text = new_street_name
                        logging.info(f"Row {row_num}: Updated street name to '{new_street_name}'.")
                        break


    # Check unit length
    if 'Unit' in elem.tag:
        row_num = elem.sourceline
        original_unit = elem.text.lower() if elem.text else None
        if original_unit is not None:
            if original_unit and len(original_unit) > 5:
                logging.warning(f"Unit '{original_unit}' exceeds maximum length of 5.")
                
                if original_unit == 'basement':
                    elem.text = 'BSMT'
                    logging.info(f"{row_num}: Standardized unit 'basement' to 'BSMT'.")
                
                # if element contains
                elif elem.text.lower() == 'lower un':
                    elem.text = 'LOWR'
                    logging.info(f"{row_num}: Standardized unit 'lower un' to 'LOWR'.")
                
                elif elem.text.lower() == 'd lower':
                    elem.text = 'LOWR'
                    logging.info(f"{row_num}: Standardized unit 'd lower' to 'LOWR'.")
                
                elif elem.text.lower() == 'upperlev':
                    elem.text = 'UPPR'
                    logging.info(f"{row_num}: Standardized unit 'UpperLev' to 'UPPR'.")
                
                elif elem.text.lower() == 'main flo':
                    elem.text = 'MAIN'
                    logging.info(f"{row_num}: Standardized unit 'main flo:' to 'MAIN'.")
                
                elif elem.text.lower() == 'mainfloo':
                    elem.text = 'MAIN'
                    logging.info(f"{row_num}: Standardized unit 'mainfloo' to 'MAIN'.")
                
                #look for brackets anywhere in the string and remove them
                elif re.match(r'.*\(.*\).*', elem.text):
                    new_unit = re.sub(r'[\(\)]', '', elem.text)
                    logging.info(f"{row_num}: Standardized unit '{original_unit}' to '{new_unit}'.")
                    elem.text = new_unit

                elif re.match('unit \d+', elem.text.lower()):
                    # remove 'unit ' and keep the number
                    new_unit = re.sub(r'unit', '', elem.text.lower())
                    logging.info(f"{row_num}: Standardized unit '{original_unit}' to '{new_unit}'.")
                    elem.text = new_unit.strip()

                else: 
                    # Cannot standardize - flag for manual review
                    # print out the row number if possible
                    logging.warning(f"Row {row_num}: Unit '{original_unit}' could not be standardized. Requires manual review.")
                    street_number = None
                    street_name = None
                    parent = elem.getparent()
                    if parent is not None:
                        for sibling in parent:
                            if 'StreetNumber' in sibling.tag:
                                street_number = sibling.text
                            if 'StreetName' in sibling.tag:
                                street_name = sibling.text
                    # Ask user to input a corrected unit
                    new_unit = input(
                        f"Please enter a corrected unit for '{original_unit}' (or press Enter to skip): "
                        f"\nContext: Street Number: {street_number}, Street Name: {street_name}: "
                    ).strip()
                    # Print out the street number and street name for context
                    # If user pressed enter then replace with empty
                    print(new_unit)
                    if new_unit == "":
                        elem.text = ""
                        logging.info(f"Row {row_num}: Updated unit to '{new_unit}'.")
                    elif new_unit:
                        elem.text = new_unit
                        logging.info(f"Row {row_num}: Updated unit to '{new_unit}'.")

# Write cleaned XML to new file
clean_path = path.replace(".xml", "_CLEAN.xml")

tree.write(clean_path, xml_declaration=True, encoding="utf-8", pretty_print=True)
logging.info(f"✔ Cleaned file saved: {clean_path}")
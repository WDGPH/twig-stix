import pandas as pd
import xmltodict
import sys
import argparse 
import logging

# Set up logging
logfile = 'pull_info.log'
logging.basicConfig(level=logging.INFO, filename=logfile, filemode='w',)

argparser = argparse.ArgumentParser(description='Extract student info from school XML.')
argparser.add_argument('input', type=str, help='Path to the XML file')
argparser.add_argument('output', type=str, help='Path to the output XML file')

args = argparser.parse_args()

# Validate input file exists and is readable
try:
    with open(args.input, 'r', encoding='utf-8') as f:
        pass
except Exception as e:
    print(f"Error reading input file: {e}")
    sys.exit(1)

with open(args.input, 'r', encoding='utf-8') as file:
    dict_data = xmltodict.parse(file.read())
    logging.info(f"Successfully parsed XML file: {args.input}")

# Get keys at the second level
records = dict_data['ns1:SchoolUpload']['ns1:School']

student_list = []
counter = 0

# For each record, get the next level
for record in records:
    counter = counter + 1 

    school_name = record['ns1:Name']
    school_number = record['ns1:SchoolNumber']
    student_info = record['ns1:Students']['ns1:Student']

    # Collect student name
    for student in student_info:
        student_name = student['ns1:Name']
        first_name = student_name.get('ns1:First', '')
        middle_name = student_name.get('ns1:Middle', '')
        last_name = student_name.get('ns1:Last', '')
        student_class = student.get('ns1:Class', None)
        

        birth_date = student.get('ns1:BirthDate', None)
        grade = student.get('ns1:Grade', None)

        # Create a list of dictionaries for each student
        student_dict = {
            'SchoolName': school_name,
            'SchoolNumber': school_number,
            'FirstName': first_name,
            'MiddleName': middle_name,
            'LastName': last_name,
            'BirthDate': birth_date,
            'Grade': grade,
            'Class': student_class
        }

        # Append to a list
        student_list.append(student_dict)

# Convert to DataFrame
df_students = pd.DataFrame(student_list)

# Extract birth year
df_students['BirthYear'] = pd.to_datetime(df_students['BirthDate']).dt.year
school_counts = df_students.groupby(['SchoolName', 'BirthYear']).size().reset_index(name='StudentCount')
grade_counts = df_students.groupby(['SchoolName', 'Grade']).size().reset_index(name='GradeCount')

# Filter by students born in 2012 and 2013
df_filtered = df_students[
    (df_students['BirthYear'] == 2012) | (df_students['BirthYear'] == 2013)
]

df_filtered = df_filtered[
    (df_filtered['Grade'] == 'GR7') | (df_filtered['Grade'] == 'GR8')
]

logging.info(f"Total schools processed: {school_counts['SchoolName'].nunique()}")
logging.info(f"Total students extracted: {len(df_students)}")
logging.info(f"Birth year distribution:\n{df_students['BirthYear'].value_counts()}")
logging.info(f"Grade distribution:\n{grade_counts}")
logging.info(f"Total students born in 2012 and 2013: {len(df_filtered)}")
logging.info(f"Grade distribution for filtered students:\n{df_filtered['Grade'].value_counts()}")
logging.info(f"Schools with filtered students:\n{df_filtered['SchoolName'].unique()}")

# Save to Excel
outpath = args.output.replace('.xml', '.xlsx')
with pd.ExcelWriter(outpath, engine='openpyxl') as writer:
    df_students.to_excel(writer, sheet_name='All_Students', index=False)
    df_filtered.to_excel(writer, sheet_name='Filtered_Students', index=False)
    school_counts.to_excel(writer, sheet_name='School_Counts', index=False)
    grade_counts.to_excel(writer, sheet_name='Grade_Counts', index=False)


import pandas as pd
import xmltodict
import sys
import argparse 

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


# Get year of birth from birthdate
df_students['BirthYear'] = pd.to_datetime(df_students['BirthDate']).dt.year

# Group by school and birth year and count students
school_counts = df_students.groupby(['SchoolName', 'BirthYear']).size().reset_index(name='StudentCount')
print(school_counts)
print(df_students['BirthYear'].value_counts())

# Group by school and birth year and count students
grade_counts = df_students.groupby(['SchoolName', 'Grade']).size().reset_index(name='GradeCount')
print(grade_counts)


# Filter by students born in 2012 and 2013
df_filtered = df_students[
    (df_students['BirthYear'] == 2012) | (df_students['BirthYear'] == 2013)
]

print(f"Total students born in 2012 and 2013: {len(df_filtered)}")
print(df_filtered['Grade'].value_counts())

# Ensure we only have grade 8 and 7 students 
df_filtered = df_filtered[
    (df_filtered['Grade'] == 'GR7') | (df_filtered['Grade'] == 'GR8')
]
print(df_filtered)
print(f"Total students in GR7 and GR8: {len(df_filtered)}")
print(df_filtered['Grade'].value_counts())

print(df_filtered['SchoolName'])

# # Save to CSV
# outpath = path.replace('.xml', '.csv')
# df_filtered.to_csv(outpath, index=False, encoding='utf-8-sig')

from pdfminer.high_level import extract_text
import re

def extract_cv_info(filepath):
    text = extract_text(filepath)
    
    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    skills = extract_skills(text)
    education = extract_education(text)
    
    return {
        'name': name,
        'email': email,
        'phone': phone,
        'skills': skills,
        'education': education
    }

def extract_name(text):
    lines = text.split('\n')
    name_start_flag = False
    for line in lines:
        stripped_line = line.strip()
        if not name_start_flag and re.search(r'\d$', stripped_line):
            continue
        if not name_start_flag:
            name_start_flag = True
        
        if stripped_line and not extract_email(stripped_line) and not extract_phone(stripped_line):
            return stripped_line
    
    return 'N/A'

def extract_email(text):
    match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    return match.group(0) if match else ''

def extract_phone(text):
    match = re.search(r'\+?\d[\d -]{8,12}\d', text)
    return match.group(0) if match else ''

def extract_skills(text):
    skills = []
    lines = text.split('\n')

    # Look for the skills section
    skills_section = False
    for line in lines:
        if re.search(r'\bskills\b', line, re.IGNORECASE):
            skills_section = True
            continue
        
        if skills_section:
            if line.strip() == "":
                break
            skills.extend([skill.strip() for skill in line.split(',') if skill.strip()])
    
    # Join the list into a single string with comma separation
    return ', '.join(skills) if skills else 'N/A'


def extract_education(text):
    education = []
    lines = text.split('\n')

    # Look for the education section
    education_section = False
    for line in lines:
        if re.search(r'\beducation\b', line, re.IGNORECASE):
            education_section = True
            continue
        
        if education_section:
            if line.strip() == "":
                break
            education.append(line.strip())
    
    # Join the list into a single string
    return '\n'.join(education) if education else 'N/A'

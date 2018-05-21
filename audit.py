#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import clean
import pprint

osm_file = open("flensburg_sample.osm", "r")

keys = []
street_names = []
unique_street_names = []
postal_codes = []
unique_postal_codes = []
phone_numbers = []
unique_phone_numbers = []

handcleaning = True

def force_unicode(text):
    # Reference: stackoverflow
    "If text is unicode, it is returned as is. If it's str, convert it to Unicode using UTF-8 encoding"
    return text if isinstance(text, unicode) else text.decode('utf8')

def was_cleaned(elem_in, elem_out):
    return force_unicode(elem_in) != force_unicode(elem_out)

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def is_postal_code(elem):
    return (elem.attrib['k'] == "addr:postcode")

def is_phone_number(elem):
    return (elem.attrib['k'] == "phone")

def is_seamark(elem):
    return (elem.attrib['k'] == "seamark")

def nearly_equal(string1, string2):
    # check differences in exactly one character for string lengths that differ by maximum 1
    if abs(len(string1) - len(string2)) <= 1:
        count_diffs = 0
        for a, b in zip(string1, string2):
            if a!=b:
                count_diffs += 1
        # return street names that differ in at least 1, but not more than 2 characters
        if count_diffs in [1,2]:
            return True
        else:
            return False

def audit():
    # audit street names and return cleaned and sorted unique street names
    if handcleaning:
        print '############# Hand Cleaned Street Names #################################\n'
    else:
        print '############# Cleaned Street Names ######################################\n'
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                
                # determine all available keys in the data set
                keys.append(tag.attrib['k'])
                
                # if the key is a street name, clean it if necessary
                if is_street_name(tag):
                    # the imported clean function is called and updated according to the findings during auditing
                    cleaned_street = clean.clean_street(tag.get('v').encode('utf8'), handcleaning)
                    # check, if the street name was cleaned, and print if True
                    if was_cleaned(tag.get('v'),cleaned_street):
                        print tag.get('v'),' -> ',cleaned_street
                    # the cleaned street name is appended to a list
                    street_names.append(cleaned_street)
                
                # if the key is a postal code, check if it is reasonable
                if is_postal_code(tag):
                    # the imported clean function checks, that the postal code has theexpected form for northern
                    # Germany and deletes it if this is not the case
                    cleaned_postal_code = clean.clean_postal_code(tag.get('v').encode('utf8'))
                    # check, if the postal code was cleaned, and print if True
                    if was_cleaned(tag.get('v'), cleaned_postal_code):
                        print tag.get('v'),' -> ',cleaned_postal_code
                    # the cleaned postal code is appended to a list
                    postal_codes.append(cleaned_postal_code)
                    
                # if the key is a phone number, check if it is reasonable
                if is_phone_number(tag):
                    # the imported clean function converts the phone number into a common format
                    cleaned_phone_number = clean.clean_phone(tag.get('v').encode('utf8'))
                    # check, if the phone number was cleaned, and print if True
                    if was_cleaned(tag.get('v'), cleaned_phone_number):
                        print tag.get('v'),' -> ',cleaned_phone_number
                    # the cleaned postal code is appended to a list
                    phone_numbers.append(cleaned_phone_number)
                    
    # create lists of unique sorted values for easy auditing
    unique_keys = sorted(set(keys))
    unique_street_names = sorted(set(street_names))                
    unique_postal_codes = sorted(set(postal_codes))
    unique_phone_numbers = sorted(set(phone_numbers))
                    
    print '\n############# Nearly Equal Street Names ################################\n'
    # find street names that differ in only one character and print for auditing
    left_street_names = []
    right_street_names = []
    for left_street_name in unique_street_names:
        for right_street_name in unique_street_names:
            if nearly_equal(left_street_name, right_street_name) and not (left_street_name in right_street_names):
                left_street_names.append(left_street_name)
                right_street_names.append(right_street_name)
                
    for name_tuple in zip(left_street_names, right_street_names):
        print name_tuple[0] + ' | ' + name_tuple[1]
        
                
    print '\n############# Street Names with Possibly Special Characters ############\n'
    # find street names that differ in only one character and print for auditing
    for unique_street_name in unique_street_names:            
        for alias_str in ['ss','ae','oe','ue']:
            if unique_street_name.lower().rfind(alias_str) != -1:
                print unique_street_name
    
    print '\n############# Available Keys for Auditing ################################\n'
    pprint.pprint(unique_keys)
    
#    print '\n############# Unique Street Names after Cleaning #########################\n'
#    for n in unique_street_names:
#        print n
#        
#    print '\n############# Unique Postal Codes after Cleaning #########################\n'
#    pprint.pprint(unique_postal_codes)
#    
#    print '\n############# Unique Phone Numbers after Cleaning ########################\n'
#    pprint.pprint(unique_phone_numbers)  
                
                
if __name__ == '__main__':
    audit()
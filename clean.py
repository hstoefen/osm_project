# -*- coding: utf-8 -*-
"""
Created on Fri Apr 20 09:24:56 2018

@author: th84sn

some of the functions in this script were inspired by Frank Leuenberger, who has taken the course before me.
A lot of the code has also been created with the help of stackoverflow and the Udacity training material
"""

import string
import re

def clean_street(street, handcleaning):
    if street.lower().rfind('strasse') != -1: # convert to lower and look for 'strasse'
        return string.replace(street,'trasse','traße') # return street with 'trasse' replaced by 'traße' in order to preserve capitals
    elif street.lower().rfind('str.') != -1: # not found, then look for 'str.'
        return string.replace(street,'str.','straße') # return street with 'str.' replaced by 'straße'
    
    # hand cleaned street names
    if handcleaning:
        if street.lower().rfind('schloss') != -1: # find Schloss/Schloß (castle), which also has the problematic letter ß
            return string.replace(street,'chloss','chloß') # replace 'ss' with 'ß'    
        if street == 'Scandinavian Park' or street == 'Scandinavien-Park':
            return 'Scandinavian-Park'
        if street == 'Geheimrat-Dr.-Schaedel-Straße':
            return 'Geheimrat-Doktor-Schaedel-Straße'
    
    return street

def clean_postal_code(postal_code):
    postal_code_area = re.compile(r'^2[0-5]{1}[0-9]{3}') # regex for postal codes in northern Germany
    if postal_code_area.search(postal_code):
        return postal_code
    else:
        return u'no valid postal code'

def clean_phone(phone):    
    # convert phone numbers according to recommendation E.123 from ITU
    # https://en.wikipedia.org/wiki/E.123
     
    phone = phone.translate(None,'/-(). ')             # remove all special characters commonly used in phone numbers, except +
    if phone.startswith('00'):                    # replace leading 00 from country code with +
        phone = phone.replace('00','+',1)
    elif phone.startswith('0'):                    # replace leading 0 from area code with '+49 '
        phone = phone.replace('0','+49',1)      
    
    l = list(phone)
    if phone.startswith('+'):                    # add whitespace after two-digit country code and again after 3-digit area code (only for Germany)
        l.insert(3, ' ')
        if phone.startswith('+49'):
            l.insert(7, ' ')
        phone = ''.join(l)
    
    return phone
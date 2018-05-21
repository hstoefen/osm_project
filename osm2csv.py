#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
clean OSM data and output .csv files

"""

import csv
import codecs
import re
import xml.etree.cElementTree as ET
import clean

OSM_PATH = "flensburg.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

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

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""
	
    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    tag_type = default_tag_type
    nd_pos = 0

    # parse tags for nodes and ways
    tags_dict = {}
    for tag in element.iter('tag'):
        if not problem_chars.search(tag.attrib['k']):
            # if the key is a street name, clean it if necessary
            if is_street_name(tag):
                # the imported clean function is called and updated according to the findings during auditing
                tag_value = clean.clean_street(tag.get('v').encode('utf8'), handcleaning)
            # if the key is a postal code, check if it is reasonable
            elif is_postal_code(tag):
                # the imported clean function checks, that the postal code has theexpected form for northern
                # Germany and deletes it if this is not the case
                tag_value = clean.clean_postal_code(tag.get('v').encode('utf8'))
            # if the key is a phone number, check if it is reasonable
            elif is_phone_number(tag):
                # the imported clean function converts the phone number into a common format
                tag_value = clean.clean_phone(tag.get('v').encode('utf8'))
            else:
                tag_value = tag.get('v')
            tag_key = tag.attrib['k']
            if ':' in tag.attrib['k']:
                tag_type = re.split(':',tag.attrib['k'])[0]
                tag_key = re.split(':',tag.attrib['k'], maxsplit=1)[1]
            tags_dict = { \
                         'id': element.attrib['id'], \
                         'key': tag_key, \
                         'value': tag_value, \
                         'type': tag_type \
                         }
            tags.append(tags_dict)

    # parse nd tags for ways
    nd_dict = {}
    for tag in element.iter('nd'):
        nd_dict = { \
                   'id': element.attrib['id'], \
                   'node_id': tag.attrib['ref'], \
                   'position': nd_pos \
                   }
        way_nodes.append(nd_dict)
        nd_pos += 1

    # return dictionries for nodes and ways	
    if element.tag == 'node':
        for node_field in node_attr_fields:
            node_attribs[node_field] = element.attrib[node_field]
        #print tags
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        for way_field in way_attr_fields:
            way_attribs[way_field] = element.attrib[way_field]        
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'wb') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'wb') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'wb') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'wb') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'wb') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cleaning of data

"""

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

#import cerberus

import schema

OSM_PATH = "flensburg_sample.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


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
            tag_key = tag.attrib['k']
            if ':' in tag.attrib['k']:
                tag_split = re.split(':',tag.attrib['k'], maxsplit=1)
                tag_type = tag_split[0]
                tag_key = tag_split[1]
            tags_dict = { \
                         'id': element.attrib['id'], \
                         'key': tag_key, \
                         'value': tag.attrib['v'], \
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

    # return dictionaries for nodes and ways	
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

# Python 2.7
#class UnicodeDictWriter(csv.DictWriter, object):
#    """Extend csv.DictWriter to handle Unicode input"""

#    def writerow(self, row):
#        super(UnicodeDictWriter, self).writerow({
#            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
#        })

#    def writerows(self, rows):
#        for row in rows:
#            self.writerow(row)

# Python 3.6
class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, str) else v) for k, v in iter(row.items())
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

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
    process_map(OSM_PATH)
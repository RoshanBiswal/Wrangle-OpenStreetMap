
# coding: utf-8

# In[ ]:

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema
import Improving_Street_Names
from Improving_Street_Names import update_name, mapping,name
Improving_Street_Names.update_name(name, mapping)
Improving_Street_Names.mapping
OSM_PATH = "pune_india.osm"

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
    toc = 0
    # YOUR CODE HERE
  
    if element.tag == 'node':
        for i in NODE_FIELDS:
            node_attribs[i] = element.attrib[i]
        for tag in element.iter("tag"):
            node_tags_attribs = {}
            temp = LOWER_COLON.search(tag.attrib['k'])
            is_pc = PROBLEMCHARS.search(tag.attrib['k'])
            if is_pc:
                continue
            if tag.attrib["k"] == 'addr:street': 
                node_tags_attribs["value"] = update_name(tag.attrib["v"], mapping)
                node_tags_attribs["id"] = element.attrib['id']
                node_tags_attribs["key"] = tag.attrib["k"].split(':',1)[1]
                node_tags_attribs["type"] = tag.attrib["k"].split(':',1)[0]
            elif temp:
                split_char = temp.group(1)
                split_index = tag.attrib['k'].index(split_char)
                type1 = temp.group(1)
                node_tags_attribs['id'] = element.attrib['id']
                node_tags_attribs['key'] = tag.attrib['k'][split_index+2:]
                node_tags_attribs['value'] = tag.attrib['v']
                node_tags_attribs['type'] = tag.attrib['k'][:split_index+1]
            else:
                node_tags_attribs['id'] = element.attrib['id']
                node_tags_attribs['key'] = tag.attrib['k']
                node_tags_attribs['value'] = tag.attrib['v']
                node_tags_attribs['type'] = 'regular'
            tags.append(node_tags_attribs)
            
            
        return {'node': node_attribs, 'node_tags': tags}
        
    elif element.tag == 'way':
        id = element.attrib['id']
        for i in WAY_FIELDS:
            way_attribs[i] = element.attrib[i]
        for i in element.iter('nd'):
            idu = {}
            idu['id'] = id
            idu['node_id'] = i.attrib['ref']
            idu['position'] = toc
            toc+=1
            way_nodes.append(idu)
        for c in element.iter('tag'):
            temp = LOWER_COLON.search(c.attrib['k'])
            is_pc = PROBLEMCHARS.search(c.attrib['k'])
            eu = {}
            if is_pc:
                continue
            if c.attrib['k'] == 'addr:street': 
                eu['value'] = update_name(c.attrib['v'], mapping)
                eu['id'] = id
                eu['key'] = c.attrib["k"].split(':',1)[1]
                eu['type'] = c.attrib["k"].split(':',1)[0]
            elif temp:
                split_char = temp.group(1)
                split_index = c.attrib['k'].index(split_char)
                eu['id'] = id
                eu['key'] = c.attrib['k'][split_index+2:]
                eu['type'] = c.attrib['k'][:split_index+1]
                eu['value'] = c.attrib['v']
            else:
                eu['id'] = id
                eu['key'] = c.attrib['k']
                eu['type'] = 'regular'
                eu['value'] = c.attrib['v']
            tags.append(eu)
            
        
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


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


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

    with codecs.open(NODES_PATH, 'w') as nodes_file,          codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file,          codecs.open(WAYS_PATH, 'w') as ways_file,          codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file,          codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

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

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

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


# In[ ]:




# In[ ]:




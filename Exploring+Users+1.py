
# coding: utf-8

# In[ ]:

import xml.etree.cElementTree as ET
import pprint
import re
filename='pune_india.osm'


def get_user(element):
    return element.get("uid")


def process_id(filename):
    users = set()
    for _, element in ET.iterparse(filename):
        user = get_user(element)
        if user != None:
         users.add(user)
        

    return users


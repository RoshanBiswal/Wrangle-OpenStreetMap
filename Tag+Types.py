
# coding: utf-8

# In[1]:

import xml.etree.cElementTree as ET
import pprint
import re
filename='pune_india.osm'

# In[2]:

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


def key_type(element, keys):
    if element.tag == "tag":
        if re.match(lower,element.get("k"))!=None:
            keys["lower"]+=1
        elif re.match(lower_colon,element.get("k"))!=None:
            keys["lower_colon"]+=1
        elif re.match(problemchars,element.get("k"))!=None:
            keys["problemchars"]+=1
        else:
            keys["other"]+=1
    return keys



def process_map(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(file):
        keys = key_type(element, keys)


    return keys


# In[ ]:





# coding: utf-8

# In[1]:

import xml.etree.cElementTree as ET
import pprint


# In[2]:

filename='pune_india.osm'


# In[3]:

def count_tags(filename):
    tags={}
    for event,elem in ET.iterparse(filename):
        if elem.tag in tags:
            tags[elem.tag]+=1
        else:
            tags[elem.tag]=1
    return tags


# In[ ]:




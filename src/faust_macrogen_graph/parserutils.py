#TODO: rename utils
from pathlib import Path
from xml.dom import minidom

#TODO: etwas umschreiben
def generate_file_list(path, file_extension=".xml"):
    """Returns a Generator with all files that will be processed.
    
    Args:
        path (str): Path to the desired directory.
        file_extension (str): File extension to search for.
    Returns:
        Generator which contains Path objects to all XML files in the given directory and its subdirectories.
        
    """
    return Path(path).glob("**/*{}".format(file_extension))

#TODO: entshceidne ob no source richtige bezeichnung
def relation_items(nodelist, items, temppre=True):
    """Returns an edited list of <item>-lists
    
    Args:
        nodelist (NodeList): NodeList of <relation>-Elements.
        items (list): List of <item>-lists, generated by xmlparser.
        temppre (bool): If True, the function only adds temp-pre child-items, else it adds temp-syn child-items.
    Returns:
        Edited list of <item>-lists.
    
    """
    tmp_items = items
    for element in nodelist:
        if element.getAttribute("name") == "temp-pre" and temppre:
            tmp_nodelist = []
            tmp_sources = []
            tmp_nodes = []
            for child in element.childNodes:      
                if child.nodeName == "source":
                    tmp_sources.append(child.attributes["uri"].value)
            
            #if no source is given
            if not tmp_sources:
                tmp_sources.append("no source")
                    
            for child in element.childNodes:
                if child.nodeName == "item":
                    tmp_nodes.append(child.attributes["uri"].value)
            
            tmp_nodelist.append(tmp_sources)    
            tmp_nodelist.append(tuple(tmp_nodes))                   
            tmp_items.append(tuple(tmp_nodelist))
            
#TODO: von temppre gewichte übernehmen       
        elif element.getAttribute("name") == "temp-syn" and temppre==False:
            tmp_nodelist = []
            for child in element.childNodes:
                if child.nodeName == "item":
                    uri_value = child.attributes["uri"].value
                    tmp_nodelist.append(uri_value)
            tmp_items.append(tuple(tmp_nodelist))
        
    return tmp_items

def xmlparser(path, absolute=False):
    """Parses only xml-files inside a directory.
    
    Args:
        path (str): Path to desired directory.
        absolute (bool): If True, the parser parses <date>-elements, else it parses <relation>-elements.
    Returns:
        
    """
    items = []
    parsed_elements = None
    for file in generate_file_list(path):
        xml_text = minidom.parse(str(file))
        if absolute:
            parsed_elements = xml_text.getElementsByTagName("date")
        else:
            parsed_elements = xml_text.getElementsByTagName("relation")
            items = relation_items(parsed_elements, items)

    return items
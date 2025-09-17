import re
from xml.etree.ElementTree import Element

def parse_attributes(attrib: str):
    """
    Parse a string of attributes from an xml

    Args:
        attrib (str): A string of attributes from an xml

    Returns:
        dict[str, str]: A well formatted dictionary of attributes
    """
    attrib_pair_re = re.compile(r"(?P<tag>\w+) (?P<text>\{[\.\w\s:;\d]+\})")
    attrib_inner_re = re.compile(r"(?P<tag>\w+):(?P<text>[\.\w\s\d]+)")
    all_attribs = attrib_pair_re.findall(attrib)
    inner_found = {k:attrib_inner_re.findall(v[1:-1]) for k,v in all_attribs}
    return {k0: {k1:v1 for k1, v1 in v0} for k0, v0 in inner_found.items()}


def extract_attribute_text(line: Element, attrib_name: str, attribs: dict[any, any]):
    """
    Extract text from an Tkb PAGE XML line by getting the offset and length attributes

    Args:
        line (Element): A text line in an xml
        attrib_name (str): The name of an attribute
        attribs (dict[str, str]): A dictionary of attributes containing length and offset

    Returns:
        _type_: _description_
    """
    if "offset" not in attribs[attrib_name]:
        raise KeyError(f"offset not in attributes for {attrib_name}")
    elif "length" not in attribs[attrib_name]:
        raise KeyError(f"length not in attributes for {attrib_name}")
    
    offset, length = int(attribs[attrib_name].pop("offset")), int(attribs[attrib_name].pop("length"))
    return line[2][0].text[offset:offset + length]
from collections import Counter
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
    attrib_pair_re = re.compile(r"(?P<tag>\w+) (?P<text>\{[\.\w\s:;\d\\]+\})")
    attrib_inner_re = re.compile(r"(?P<tag>\w+):(?P<text>[\.\w\s\d\\]+)")
    all_attribs = attrib_pair_re.findall(attrib)
    # counts = Counter([x[0] for x in all_attribs])  # TODO implement checking for multiple attrs in one line
    inner_found = {k:attrib_inner_re.findall(v[1:-1]) for k,v in all_attribs}
    formatted_attributes = {k0: {k1:v1 for k1, v1 in v0} for k0, v0 in inner_found.items()}
    return formatted_attributes


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


def strip_debug_log(filepath):
    with open(filepath) as f:
        lines = f.readlines()
        stripped_lines = [l for l in lines if "DEBUG" in l]
    
    with open(filepath[:-4] + "_stripped.log", "w") as f:
        f.write(stripped_lines)


if __name__ == "__main__":
    attr_str = "readingOrder {index:28;} acknowledgement {offset:0; length:11; continued:true;} person {offset:20; length:6;title:Mr; lastname:Baness;} person {offset:28; length:5;title:Mr; lastname:Horst;} person {offset:38; length:5;title:Mr; lastname:Bolst;} acknowledgement {offset:48; length:11; continued:true;}"
    parse_attributes(attr_str)



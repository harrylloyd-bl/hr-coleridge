from collections import Counter
from itertools import combinations
import re
from xml.etree.ElementTree import Element


def parse_custom_attribute_string(element: Element) -> list[tuple[str, tuple[str, str]]]:
    """
    Parse the custom attributes of an XML element
    Convert the custom string into a list of (Transkribus) tags and tag values

    Args:
        element (Element): _description_

    Returns:
        list[tuple[str, tuple[str, str]]]: _description_
    """
    attributes_raw = element.attrib.get("custom")
    # Handle misformatted Unicode, U+0020 (space), U+0027 (apostrophe)
    attributes = attributes_raw.replace(r"\u0020", " ").replace(r"\u0027", "'")
    attrib_pair_re = re.compile(r"(?P<tag>\w+) (?P<text>\{[\.\w\s:;\d\\'’]+\})")
    attrib_inner_re = re.compile(r"(?P<tag>\w+):(?P<text>[\.\w\s\d\\'’]+)")
    all_attribs = attrib_pair_re.findall(attributes)

    inner_found = [(k, attrib_inner_re.findall(v[1:-1])) for k,v in all_attribs]
    # breakpoint()
    return inner_found


def parse_attributes(region: Element, line_idx: int = None) -> dict[str, dict[str, str]|list[dict[str, str]]]:
    """
    Parse a string of attributes from an xml

    Args:
        attrib (str): A string of attributes from an xml
        region_lines (Element[str]): All lines after the current line in the parent text region (inclusive)

    Returns:
        dict[str, dict[str, str]|list[dict[str, str]]]: A well formatted dictionary of attributes
    """
    if line_idx is None: # Just one line of attributes in a TextRegion, no continuation
        element = region
        inner_found = parse_custom_attribute_string(element)
        formatted_attributes = {k0: {k1:v1 for k1, v1 in v0} for (k0, v0) in inner_found}
        return formatted_attributes
    
    element = region[line_idx]

    if "Coord" in element.tag or "TextEquiv" in element.tag:
        raise ValueError(f"Only TextLines should be passed to parse_attributes, f{element.tag.split("}")[1]} was passed")
    elif element[2][0].text is None:
        return dict()  # No text
    
    inner_found = parse_custom_attribute_string(element)
    
    formatted_attributes = {}
    counts = Counter([x[0] for x in inner_found])  # TODO implement checking for multiple attrs in one line
    multiples = {k:0 for k,v in counts.items() if v > 1}

    attr_dicts = [(attr, {k: v for k,v in vals}) for attr, vals in inner_found]
    unique_attr_dicts = {}
    for attr, vals in attr_dicts:
        if attr in multiples:
            unique_attr_dicts[f"{attr}{multiples[attr]}"] = vals
            multiples[attr] += 1
        else:
            unique_attr_dicts[attr] = vals

    overlaps = [(a, (d.get("offset"), d.get("length"))) for a, d in unique_attr_dicts.items()]
    overlaps = [(a, {x for x in range(int(d[0]), int(d[0]) + int(d[1]) + 1)}) for a, d in overlaps if d[0]]

    sets = combinations(overlaps, r=2)
    grouped_sets = {slice(min(span), max(span)): [] for k,span in overlaps}
    for ((tag1, span1), (tag2, span2)) in sets:
        if span1 & span2:
            grouped_sets[slice(min(span1), max(span1))].extend([tag1, tag2])

    grouped_sets = {k:list(set(v)) for k,v in grouped_sets.items() if v}
    grouping_tags = ["medical", "acknowledgement", "criticism", "role", "Role"]

    for gs in grouped_sets.values():
        de_duped = {de_dupe(tag):tag for tag in gs}  # this won't work for overlaps with multiple of the same tag
        if "person" in de_duped:
            person = unique_attr_dicts[de_duped["person"]]

            if "member" in de_duped:
                person["leader"] = False
            elif "leader" in de_duped:
                person["leader"] = True

            if "ethnicity" in de_duped:
                person["ethnicity"] = "Native"
            elif "ethnic_label" in de_duped:
                person["ethnicity"] = "Native"

            grouped_tags_to_combine = [x for x in grouping_tags if x in de_duped]
            for t in grouped_tags_to_combine:  # based on overlapping_groups.txt
                person[t] = gather_attribute_text(region, line_idx, attr=t, attr_dict=unique_attr_dicts[de_duped[t]])

            for k, v in de_duped.items():
                if k == "person":
                    continue
                else:
                    del unique_attr_dicts[v]
            
            unique_attr_dicts[de_duped["person"]] = person
        
        elif "member" in de_duped:  # There are only member/ethnicity overlaps as per overlapping_groups.txt
            if "ethnicity" in de_duped:
                unique_attr_dicts[de_duped["member"]]["ethnicity"] = "Native"
                del unique_attr_dicts[de_duped["ethnicity"]]


    # breakpoint()
    for attr, attr_dict in unique_attr_dicts.items():
        if attr == "readingOrder":
            continue

        if "offset" in attr_dict:
            attr_text = gather_attribute_text(region=region, line_idx=line_idx, attr=attr, attr_dict=attr_dict)
            # breakpoint()
            if attr_text is None:  # This was text continued from a previous line
                continue            
        
        attr_dict["text"] = attr_text
        output_dict = {attr:attr_dict}
        formatted_attributes |= output_dict
    
    # breakpoint()
    return formatted_attributes


def gather_attribute_text(region: Element, line_idx: int, attr: str, attr_dict: dict[str, str]) -> str:
    """
    Extract text from lines after the line_idx line that have the continued tag and are associated with
    a continued attr tag from the line_idx line

    Args:
        region (Element): The TextRegion the current line is a child of
        line_idx (int): The idx of the current line with region
        attr (str): The attr to search for continued tags of in following lines

    Returns:
        str: A concatenated, new line joined string representing all continued text
    """
    # breakpoint()    
    offset = int(attr_dict["offset"])
    length = int(attr_dict["length"])
    line_length = len(region[line_idx][2][0].text)
    line_attr_text = extract_line_text(line=region[line_idx], attr=attr, attr_dict=attr_dict)

    if "continued" not in attr_dict:
        return line_attr_text

    # two ways of checking if a continued tag refers to the next line or a previous line
    # 1 verify attributes other than offset/length match a previous/succeeding continued tag
    # 2 verify that a succeeding continued tag ends before the end of the next line
    # There is one situation we can't catch without parsing the text
    # acknowledgement tags only contain offset/length, so we can't verify continuation
    # if an acknowledgement tag ends at the end of a line, and there is a continued ack tag on the next line
    # we won't be able to separate them

    elif "continued" in attr_dict:
        
        if line_idx + 1 == len(region):
            # Last line in a region, this is continued line that has been collected earlier
            return None
        
        if offset + length < line_length:
            # This is continued from a previous line
            # will have been picked up by the gather_attribute_text call for that line
            return None

        # acknowledgement has no extra attributes we can exploit to check continuity
        # rely on offset, length alone
        # other tags have attributes we can compare between lines to check continuity

        if attr != "acknowledgement" and line_idx > 0:            
            prev_line_attrs_raw = region[line_idx - 1].attrib.get("custom")
            prev_line_attrs = prev_line_attrs_raw.replace(r"\u0020", " ").replace(r"\u0027", "'")
            
            common_overlap_keys = ["continued", "scale", "member", "leader", "ethnicity"]  # tag attributes that are likely to be the same as the prev line by chance
            # breakpoint()
            if any(v in prev_line_attrs for k, v in attr_dict.items() if k not in common_overlap_keys):
                # Attrs in this line appear verbatim in the last line, so is continued
                # Will have been picked up by the gather_attribute_text call for that line
                return None                    
        
        # breakpoint()
        continued_text = find_continued_text(region=region, line_idx=line_idx, attr=attr)
        line_attr_text += continued_text
        return line_attr_text
    

def extract_line_text(line: Element, attr: str, attr_dict: dict[any, any]):
    """
    Extract text from an Tkb PAGE XML line by getting the offset and length attributes

    Args:
        line (Element): A text line in an xml
        attrib_name (str): The name of an attribute
        attribs (dict[str, str]): A dictionary of attributes containing length and offset

    Returns:
        _type_: _description_
    """
    if "offset" not in attr_dict:
        raise KeyError(f"offset not in attributes for {attr}")
    elif "length" not in attr_dict:
        raise KeyError(f"length not in attributes for {attr}")
    
    offset, length = int(attr_dict.pop("offset")), int(attr_dict.pop("length"))
    return line[2][0].text[offset:offset + length]


def find_continued_text(region: Element, line_idx: int, attr: str) -> str:
    """
    Find text of an attribute continuing from one line to another

    Args:
        region (Element): TextRegion, excluding Coords and TextEquiv lines
        line_idx (int): The current line being parsed in the TextRegion
        attr (str): Name of the continued tag

    Returns:
        str: The text of the tag continued on succeeding lines
    """
    continued_text = "\n"
    
    for i, line in enumerate(region[line_idx + 1:]): # Coords/TextEquiv lines are checked for in parse_attributes()
        # breakpoint()
        line_length = len(line[2][0].text)
        inner_found = parse_custom_attribute_string(line)

        for attr, vals in inner_found:
            attr_dict = {attr: {k: v for k,v in vals}}
            if "continued" not in attr_dict[attr]:
                continue

            length = int(attr_dict[attr]["length"])
            offset = int(attr_dict[attr]["offset"])

            if offset != 0:
                continue

            if attr == attr:
                attr_text = extract_line_text(line=line, attr=attr, attr_dict=attr_dict[attr])
                # breakpoint()
                continued_text += attr_text + "\n"
                if line_idx + i + 2 == len(region):  # End of a region
                    return continued_text.rstrip("\n")
                elif length < line_length:
                    return continued_text.rstrip("\n")
                break
        else:
            return continued_text.rstrip("\n")


def de_dupe(s: str) -> str:
    """
    Remove a trailing digit from a tag
    Trailing digits are used to make it unique within a set

    Args:
        s (str): A string to check for a trailing digit

    Returns:
        str: A string stripped of a trailing digit if present
    """
    try:
        int(s[-1])
        return s[:-1]
    except ValueError:
        return s


def strip_debug_log(filepath):
    with open(filepath) as f:
        lines = f.readlines()
        stripped_lines = [l for l in lines if "DEBUG" in l]
    
    with open(filepath[:-4] + "_stripped.log", "w") as f:
        f.write(stripped_lines)


if __name__ == "__main__":
    attr_str = "readingOrder {index:28;} acknowledgement {offset:0; length:11; continued:true;} person {offset:20; length:6;title:Mr; lastname:Baness;} person {offset:28; length:5;title:Mr; lastname:Horst;} person {offset:38; length:5;title:Mr; lastname:Bolst;} acknowledgement {offset:48; length:11; continued:true;}"
    parse_attributes(attr_str)



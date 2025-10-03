from collections import Counter
import glob
import xml.etree.ElementTree as ET

from coleridge.data.parse_xml import parse_custom_attribute_string

ns = {
    "page": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance"
}

if __name__ == "__main__":

    CLEAN = False

    combined_pages = glob.glob("data/interim/*combined_pages.xml")
    CHECK_TAGS = True
    if CHECK_TAGS:
        
        tags = []
        for p in combined_pages:
            tree = ET.parse(p)
            root = tree.getroot()
            text_regions = [tr for tr in root.iter(f"{{{ns['page']}}}TextRegion")]
            for i, region in enumerate(text_regions):
                for line in region[1:-1]:
                    line_tags = parse_custom_attribute_string(line, normalise_role=True)
                    if line_tags:
                        tags.extend([t[0] for t in line_tags])


        counted_tags = Counter(tags)

        if CLEAN:
            f_path = "data/processed/tag_counts_clean.txt"
        else:
            f_path = "data/processed/tag_counts.txt"

        with open(f_path, "w") as f:
            if CLEAN:
                sorted_counted_tags = sorted([(k,v) for k,v in counted_tags.items() if k!= "readingOrder"], key=lambda x: x[1], reverse=True)
            else:
                sorted_counted_tags = sorted([(k,v) for k,v in counted_tags.items()], key=lambda x: x[1], reverse=True)
            [f.write(f"{tag}: {count}\n") for tag, count in sorted_counted_tags]
        # [logging.info(f"{tag}: {count}") for tag, count in sorted([(k,v) for k,v in counted_tags.items()], key=lambda x: x[1], reverse=True)]
        print(f"Tag total: {sum([c for t,c in sorted_counted_tags])}")

    CHECK_ATTRIBUTES = True
    if CHECK_ATTRIBUTES:

        tag_attributes = {
            "readingOrder": [],
            "place": [],
            "person": [],
            "Role": [],
            "ethnicity": [],
            "acknowledgement": [],
            "survey_area": [],
            "member": [],
            "map": [],
            "medical": [],
            "survey_party": [],
            "role": [],
            "criticism": [],
            "organization": [],
            "military_branch": [],
            "leader": [],
            "ethnic_group": [],
            "abbrev": [],
            "report_number": [],
            "date": [],
            "unclear": [],
            "remuneration": [],
            "medical_label": [],
            "ethnic_label": [],
            "structure": []
        }

        for p in combined_pages:
            tree = ET.parse(p)
            root = tree.getroot()
            text_regions = [tr for tr in root.iter(f"{{{ns['page']}}}TextRegion")]
            for i, region in enumerate(text_regions):

                for line in region[1:-1]:
                    line_tags = parse_custom_attribute_string(line, normalise_role=True)
                    if line_tags:
                        [tag_attributes[tag].extend([a[0] for a in attrs]) for (tag, attrs) in line_tags]
        
        if CLEAN:
            del tag_attributes["readingOrder"]

        if CLEAN:
            f_path = "data/processed/tag_attribute_counts_clean.txt"
        else:
            f_path = "data/processed/tag_attribute_counts.txt"

        with open(f_path, "w") as f:
            
            for tag, attrs in tag_attributes.items():
                counted_attrs = Counter(attrs)
                sorted_counted_tag_attrs = [(attr, count) for attr, count in sorted([(k,v) for k,v in counted_attrs.items()], key=lambda x: x[1], reverse=True)]
                tag_attributes[tag] = sorted_counted_tag_attrs
                if CLEAN:
                    [f.write(f"{tag}: {attr}, {count}\n") for attr, count in sorted_counted_tag_attrs if attr not in ["offset", "length", "continued"]]
                else:
                    [f.write(f"{tag}: {attr}, {count}\n") for attr, count in sorted_counted_tag_attrs]

        if CLEAN:
            print(f"Tag attribute total: {sum([sum([c for a, c in attrs if a not in ["offset", "length", "continued"]]) for _, attrs in tag_attributes.items()])}")
        else:
            print(f"Tag attribute total: {sum([sum([c for _, c in attrs]) for _, attrs in tag_attributes.items()])}")
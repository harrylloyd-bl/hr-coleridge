from collections import Counter
import glob
import xml.etree.ElementTree as ET

from coleridge.data.parse_xml import parse_attributes

ns = {
    "page": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance"
}

if __name__ == "__main__":

    combined_pages = glob.glob("data/interim/*combined_pages.xml")
        
    overlapping_groups = []
    for p in combined_pages:
        tree = ET.parse(p)
        root = tree.getroot()
        text_regions = [tr for tr in root.iter(f"{{{ns['page']}}}TextRegion")]
        for region in text_regions:
            for i, _ in enumerate(region[1:-1]):
                line_overlapping_groups = parse_attributes(region=region[1:-1], line_idx=i)
                if line_overlapping_groups:
                    for group in line_overlapping_groups.values():
                        sorted_de_dupe = []
                        for tag in sorted(group):
                            try:
                                int(tag[-1])
                                sorted_de_dupe.append(tag[:-1])
                            except ValueError:
                                sorted_de_dupe.append(tag)

                        overlapping_groups.append(tuple(sorted_de_dupe))

    overlapping_groups_count = Counter(overlapping_groups)
    sorted_overlap_count = sorted([(k,v) for k,v in overlapping_groups_count.items()], key=lambda x: x[1], reverse=True)
    with open("data/processed/overlapping_groups.txt", "w") as f:
        [f.write(f"{group}: {count}\n") for group, count in sorted_overlap_count]
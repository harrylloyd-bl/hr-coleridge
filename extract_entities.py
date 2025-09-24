import glob
from datetime import datetime
import logging
import os
import xml.etree.ElementTree as ET

import pandas as pd

from coleridge.data.parse_xml import parse_attributes, extract_attribute_text

COMBINE = False

if COMBINE:
    report_date = 1865
    pages = glob.glob(f"data/raw/{report_date}/00*.xml")
    ordered_pages = sorted(pages, key=lambda x: int(x.split("\\")[-1].split("_")[0]))

    trees, roots = [], []
    for p in ordered_pages:
        if 'Table' not in p:
            tree = ET.parse(p)
            root = tree.getroot()

        trees.append(tree)
        roots.append(root)


    combined_root = roots[0]
    combined_tree = trees[0] 

    for root in roots[1:]:
        for child in root:
            combined_root.append(child)



ns = {
    "page": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance"
}



if __name__ == "__main__":

    logging.basicConfig(
        filename=f"logs/{datetime.now().strftime('%y%m%d_%H%M%S')}.log",
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M',
        encoding='utf-8',
        level=logging.INFO)

    combined_pages = glob.glob("data/interim/*combined_pages.xml")
    entity_dfs = []
    for p in combined_pages:
        report_date = int(os.path.basename(p).split("_")[0])
        tree = ET.parse(p)
        root = tree.getroot()
        entities = []

        text_regions = [tr for tr in root.iter(f"{{{ns['page']}}}TextRegion")]
        for i, region in enumerate(text_regions):
            if i >= 2:
                prev1_head = "{type:heading;}" in text_regions[i-1].attrib.get("custom", [])
                prev2_head = "{type:heading;}" in text_regions[i-2].attrib.get("custom", [])
                preceding_heading = prev1_head or prev2_head

            if "{type:heading;}" in region.attrib.get("custom", []):
                logging.info(f"{report_date} heading {i}")
                credit_child = 0
                print({"child_idx": i} | region.attrib)
                survey_party_lines = []
                survey_area_lines = []
                heading_place = ""
                heading_season = ""
                other_heading_place_attribs = {}
                for line in region[1:-1]:
                    if line[2][0].text is None:
                        continue
                    line_attributes = parse_attributes(line.attrib.get("custom", []))
                    # print(line_attributes)
                    # print(line[2][0].text)
                    if "survey_party" in line_attributes:
                        survey_party_lines.append(extract_attribute_text(line, "survey_party", line_attributes)) 
                    if "survey_area" in line_attributes:
                        survey_area_lines.append(extract_attribute_text(line, "survey_area", line_attributes))
                    if "place" in line_attributes:
                        heading_place = extract_attribute_text(line, "place", line_attributes)
                        other_heading_place_attribs = {"heading_" + k:v for k, v in line_attributes["place"].items()}
                    elif "Season" in line[2][0].text:
                        heading_season = line[2][0].text
                heading_survey_party = ", ".join(survey_party_lines)
                heading_survey_area = ", ".join(survey_area_lines)
                # heading.append((region, survey_party))

            elif "{type:credit;}" in region.attrib.get("custom", []) and preceding_heading:
                logging.info(f"{report_date} credit region {i} credit child {credit_child}")
                print({"child_idx": i, "credit_child": credit_child} | region.attrib)
                credit_child += 1

                survey_party = heading_survey_party
                survey_area = heading_survey_area
                place = heading_place
                other_place_attribs = other_heading_place_attribs
                for j, line in enumerate(region[1:-1]):  # TODO add 'continued logic'
                    entity = {}
                    line_attributes = parse_attributes(line.attrib.get("custom", []))
                    # print(line_attributes)
                    # print(line[2][0].text)
                    if "survey_party" in line_attributes:
                        survey_party = extract_attribute_text(line, "survey_party", line_attributes)

                    if "survey_area" in line_attributes:
                        survey_area = extract_attribute_text(line, "survey_area", line_attributes)

                    if "place" in line_attributes:
                        place = extract_attribute_text(line, "place", line_attributes)
                        other_place_attribs = line_attributes["place"]

                    if "person" in line_attributes:
                        person = extract_attribute_text(line, "person", line_attributes)
                        entity |= line_attributes["person"]  # Any remaining person attribs
                        entity["person"] = person

                    elif "member" in line_attributes:
                        entity["person"] = extract_attribute_text(line, "member", line_attributes)
                
                    if "leader" in line_attributes:
                        entity["leader"] = True
                        entity["person"] = extract_attribute_text(line, "leader", line_attributes)

                    if not entity:  # Handle case when other attributes exist but person|member|leader do not
                        continue
                    
                    entity["report_date"] = report_date
                    entity["heading_survey_area"] = heading_survey_area.strip(",")
                    entity["heading_survey_party"] = heading_survey_party.strip('"')
                    entity["season"] = heading_season.strip("Season ").strip(".")
                    entity["heading_place"] = heading_place
                    entity |= other_heading_place_attribs

                    entity["survey_party"] = survey_party
                    entity["survey_area"] = survey_area

                    entity["place"] = place
                    entity |= other_place_attribs  # Any remaining place attribs

                    if "medical" in line_attributes:
                        entity["medical"] = extract_attribute_text(line, "medical", line_attributes)

                    # if "acknowledgement" in line_attributes:
                    #     entity["acknowledgement"] = extract_attribute_text(line, "acknowledgement", line_attributes)

                    # if "criticism" in line_attributes:
                    #     entity["criticism"] = extract_attribute_text(line, "criticism", line_attributes)
                    
                    if "military_branch" in line_attributes:
                        entity["military_branch"] = extract_attribute_text(line, "military_branch", line_attributes)

                    if "ethnicity" in line_attributes:
                        ethnicity = extract_attribute_text(line, "ethnicity", line_attributes)
                        entity["ethnicity"] = "Native"
                        entity["ethnicity_text"] = ethnicity

                    if "role" in line_attributes:
                        role = extract_attribute_text(line, "role", line_attributes)
                        entity["role"] = role

                    entities.append(entity)

            elif "{type:credit;}" in region.attrib.get("custom", []):
                print(f"Skipping credit {credit_child} as not immediately succeeding a heading tag")
                logging.info(f"{report_date} skipped credit region {i} credit child {credit_child} as not immediately succeeding a heading tag")
                credit_child += 1
                                

        logging.info(f"{report_date} {len(entities)} entities")
        if not entities:
            continue

        entity_df = pd.DataFrame(entities)
        # entity_df.info()

        # print(entity_df.head())
        entity_dfs.append(entity_df)
    
    combined_entities = pd.concat(entity_dfs)
    combined_entities_ordered = combined_entities[
        [
            "title", "firstname", "lastname", "person", "report_date", "leader", "role", "heading_survey_area", "heading_survey_party", "heading_placeName", "heading_wikiData", "season", "heading_place",
            "survey_party", "survey_area", "place", "military_branch", "ethnicity", "ethnicity_text", "dateOfDeath", "medical", "wikiData", "placeName",  "continued"
        ]
    ]
    
    missing_cols = combined_entities.columns.difference(combined_entities_ordered.columns)

    if not missing_cols.empty:
        print(f"{missing_cols} not ordered in output")

    # Handle misformatted Unicode, U+0020 (space), U+0027 (apostrophe)
    combined_entities_ordered["title"] = combined_entities_ordered["title"].str.replace(r"\u0020", " ")
    combined_entities_ordered["firstname"] = combined_entities_ordered["firstname"].str.replace(r"\u0020", " ")
    combined_entities_ordered["firstname"] = combined_entities_ordered["firstname"].str.replace(r"\u0027", "'")
    combined_entities_ordered["lastname"] = combined_entities_ordered["lastname"].str.replace(r"\u0020", " ")
    combined_entities_ordered["lastname"] = combined_entities_ordered["lastname"].str.replace(r"\u0027", "'")
    combined_entities_ordered["heading_placeName"] = combined_entities_ordered["heading_placeName"].str.replace(r"\u0020", " ")
    combined_entities_ordered["placeName"] = combined_entities_ordered["placeName"].str.replace(r"\u0020", " ")

    combined_entities_ordered.to_csv("data/processed/combined_entities.csv", encoding="utf8")
    combined_entities_ordered.groupby(by="report_date").count().apply(lambda x: logging.info(f"{int(x.name)} {x['person']} entities"), axis=1)
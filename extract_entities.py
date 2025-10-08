from collections import Counter
from datetime import datetime
import glob
import logging
import os
import xml.etree.ElementTree as ET

import pandas as pd

from coleridge.data.parse_xml import parse_attributes, de_dupe, extract_entities

ns = {
    "page": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance"
}


if __name__ == "__main__":

    logging.basicConfig(
        filename=f"logs/{datetime.now().strftime('%y%m%d_%H%M%S')}_entities.log",
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
        multi_entities = []

        text_regions = [tr for tr in root.iter(f"{{{ns['page']}}}TextRegion")]

        report_text = ""
        for region in text_regions:
            for line in region[1:-1]:
                if line[2][0].text:
                    report_text += line[2][0].text + " "

        for i, region in enumerate(text_regions):
            if i >= 2:
                prev1_head = "{type:heading;}" in text_regions[i-1].attrib.get("custom", [])
                prev2_head = "{type:heading;}" in text_regions[i-2].attrib.get("custom", [])
                preceding_heading = prev1_head or prev2_head

            if "{type:heading;}" in region.attrib.get("custom", []):
                logging.info(f"{report_date} heading {i}")
                credit_child = 0
                print({"child_idx": i} | region.attrib)

                heading_survey_parties = []
                heading_survey_areas = []
                heading_place_texts = []
                heading_place_names = []
                heading_place_wikidata_ids = []
                heading_place_countries = []
                heading_season = ""
                other_heading_place_attribs = {}

                for j, line in enumerate(region[1:-1]):
                    if line[2][0].text is None:
                        continue
                    line_attributes = parse_attributes(region=region[1:-1], line_idx=j)

                    if "survey_party" in line_attributes:
                        heading_survey_parties.append(line_attributes["survey_party"]["text"])
                    if "survey_area" in line_attributes:
                        heading_survey_areas.append(line_attributes["survey_area"]["text"])

                    for attr, val in line_attributes.items():
                        if de_dupe(attr) == "place":
                            heading_place_texts.append(val.get("text"))
                            heading_place_names.append(val.get("placeName", ""))
                            heading_place_wikidata_ids.append(val.get("wikiData", ""))
                            heading_place_countries.append(val.get("country", ""))

                    if "Season" in line[2][0].text:
                        heading_season = line[2][0].text

                heading_survey_parties = ", ".join(heading_survey_parties)
                heading_survey_areas = ", ".join(heading_survey_areas)
                heading_place_texts = ", ".join(heading_place_texts)
                heading_place_names = ", ".join(heading_place_names)
                heading_place_wikidata_ids = ", ".join(heading_place_wikidata_ids)
                heading_place_countries = ", ".join(heading_place_countries)
                
                heading_attribs = {
                    "report_date": report_date,
                    "heading_survey_area": heading_survey_areas.strip(","),
                    "heading_survey_party": heading_survey_parties.strip('"'),
                    "season": heading_season.strip("Season ").strip("."),
                    "heading_places": heading_place_names,
                    "heading_place_names": heading_place_names,
                    "heading_place_wikidata_ids": heading_place_wikidata_ids,
                    "heading_place_countries": heading_place_countries,
                }

            elif "{type:credit;}" in region.attrib.get("custom", []) and preceding_heading:
                logging.info(f"{report_date} credit region {i} credit child {credit_child}")
                print({"child_idx": i, "credit_child": credit_child} | region.attrib)
                credit_child += 1

                survey_party = ""
                survey_area = ""
                place = dict()
                other_place_attribs = other_heading_place_attribs
                for j, line in enumerate(region[1:-1]):  # TODO add 'continued logic'
                    line_attributes = parse_attributes(region=region[1:-1], line_idx=j)
                    line_entities = extract_entities(attribs=line_attributes, heading_attribs=heading_attribs)
                    if type(line_entities) is dict:
                        if "lastname" in line_entities:
                            line_entities["frequency"] = report_text.count(line_entities["lastname"])
                        else:
                            line_entities["frequency"] = report_text.count(line_entities["person"])
                        entities.append(line_entities)
                    elif type(line_entities) is list:
                        multi_entities.append(line_entities)


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
            "title", "firstname", "lastname", "person", "report_date", "leader", "frequency", "role_title", "role_text", "role_seniority", "role", "seniority", "ethnicity", "ethnicity_text", "heading_survey_area", "heading_survey_party", "heading_places", "heading_place_names", "heading_place_wikidata_ids", "heading_place_countries", "season",
            "military_branch_text", "organization_text", "organization_wikiData", "dateOfDeath", "medical_label_text", "medical_text", "dateOfDeath", "place_placeName",  "place_text", "place_wikiData", 
        ]
    ]
    # not in single entities: "survey_party", "survey_area"
    missing_cols = combined_entities.columns.difference(combined_entities_ordered.columns)

    if not missing_cols.empty:
        print(f"{missing_cols} not ordered in output")

    combined_entities_ordered.to_csv("data/processed/combined_entities.csv", encoding="utf8")
    combined_entities_ordered.groupby(by="report_date").count().apply(lambda x: logging.info(f"{int(x.name)} {x['person']} entities"), axis=1)

    with open("data/processed/multi_entities.txt", "w") as f:
        for me in multi_entities:
            f.write(", ".join(me))
            f.write("\n")
import glob
from datetime import datetime
import logging
import os
import xml.etree.ElementTree as ET

import pandas as pd

from coleridge.data.parse_xml import parse_attributes, de_dupe


ns = {
    "page": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance"
}


if __name__ == "__main__":

    logging.basicConfig(
        filename=f"logs/{datetime.now().strftime('%y%m%d_%H%M%S')}_places.log",
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M',
        encoding='utf-8',
        level=logging.INFO)

    combined_pages = glob.glob("data/interim/*combined_pages.xml")
    places = []
    for p in combined_pages:

        report_date = int(os.path.basename(p).split("_")[0])
        tree = ET.parse(p, parser=ET.XMLParser(encoding="utf-8"))
        root = tree.getroot()

        text_regions = [region for region in root.iter(f"{{{ns['page']}}}TextRegion")]

        report_text = ""
        for region in text_regions:
            for line in region[1:-1]:
                if line[2][0].text:
                    report_text += line[2][0].text + " "

        report_places = []

        heading_place = ""
        heading_season = ""
        heading_survey_party = ""
        heading_survey_area = ""
        for i, region in enumerate(text_regions):
            region_attributes = parse_attributes(region=region)
            structure = region_attributes.get("structure", {"type": ""}).get("type")

            if structure == "heading":
                
                logging.info(f"{report_date} heading {i}")
                credit_child = 0
                print({"heading_region_idx": i} | region.attrib)
                survey_party_lines = []
                survey_area_lines = []

                heading_place = ""
                heading_season = ""
                heading_survey_party = ""
                heading_survey_area = ""

                other_heading_place_attribs = {}
                for i, line in enumerate(region[1:-1]):
                    if line[2][0].text is None:
                        continue
                    line_attributes = parse_attributes(region=region[1:-1], line_idx=i)

                    survey_party_lines.append(line_attributes.get("survey_party", {"text": ""}).get("text"))
                    survey_area_lines.append(line_attributes.get("survey_area", {"text": ""}).get("text"))

                    if "place" in line_attributes:
                        heading_place = line_attributes.get("place")
                        other_heading_place_attribs = {"heading_" + k:v for k, v in line_attributes["place"].items()}
                    elif "Season" in line[2][0].text:
                        heading_season = line[2][0].text

                survey_party_lines = [l for l in survey_party_lines if l]
                survey_area_lines = [l for l in survey_area_lines if l]
                heading_survey_party = ", ".join(survey_party_lines)
                heading_survey_area = ", ".join(survey_area_lines)

            for i, line in enumerate(region[1:-1]): # First and last elements are Coords and TextEquiv, which we ignore
                line_attributes = parse_attributes(region=region[1:-1], line_idx=i)
                for k, v in line_attributes.items():
                    if "place" in de_dupe(k):
                        print({"place_idx": i} | region.attrib)
                        place = line_attributes[k]
                        place["report_date"] = report_date
                        place["heading_survey_area"] = heading_survey_area.strip(",")
                        place["heading_survey_party"] = heading_survey_party.strip('"')
                        place["structure"] = structure
                        place["text_lb"] = place["text"]
                        place["text"] = place["text"].replace("\n", " ")
                        place["frequency"] = report_text.count(place["text"])
                        report_places.append(place)           

        places.extend(report_places)
    places_df = pd.DataFrame(places)
    places_df = places_df.drop_duplicates(subset=["heading_survey_area", "heading_survey_party", "report_date", "text", "frequency"]).reset_index()
    ordered_places_df = places_df[
        [
            "heading_survey_area","heading_survey_party","report_date",
            "text", "frequency", "text_lb", "placeName", "wikiData", "country", "structure", "continued"
        ]
    ]
    
    ordered_places_df.to_csv("data/processed/report_places.csv", encoding="utf-8-sig")

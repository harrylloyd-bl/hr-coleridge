import pytest
import xml.etree.ElementTree as ET

from coleridge.data.parse_xml import parse_attributes, extract_entities


@pytest.fixture
def root():
    tree = ET.parse("tests/test_parse_attributes.xml")
    root = tree.getroot()
    return root


@pytest.fixture
def entity_region_lines():
    tree = ET.parse("tests/test_extract_entities.xml")
    root = tree.getroot()
    entities_region = root[1][2]
    line_attributes = [parse_attributes(entities_region[1:-1], line_idx=i) for i, _ in enumerate(entities_region[1:-1])]
    # breakpoint()
    return line_attributes


# @pytest.fixture
# def scratch_root():
#     tree = ET.parse("tests/scratch.xml")
#     root = tree.getroot()
#     return root


# def test_scratch(scratch_root):
#     scratch_region = scratch_root[1][1][1:-1]
#     idx = 0
#     assert parse_attributes(scratch_region, line_idx=idx) == {
#         "person": {},
#         "role": {}
#     }


def test_parse_attributes(root):
    basic_region = root[1][1]
    assert parse_attributes(basic_region) == {"readingOrder": {"index": "7"}}

def test_continued(root):
    basic_region = root[1][1]
    map_line_idx = 2
    assert parse_attributes(basic_region, line_idx=map_line_idx) == {
        "map": {
            "continued": "true",
            "text": "Degree Sheet No. 1.—Parts of Gwalior, Dholpore and Dattiah States. Scale\nmile = 1 inch.",
            "title": "Degree Sheet No. 1.",
            "scale": "1 inch to 1 mile"
        }
    }

def test_post_continued(root):
    basic_region = root[1][1]
    continued_line_idx = 3
    assert parse_attributes(basic_region, line_idx=continued_line_idx) == dict()


def test_map_continued(root):
    basic_region = root[1][1]
    map_continued_idx = 4
    assert parse_attributes(basic_region, line_idx=map_continued_idx) == {
        "map": {
            "continued": "true",
            "text": "Sheet No. 50 of\nthe Indian Atlas",
            "title": "Sheet No. 50 of the Indian Atlas"
        }
    }

def test_two_map(root):
    basic_region = root[1][1]
    two_map_continued_idx = 5
    assert parse_attributes(basic_region, line_idx=two_map_continued_idx) == {
        "map1": {
            "text": "Sheet No. 51",
            "title": "Sheet No. 51 of the Indian Atlas"
        }
    }

def test_generic_continued(root):
    basic_region = root[1][1]
    generic_continued_idx = 6
    assert parse_attributes(basic_region, line_idx=generic_continued_idx) == {
        "person": {
            "text": "Captain A. B. Melville",
            "firstname": "A. B.",
            "title": "Captain",
            "lastname": "Melville"
        },
        "role": {
            "text": "Assistant Surveyor",
            "title": "Assistant Surveyor"
        },
        "survey_area": {
            "continued": "true",
            "text": "Kashmir\nSurvey",
        }
    }

def test_generic_post_continued(root):
    basic_region = root[1][1]
    generic_post_continued_idx = 7
    assert parse_attributes(basic_region, line_idx=generic_post_continued_idx) == {
        "person": {
            "text": "Lieutenant Colonel Robinson",
            "title": "Lieutenant Colonel",
            "lastname": "Robinson"
        }
    }

def test_multiple_person_combining(root):
    basic_region = root[1][1]
    multiple_person_combining_idx = 8
    assert parse_attributes(basic_region, line_idx=multiple_person_combining_idx) == {
        "role": {
            "text": "Native Surveyors",
            "title": "Native Surveyors"
        },
        "ethnicity0": {
            "text": "Native"
        },
        "person0": {
            "text": "Prem Raj",
            "lastname": "Prem Raj",
            "leader": False,
            "ethnicity": "Native"
        },
        "person1": {
            "continued": "true",
            "text": "Ali\nAhmed",
            "lastname": "Ali Ahmed",
            "leader": False,
            "ethnicity": "Native"
        }
    }


def test_multiple_person_combining_succeeding_line(root):
    basic_region = root[1][1]
    idx = 9
    assert parse_attributes(basic_region, line_idx=idx) == {}


def test_generic_multiple(root):
    basic_region = root[1][1]
    idx = 10
    assert parse_attributes(basic_region, line_idx=idx) == {
        "place0": {
            "text": "Scindhia’s Territory",
            "placeName": "Scindhia’s Territory"
        },
        "place1": {
            "text": "Kerowlee",
            "placeName": "Kerowlee"
        }
    }


def test_subset_overlap(root):
    basic_region = root[1][1]
    idx = 11
    assert parse_attributes(basic_region, line_idx=idx) == {
        "person0": {
            "text": "Ramloosain",
            "lastname": "Ramloosain",
            "role": "Surveyors\xa0",
            "title": "Native Surveyor",
            "ethnicity": "Native"
        },
        "person1": {
            "text": "Gour Chundra",
            "lastname": "Gour Chundra",
            "ethnicity": "Native"
        },
        "person2": {
            "text": "Moung-gyweng",
            "lastname": "Moung-gyweng",
            "ethnicity": "Native"
        },
        "person3": {
            "text": "Shuay-leng",
            "lastname": "Shuay-leng",
            "ethnicity": "Native"
        },
        "person4": {
            "text": "Kyanzan",
            "lastname": "Kyanzan",
            "ethnicity": "Native"
        }
    }


def test_extended_map_continue(root):
    basic_region = root[1][1]
    idx = 12
    assert parse_attributes(basic_region, line_idx=idx) == {
        "map": {
            "continued": "true",
            "text": "maps\nof Teiks have been made on the scale of 4 inches to the\nmile",
            "title": "Maps of Circles",
            "scale": "one inch scale"
        }
    }


def test_rare_characters(root):
    basic_region = root[1][1]
    idx = 16
    assert parse_attributes(basic_region, line_idx=idx) == {
        "person": {
            "firstname": "J.",
            "title": "Esquire",
            "dateOfDeath": "25/03/1869",
            "lastname": "Mulheran'’-",
            "text": "J. Mulheran, Esq.",
            "leader": True
        },
        "role": {
            "seniority": "2nd grade",
            "title": "Deputy Superintendent",
            "text": "Depy. Supdt., 2nd grade"
        }
    }



def test_penultimate_textline_continue(root):
    basic_region = root[1][1]
    idx = len(basic_region) - 2
    assert parse_attributes(basic_region, line_idx=idx) == {
        "medical": {
            "continued": "true",
            "text": "he suffered so much from the exposure, that ever since his health has been in a very bad\nstate."
        }
    }




def test_final_textline_continue(root):
    basic_region = root[1][1]
    idx = len(basic_region) - 1
    assert parse_attributes(basic_region, line_idx=idx) == {}


def test_extract_one_person(entity_region_lines):
    entity = extract_entities(entity_region_lines[0])
    assert entity == {
        "person": "James Mulheran, Esquire",
        "firstname": "James",
        "title": "Esquire",
        "lastname": "Mulheran",
        "leader": True,
        "role_continued": "true",
        "role_text": "Executive\nOfficer in charge",
        "role_title": "Sub- Assistant",
        "role_seniority": "1st Class"
    }


def test_extract_one_member(entity_region_lines):
    entity = extract_entities(entity_region_lines[2])
    assert entity == {
        "person": "Mr. Andrew Chamarett",
        "firstname": "Andrew",
        "title": "Mr.",
        "lastname": "Chamarett",
        "leader": False,
        "role_continued": "true",
        "role_text": "2nd Civil\nAssistant",
        "role_title": "Sub- Assistant",
        "role_seniority": "1st Class"
    }


def test_no_entities(entity_region_lines):
    entity = extract_entities(entity_region_lines[4])
    assert entity is None


def test_ethnicity(entity_region_lines):
    entity = extract_entities(entity_region_lines[5])
    assert entity == {
        "person": "Ramchunder.",
        "lastname": "Ramchunder",
        "leader": False,
        "ethnicity": "Native"
    }
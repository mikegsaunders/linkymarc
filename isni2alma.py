import os
import pymarc
import requests
import xml.etree.ElementTree as ET
from io import StringIO

# variables
apiKey = os.environ.get("ALMA_API_SANDBOX")
headers = {"Accept": "application/xml"}


tree = ET.parse("isni_wiki_v4_qa_test_alma_update.xml")
root = tree.getroot()

for child in root:
    if child.tag == "record":
        for subchild in child:
            if subchild.tag == "controlfield":
                if subchild.attrib["tag"] == "001":
                    mmsID = subchild.text.strip()

                    # get alma rec from api
                    url = f"https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/{mmsID}?apikey={apiKey}"
                    r = requests.get(url, headers=headers)
                    if r.status_code == 200:
                        xml_content = r.content.decode("utf-8")
                        xml_file_like = StringIO(xml_content)
                        records = pymarc.parse_xml_to_array(xml_file_like)

                        isni = "shisni"
                        for record in records:
                            linky_isni = record.get("100").get("1")
                            if linky_isni is None:
                                record.add_ordered_field(
                                    subfields=[pymarc.Subfield(code="1", value=isni)],
                                )
                                print(record["100"])

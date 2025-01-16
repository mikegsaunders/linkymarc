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
                    # probably a better way to do this bit:
                    # if subchild.tag == "datafield":
                    #     if subchild.attrib["tag"] == "100":
                    #     etc

                    # get alma rec from api
                    url = f"https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/{mmsID}?apikey={apiKey}"
                    r = requests.get(url, headers=headers)
                    if r.status_code == 200:
                        xml_content = r.content.decode("utf-8")
                        xml_file_like = StringIO(xml_content)
                        records = pymarc.parse_xml_to_array(xml_file_like)
                        for record in records:
                            field100 = record.get("100")
                            isni = "shisni"
                            wiki = "shiski"
                            field100_1 = field100.get_subfields("1")
                            if "isni" not in field100_1:
                                field100.addsubfield("1", isni)
                            if "wiki" not in field100_1:
                                field100.addsubfield("1", wiki)
                            print(record["100"])

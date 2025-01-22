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
        mmsID = child.find("controlfield[@tag='001']").text.strip()
        LODs = child.findall("datafield[@tag='100']/subfield[@code='1']")
        if child.find("datafield[@tag='100']/subfield[@code='z']") is not None:
            qa = child.find("datafield[@tag='100']/subfield[@code='z']").text.strip()
        else:
            qa = ""
        isni = ""
        wiki = ""
        for each in LODs:
            if "isni" in each.text.strip():
                isni = each.text.strip()
            if "wiki" in each.text.strip():
                wiki = each.text.strip()
        # print(mmsID, isni, wiki, LOD_source)
        # get alma rec from api
        url = f"https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/{mmsID}?apikey={apiKey}"
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            # parse xml to pymarc
            xml_content = r.content.decode("utf-8")
            xml_file_like = StringIO(xml_content)
            records = pymarc.parse_xml_to_array(xml_file_like)

            # add in linked open data fields
            for record in records:
                field100 = record.get("100")
                field100_1 = field100.get_subfields("1")
                if not any("isni" in subfield for subfield in field100_1):
                    if isni != "":
                        field100.add_subfield("1", isni)
                    if qa != "":
                        field100.add_subfield("z", qa)
                else:
                    field100.add_subfield("z", "ISNIQAPASS_HUMAN")
                if not any("wiki" in subfield for subfield in field100_1):
                    if wiki != "":
                        field100.add_subfield("1", wiki)

                # convert back to xml
                xml = pymarc.record_to_xml(record)
                # add bib wrapper
                xml_element = ET.fromstring(xml)
                bib_element = ET.Element("bib")
                bib_element.append(xml_element)
                xml_with_bib = ET.tostring(bib_element, encoding="utf-8")
                print(xml_with_bib)
                # send to alma
                # r = requests.put(url, data=xml, headers=headers)

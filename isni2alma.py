import os
import pymarc
import requests
import xml.etree.ElementTree as ET
from io import StringIO

# variables
apiKey = os.environ.get("ALMA_API_SANDBOX")
headers = {"Accept": "application/xml", "Content-Type": "application/xml"}

# counters
total = 0
progress = 0
existing_isni = 0
no_LOD = 0


tree = ET.parse("isni_wiki_v4_qa_test_alma_update.xml")
root = tree.getroot()
total = len(root)

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
        # skip if nothing new to add
        if isni == "" and qa == "":
            progress += 1
            no_LOD += 1
            continue
        # get alma rec from api
        url = f"https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/{mmsID}?apikey={apiKey}"
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            print(r.text)
        if r.status_code == 200:
            # parse xml to pymarc
            xml_content = r.content.decode("utf-8")
            xml_file_like = StringIO(xml_content)
            records = pymarc.parse_xml_to_array(xml_file_like)

            # add in linked open data fields
            for record in records:
                field100 = record.get("100")
                field100_1 = field100.get_subfields("1")
                field100_z = field100.get_subfields("z")
                if not any("isni" in subfield for subfield in field100_1):
                    if isni != "":
                        field100.add_subfield("1", isni)
                    if qa != "":
                        field100.add_subfield("z", qa)
                else:
                    existing_isni += 1
                    if len(field100_z) == 0:
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
                # send to alma
                r = requests.put(url, data=xml_with_bib, headers=headers)
                progress += 1
                if r.status_code != 200:
                    print(r.text)
    print(
        f"\rProgress: {progress}/{total} records, {existing_isni} recs with existing ISNI, {no_LOD} recs with no linked data",
        end="",
    )
total_skipped = existing_isni + no_LOD
updated_records = progress - total_skipped
print(f"\n{updated_records} records updated with linked data")

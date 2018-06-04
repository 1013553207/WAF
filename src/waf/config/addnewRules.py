import xml.etree.ElementTree as ET
tree = ET.parse("rules.xml")
root = tree.getroot()
rid = 3000

for child in root:
    if child.attrib['attr'] == 'args':
        with open('sqli.txt') as fd:
            for line in fd:
                a = ET.Element("rule")
                a.attrib['action'] = str(1)
                a.attrib['id'] = str(rid)
                a.attrib['method'] = '*'
                a.attrib['rtype'] = 'xss'
                a.text = line
                rid += 1
                child.append(a)
#tree = ET.ElementTree(a)
tree.write('new_rules.xml', encoding='utf-8')
#tree.write('new_rules.xml')
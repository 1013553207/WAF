# -*- coding: utf-8 -*-
from xml.dom.minidom import parse

def parseRules(rulefiles):
    DOMTree = parse(rulefiles)
    collection = DOMTree.documentElement
    fieldNodes = collection.getElementsByTagName("field")
    result = {}
    for fieldNode in fieldNodes:
        field = fieldNode.getAttribute('attr')
        phase = int(fieldNode.getAttribute('phase'))
        ruleNodes = fieldNode.getElementsByTagName('rule')
        result[(field, phase)] = {
                        ruleNode.getAttribute('id'):
                            (int(ruleNode.getAttribute('id')),
                            ruleNode.getAttribute('method'),
                            ruleNode.childNodes[0].data,
                            int(ruleNode.getAttribute('action'))) for ruleNode in ruleNodes }
    return result


if __name__ == '__main__':
    print(parseRules(r'C:\\Users\\DIY\\Desktop\\WAF\\src\\waf\\config\\rules.xml'))
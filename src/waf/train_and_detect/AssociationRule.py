# -*- coding: utf-8 -*-

import pyfpgrowth


def AssociationRule(ip_urls, support, minConf):
    ips = set([items[0] for items in ip_urls])
    url_paths = set([items[1] for items in ip_urls])
    ips_map = {ip: -i-1 for i, ip in enumerate(ips)}
    urls_map = {ulrpath: i+1 for i, ulrpath in enumerate(url_paths)}
    transactions = [[ips_map.get(items[0]), url_paths.get(items[1])] for items in ip_urls]
    patterns = pyfpgrowth.find_frequent_patterns(transactions, support)
    rules = pyfpgrowth.generate_association_rules(patterns, minConf)
    ip = []
    url = []
    for (i,) in rules.keys():
         if i < 0:
             ip.append(i)
         else:
             url.append(i)




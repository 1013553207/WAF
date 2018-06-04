# -*- coding: utf-8 -*-
import os
import re
import random
import xml.dom.minidom
from datetime import datetime

import mysql.connector

config = {
    'host': '10.200.200.200',
    'user': 'root',
    'password': '535574',
    'port': 3306,
    'database': 'waflog',
    'charset': 'utf8'
}
cnn = None
try:
    cnn = mysql.connector.connect(**config)
except mysql.connector.Error as e:
    print('connect fails!{}'.format(e))

cursor = cnn.cursor()
try:
    sql_query = 'delete from rules;'
    cursor.execute(sql_query)
except mysql.connector.Error as e:
    print('query error!{}'.format(e))
finally:
    cnn.commit()
    cursor.close()

cursor = cnn.cursor()
#在内存中创建一个空的文档
doc = xml.dom.minidom.Document()
#创建一个根节点Managers对象
root = doc.createElement('rules')
#设置根节点的属性
root.setAttribute('desc', 'rule set')
# root.setAttribute('', '科技软件园')
#将根节点添加到文档对象中

index = 1
BasePath = r'C:\Users\DIY\Desktop\WAF\rules'
fields = [('args', 1), ('cookie', 1), ('requestbody', 1), ('responsebody', 2), ('user_agent', 1), ('url', 2)]
for file, phase in fields:
      nodefield = doc.createElement('field')
      nodefield.setAttribute('attr',  file)
      nodefield.setAttribute('phase', str(phase))
      with open(os.path.join(BasePath, file), 'r') as fd:
          for line in fd:
                line = line.strip()
                if re.match(line, '^(\s*)'):
                    continue
                if '#' in line:
                    comNode = doc.createComment(line)
                    nodefield.appendChild(comNode)
                    continue
                ruleNode = doc.createElement('rule')
                ruleNode.setAttribute('rtype', 'xss')
                ruleNode.setAttribute('action',  '1')
                ruleNode.setAttribute('method', '*')
                ruleNode.setAttribute('id', str(index))
                sql = '''insert into `rules`(`rid`, `create_time`, `rtype`, `action`, `method`, `pattern`)
                        value("%d", "%s", "%s", "%d", "%s", "%s")''' % (index,
                                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                                        random.choice(['sql注入', 'xss', 'csrf', 'os command注入', '信息泄露', '协议校验']), #ruleNode.getAttribute('rtype'),
                                                                        1,
                                                                        '*',
                                                                        line.strip())
                cursor.execute(sql)
                index += 1
                #给叶子节点name设置一个文本节点，用于显示文本内容
                ruleNode.appendChild(doc.createTextNode(str(line.strip())))
                nodefield.appendChild(ruleNode)
      root.appendChild(nodefield)
doc.appendChild(root)
with open(r'C:\Users\DIY\Desktop\WAF\src\waf\config\rules.xml', 'w') as fp:
    doc.writexml(fp, indent='\t', addindent='\t', newl='\n', encoding="utf-8")
cursor.close()
cnn.commit()
cnn.close()
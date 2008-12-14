#!/usr/bin/python
import os
import sys
sys.path.append(os.path.join(os.path.dirname(sys.argv[0]),"..", "src"))
import Ansi

input = open(sys.argv[1],'r')
content = input.read()
ansiText = Ansi.AnsiText(content)
print ansiText.render()
#print parsed

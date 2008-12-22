#!/usr/bin/python

import sys
import re
import xmpp.simplexml
import logging

ESC_TO_COLOR = {
    '30m' : 'black',
    '31m' : 'red',
    '32m' : 'green',
    '33m' : 'yellow',
    '34m' : 'blue',
    '35m' : 'magenta',
    '36m' : 'cyan',
    '37m' : 'white',
    '38m' : 'black',
}

class DataType:
    TEXT=1
    COLOR=2
    CONTROL=3

class RenderType:
    TEXT=1
    HTML=2

class AnsiText:
    def __init__(self, text):
        self._parsedData = self.concatText(self.parseString(text))
        self._colorMap = {}
    
    def setColorMap(self, colorMap):
        self._colorMap = colorMap

    def parseESCSeq(self,chars):
        char = chars.pop()
        if char == '[' and len(chars) > 0:
            content = ''
            char = chars.pop()
            content += char
            while len(chars) > 0 and not re.match("[a-zA-Z]",char):
                char = chars.pop()
                content += char
            #print "\nParsed: %s" % content
            return (DataType.COLOR, content)
        else:
            logging.warn("Invalid ESC Sequence - at least for me")
            return (DataType.TEXT, '')

    def parseString(self,txt):
        chars = []
        for char in txt:
            chars.append(char)
        chars.reverse()
        parsedText = []
        while len(chars) > 0:
            char = chars.pop()
            if char == chr(27) and len(chars) > 0:
                element = self.parseESCSeq(chars)
            elif char == '\n' or char == '\r':
                element = (DataType.CONTROL,char)
            elif char < chr(32) or char > chr(126):
                element = (DataType.CONTROL, char)
            else:
                element = (DataType.TEXT,char)
            parsedText.append(element)
        return parsedText

    def concatText(self,parsedText):
        txt = ''
        parsedResult = []
        for item in parsedText:
            (type,value) = item
            if type == DataType.TEXT:
                txt += value
            else:
                if len(txt) > 0:
                    parsedResult.append((DataType.TEXT, txt))
                    txt = ''
                parsedResult.append(item)
        if len(txt) > 0:
            parsedResult.append((DataType.TEXT, txt))
        return parsedResult

    def render(self, type=RenderType.HTML):
        return self.renderHTML(self._parsedData)

    def renderHTML(self,parsedText):
        txt = ''
        tagStack = []
        for element in parsedText:
            (type,value) = element
            if type == DataType.CONTROL:
                if value == '\n':
                    txt += '<br/>'
                else:
                    #txt += "<!-- Terminal CONTROL Data -->" 
                    logging.info("Terminal Control data")
            elif type == DataType.COLOR:
                if ESC_TO_COLOR.has_key(value):
                    color = ESC_TO_COLOR[value]
                    if self._colorMap.has_key(color):
                        color = self._colorMap[color]
                    txt += "<span style=\"color:%s\">" % color
                    tagStack.append('</span>')
                    font = True
                elif value == '1m':
                    txt += "<strong>"
                    tagStack.append('</strong>')
                elif value == '0m':
                    tagStack.reverse()
                    txt += ''.join(tagStack)
                    tagStack = []
                else:
                    logging.warn("Unknown ESC Color Sequence (%s)" % str(value))
                    #txt += "\n<!-- ESC COLOR (%s) not known -->\n" % str(value)
            elif type == DataType.TEXT:
                    txt += xmpp.simplexml.XMLescape(value)
        tagStack.reverse()
        txt += ''.join(tagStack)
        return txt 



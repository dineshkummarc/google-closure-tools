import sys
import os
import fnmatch
import string
import logging
import subprocess
import datetime
from xml.dom import minidom
from Shared import *

def fixSlashes(path):
  return string.replace(path,"\\","/")

def append_analytics_files(source_html, target_html, analytics_files):
  with open(source_html,'r') as input:
    content = input.read()

  partitions = content.partition('</body>')
  
  new_content = [partitions[0]]

  for af in analytics_files:
    with open(af,'r') as file:
      new_content.append(file.read())

  new_content += [partitions[1],partitions[2]]
  
  with open(target_html, 'w') as file:
    file.writelines(new_content)
  
  ensureHtmlElementsFromFile(target_html)

def getScriptElementsFromDom(dom, exclude_http = True):
  # TODO: should really use xpath here, eh?
  html = dom.getElementsByTagName('html')[0]
  head = html.getElementsByTagName('head')[0]
  elements = head.getElementsByTagName('script')
  if(exclude_http):
    return filter(lambda e: e.hasAttribute('src') and not(e.getAttribute('src').startswith("http://")) , elements)
  else:
    return elements

def getCSSElementsFromDom(dom, exclude_http = True):
  # TODO: should really use xpath here, eh?
  html = dom.getElementsByTagName('html')[0]
  head = html.getElementsByTagName('head')[0]
  elements = head.getElementsByTagName('link')
  elements = filter(lambda e: e.hasAttribute('rel') and e.getAttribute('rel') == 'stylesheet', elements)
  if(exclude_http):
    return filter(lambda e: e.hasAttribute('href') and not(e.getAttribute('href').startswith("http://")) , elements)
  else:
    return elements

def replaceJsFiles(source_html_file, target_html_file, compiled_js_file, source_js_files = None):
  compiled_js_file = fixSlashes(compiled_js_file)
  if source_js_files != None:
    source_js_files = map(fixSlashes, source_js_files)
  
  dom = minidom.parse(source_html_file)
  script_elements = getScriptElementsFromDom(dom)
  
  # remove all script references that are compiled
  for element in script_elements:
    process_script_element(element, source_js_files)
  
  compiledElement = dom.createElement('script')
  compiledElement.setAttribute('src', compiled_js_file)
  # needed to ensure xml output writes both open/close tags
  compiledElement.appendChild(dom.createTextNode(''))
  
  head = dom.getElementsByTagName('head')[0]
  head.appendChild(compiledElement)
  
  ensureHtmlElementsFromDom(dom)
  
  writeXmlSansInstructions(dom,target_html_file)

def process_script_element(element, source_js_files = None):
  if(element.hasAttribute('src')):
    src_attribute = element.getAttribute('src')
    if(source_js_files == None or source_js_files.count(src_attribute) > 0):
      toRemove = [element]
      
      # loop through following elements, removing whitespace
      element = element.nextSibling
      while element and element.nodeType == element.TEXT_NODE and len(string.strip(element.data)) == 0:
        toRemove.append(element)
        element = element.nextSibling
      for element in toRemove:
        element.parentNode.removeChild(element)

def ensureHtmlElementsFromFile(path):
  dom = minidom.parse(path)
  ensureHtmlElementsFromDom(dom)
  writeXmlSansInstructions(dom, path)

def ensureHtmlElementsFromDom(dom):
  # now go through all 'important' tags and ensure they are not empty
  for element_name in ['canvas', 'script', 'div', 'a']:
    for element in dom.getElementsByTagName(element_name):
      element.appendChild(dom.createTextNode(''))
  
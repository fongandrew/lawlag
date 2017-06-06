# Makes the meta files used for a Tort Bunnies page.
# This code is public domain.

import yaml
import os
import sys
import datetime
import time
import re
from subprocess import Popen, PIPE

from gen import ROOT_DIR, META_DIR
COMICS_DIR = os.path.join(ROOT_DIR, 'assets', 'comics')

try:
	# Load Inkscape powers
	INKSCAPE_DIR = 'C:\\Program Files (x86)\\Inkscape'
	sys.path.append('C:\\Program Files (x86)\\Inkscape\\share\\extensions')
	import inkex
except ImportError:
	# Portable Inkscape
	INKSCAPE_DIR = 'C:\\Users\\Andrew\\Apps\\InkscapePortable\\App\\Inkscape'
	sys.path.append('C:\\Users\\Andrew\\Apps\\InkscapePortable\\App\\Inkscape\\share\\extensions')
	import inkex

META_TEMPLATE = """globals:
  last: c{num}
includes:
- from: c{num}.png
  to: images/c{num}.png
- from: t{num}.png
  to: images/t{num}.png
pages:
- _id: c{num}
  _path: {num}.html
  _template: page.html
  _post_to_facebook: 1
  prev: c{prev}
  next: c{next}
  datetime: {date}
  src: images/c{num}.png
  thumbnail: images/t{num}.png
  width: {width}
  height: {height}
  name: {name}
  facebook: 1
  description: <<!!Description!!>>
  alt: <<!!alt!!>>
  notes: |
    <p><b><date></b>. <<!!Notes!!>></p>
  transcript: |
{transcript}
revision: {num}
""" # {transcript} not being aligned tab-wise is intentional.

def parse_inkscape_file(number):
    template_vars = {}
    
    template_vars['num'] = int(number)
    template_vars['prev'] = int(number) - 1
    template_vars['next'] = int(number) + 1
    filename = os.path.join(COMICS_DIR, 'c' + number + '.svg')
    e = inkex.Effect()
    e.parse(filename)
    svg = e.document.getroot()
    
    template_vars['width'] = int(svg.get('width'))
    template_vars['height'] = int(svg.get('height'))
    
    # Find title of comic by looking for italics in cites
    italics = svg.xpath("svg:g[@inkscape:label='Cite']//svg:tspan[contains(@style,'italic')]", namespaces=inkex.NSS)
    if italics:
        template_vars['name'] = italics[0].text
    else:
        template_vars['name'] = '<<!!Name!!>>'
    
    # Find date by parsing cite
    date_str = ''; res=None;
    date_re = re.compile(r'\((?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*(?P<day>[0-9]+)\s*,\s*(?P<year>[0-9]+)\)')
    texts = svg.xpath("svg:g[@inkscape:label='Cite']//svg:text", namespaces=inkex.NSS)
    for text in texts:
        for t in text.itertext():
            res = date_re.search(t)
            if res: break;
        if res: break;
    if res:
        res = res.groupdict()
        month = {'Jan':'01',
                 'Feb':'02', 
                 'Mar':'03', 
                 'Apr':'04', 
                 'May':'05',
                 'Jun':'06', 
                 'Jul':'07', 
                 'Aug':'08', 
                 'Sep':'09', 
                 'Oct':'10', 
                 'Nov':'11', 
                 'Dec':'12'}[res['month']]
        day = res['day']
        if len(day) == 1:
            day = '0' + day;
        year = res['year']
        template_vars['date'] = "{year}-{month}-{day}".format(year=year, month=month, day=day)
    else:
        template_vars['date'] = '<<!!Date!!>>'
    template_vars['date'] += ' 05:00:00' #Because we always post at this particular time
    
    # Extract panel data
    panel_data = svg.xpath("svg:g[@inkscape:label='Top-Boxes']/svg:rect", namespaces=inkex.NSS)
    # Order it -- we determine panel order by going left to right, top to bottom
    # We rely on the midpoints of panels (formula doesn't incorporate div / 2
    # since it's comparison). There's a 30 pt buffer for panels that may be on
    # the same horizontal level but are slightly off for whatever reason.
    panels = []
    for panel in panel_data:
        id = panel.get('id')
        print "Querying panel %s" % id
        p = Popen('inkscape --query-x --query-id={id} "{filename}"'.format(
            id=id, filename=filename),
            shell=True, stdout=PIPE, stderr=PIPE, cwd=INKSCAPE_DIR)
        p.wait()
        x = float(p.stdout.read())
        p = Popen('inkscape --query-y --query-id={id} "{filename}"'.format(
            id=id, filename=filename),
            shell=True, stdout=PIPE, stderr=PIPE, cwd=INKSCAPE_DIR)
        p.wait()
        y = float(p.stdout.read())
        # We query x, y using popen b/c of x,y reversal issues with querying
        # vs. directly examining text. No need for h, w though.
        # x = float(panel.get('x'))
        # y = float(panel.get('y'))
        h = float(panel.get('height'))
        w = float(panel.get('width'))
        panels.append((int(y+h) / 30, int(x+w) / 30, x, y, x+w, y+h, panel))
    panels.sort()
    print panels
    
    # Extract text
    dialogue = [[] for p in panels] # Create an empty list for each panel
    texts = svg.xpath("svg:g[@inkscape:label='Text']/svg:text", namespaces=inkex.NSS)
    for text in texts:
        # We have to query Inkscape to get dimensions of text
        # Can't rely on x,y in element (this is baseline, not actual x,y)
        id = text.get('id')
        print "Querying %s" % id
        p = Popen('inkscape --query-x --query-id={id} "{filename}"'.format(
            id=id, filename=filename),
            shell=True, stdout=PIPE, stderr=PIPE, cwd=INKSCAPE_DIR)
        p.wait()
        x = float(p.stdout.read())
        p = Popen('inkscape --query-y --query-id={id} "{filename}"'.format(
            id=id, filename=filename),
            shell=True, stdout=PIPE, stderr=PIPE, cwd=INKSCAPE_DIR)
        p.wait()
        y = float(p.stdout.read())
        p = Popen('inkscape --query-width --query-id={id} "{filename}"'.format(
            id=id, filename=filename),
            shell=True, stdout=PIPE, stderr=PIPE, cwd=INKSCAPE_DIR)
        p.wait()
        w = float(p.stdout.read())
        p = Popen('inkscape --query-height --query-id={id} "{filename}"'.format(
            id=id, filename=filename),
            shell=True, stdout=PIPE, stderr=PIPE, cwd=INKSCAPE_DIR)
        p.wait()
        h = float(p.stdout.read())
        
        # A piece of text is in a panel if its midpoint is inside the panel
        print "Calculating layer"
        mid_x = (2*x + w) / 2
        mid_y = (2*y + h) / 2
        print mid_x, mid_y
        for i,p in enumerate(panels):
            if (mid_x > p[2] and mid_x < p[4] and mid_y > p[3] and mid_y < p[5]):
                dialogue[i].append((int(y)/30, int(x)/30, text)) # /30 is for ordering
                print "Into panel", i
                break
    
    # Order dialogue - same principle as ordering panels
    for i,d in enumerate(dialogue):
        d.sort()
        dialogue[i] = [t[2] for t in d]
    
    # Get text out of elements
    transcript = []
    for panel in dialogue:
        panel_transcript = []
        for text in panel:
            title = text.xpath("svg:title", namespaces=inkex.NSS)
            if title:
                title = title[0]
                speaker = title.text
            else:
                speaker = "<<!!Speaker!!>>"
            # Each tspan represents a line of text
            tspans = text.xpath("svg:tspan", namespaces=inkex.NSS)
            # We use itertext reather than text b/c nested tspans can screw that up.
            lines = [''.join(tspan.itertext()) for tspan in tspans]
            # Figure out spacing to get YAML-like appearance for transcript.
            # We add 4 extra spaces because of the way the template appears.
            speaker = "    " + speaker + ": ";
            shift = ' ' * len(speaker);
            panel_transcript.append(speaker + ("\n" + shift).join(lines) + " ;")
        transcript.append("\n".join(panel_transcript))
    template_vars['transcript'] = "\n    -----\n".join(transcript)
    return template_vars;
    
def write_yaml(number, vars):
    filename = os.path.join(META_DIR, 'c' + number + '.yaml')
    print "Writing %s" % filename
    try:
        f = open(filename, 'a') # Append rather than overwrite to avoid regrets
    except IOError:
        f = open(filename, 'w')
    f.write(META_TEMPLATE.format(**vars))
    f.close()

if __name__ == '__main__':
    try:
        number = raw_input("Which comic number? ")
        write_yaml(number, parse_inkscape_file(number))
    except:
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        traceback.print_tb(exceptionTraceback, limit=100, file=sys.stdout)
        print str(exceptionType), exceptionValue
    finally:
        raw_input("Press enter to quit. ")


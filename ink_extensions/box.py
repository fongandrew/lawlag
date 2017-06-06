# Draws a box around selected object
# This code is public domain.

import os
import sys
from subprocess import Popen, PIPE
from simplestyle import *
import inkex

class BoundingBox(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option('-p', '--padding', action='store', type='string',
            dest='padding', default = '10', help='How many pixels of padding?')
    
    def effect(self):
        padding = int(self.options.padding)
        
        # Get SVG doc + file
        svg = self.document.getroot()
        file = self.args[-1]
        
        # Create a new layer
        layer = inkex.etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), 'Bounding Box Layer')
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        
        # Default style for boxes
        style = {'fill' : '#ffffff', 'stroke' : '#000000', 'stroke-width' : 2}
        
        # Iterate through selection
        for id in self.options.ids:
            node = self.getElementById(id)
            
            #query inkscape about the bounding box of obj
            q = {'x':0,'y':0,'width':0,'height':0}
            for query in q.keys():
                p = Popen('inkscape --query-%s --query-id=%s "%s"' % (query,id,file), shell=True, stdout=PIPE, stderr=PIPE)
                rc = p.wait()
                q[query] = float(p.stdout.read())
                err = p.stderr.read()
            
            rect = inkex.etree.Element(inkex.addNS('rect','svg'))
            rect.set('x', str(q['x'] - padding))
            rect.set('y', str(q['y'] - padding))
            rect.set('width', str(q['width'] + 2 * padding))
            rect.set('height', str(q['height'] + 2 * padding))
            rect.set('style', formatStyle(style))
            layer.append(rect)        

if __name__ == '__main__':
    e = BoundingBox()
    e.affect()
# Syncs to server, for use as cronjob
from gen import ROOT_DIR, REV_DIR, BASE_YAML, get_sync_data, get_base, get_rev_dir, write_sync_data
import os
import yaml
import urllib
import webbrowser
import tempfile
import cgi

# Set up form elements - these will become the input elements in the form
VALUES = {}
ACTION='http://validator.w3.org/feed/check.cgi'
METHOD='post'

# Build input fields
def validate(r):
    data = get_atom(r)
    VALUES['rawdata'] = data
    
    #Set up javascript form submition function. 
    # I am using the 'format' function on a string, and it doesn't like the { and } of the js function
    # so I brought it out to be inserted later
    js_submit = '$(document).ready(function() {$("#form").submit(); });'

    # Set up file content elements
    input_field = '<textarea name="{0}">{1}</textarea>'

    base_file_contents = """
    <script src='http://www.google.com/jsapi'></script>
    <script>
        google.load('jquery', '1.4.2');
    </script>

    <script>
        {0}
    </script>

    <form id='form' action='{1}' method='{2}' />
        {3}
    </form>
    """
    
    input_fields = ""
    for key, value in VALUES.items():
        input_fields += input_field.format(key, cgi.escape(value))
        
    with open('temp_file.html', "w") as f:
        f.write(base_file_contents.format(js_submit, ACTION, METHOD, input_fields))
        f.close()
        webbrowser.open(os.path.abspath(f.name))
        # os.remove(os.path.abspath(f.name))

def get_atom(r):
    fn = os.path.join(get_rev_dir(r), 'atom.xml')
    f = open(fn)
    return f.read()

if __name__ == '__main__':
    import time, sys, traceback, datetime
    base = get_base()
    revisions = base['revisions'].items()
    latest = 0
    for r, dt in revisions: # Get latest revision that has or will deploy soon
        if r > latest: latest = r
    if latest:
        validate(latest)

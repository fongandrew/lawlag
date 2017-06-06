# Reads base.yaml to generate out pages in rev folder
# This code is public domain.

from jinja2 import FileSystemLoader, Environment
from distutils.dir_util import copy_tree
from distutils.file_util import copy_file
import yaml
import os
import datetime
import time

# All other paths interpeted relative to this one
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Misc settings and globals
WWW_DIR = os.path.join(ROOT_DIR, 'www')
REV_DIR = os.path.join(ROOT_DIR, 'rev')
INCLUDE_DIR = os.path.join(ROOT_DIR, 'include')
TEMPLATE_DIR = os.path.join(ROOT_DIR, 'templates')
META_DIR = os.path.join(ROOT_DIR, 'meta')
SYNC_DATA_DIR = os.path.join(ROOT_DIR, 'sync_data')
BASE_YAML = os.path.join(ROOT_DIR, 'base.yaml')
ENV = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

# Actual functions that do work start here
def main(revision, data, base={}):
    sync_data = {}
    globs, includes, pages = extract_data(data, revision)
    base.update(globs)
    globs = base
    
    # Output directory for this revision
    rev_dir = get_rev_dir(revision)
    
    # Copy common assets
    copy_tree(WWW_DIR, rev_dir)
    
    # Handle includes
    for inc in includes:
        from_path, to_path = inc['from'], inc['to']
        from_path = from_path.replace('\\', '/').split('/')
        from_path = os.path.join(INCLUDE_DIR, *from_path)
        to_path = to_path.replace('\\', '/').split('/')
        to_path = os.path.join(rev_dir, *to_path)
        copy_file(from_path, to_path)
            
    # Generate pages 
    for index, page in enumerate(pages):
        print "Starting page ", page['_id']
        context = {'_now' : datetime.datetime.now() }
        context.update(globs)
        context.update(page)
        
        template = ENV.get_template(page['_template'])
        f = open(os.path.join(rev_dir, page['_path']), 'w')
        r = template.render(**context)
        f.write(r.encode('utf-8'))
        f.close()
        
        # Create entry for sync data for FB posts
        p2fb = page.get('_post_to_facebook', None)
        if p2fb and page.get('_new', None):
            if (p2fb == "1" or p2fb == 1): p2fb = ""
            if not sync_data.get('post_to_facebook', []):
                sync_data["post_to_facebook"] = []
            sync_data["post_to_facebook"].append({
                'link' : "http://" + globs["domain"] + "/" + page['_path'],
                'message' : p2fb})
        
    # Create sync data file
    write_sync_data(revision, sync_data)

def write_sync_data(rev, sync_data):
    try:
        os.makedirs(SYNC_DATA_DIR)
    except OSError:
        pass
    sync_data_fn = os.path.join(SYNC_DATA_DIR, str(rev) + ".yaml")
    f = open(sync_data_fn, 'w')
    f.write(yaml.dump(sync_data))
    f.close()

def get_sync_data(rev):
    fn = os.path.join(SYNC_DATA_DIR, str(rev) + '.yaml')
    try:
        f = open(fn, 'r')
        return yaml.load(f.read())
    except IOError:
        return None

def extract_data(data, rev=0):
    """
    Takes a list of revision dicts and extracts globals, includes, and pages
    Expects revision dict to be sorted already
    Returns 3-tuple
    """
    globs = {'_pages' : {}}
    includes = []
    pages = []
    pages_list = []
    for datum in data:
        globs.update(datum.get('globals', {}))
        includes += datum.get('includes', [])
        datum_pages = datum.get('pages', [])
        for page in datum_pages:
            if rev and datum.get('revision', None) == rev:
                page['_new'] = 1
            globs['_pages'][page['_id']] = page
            pages.append(page)
            if page.get('datetime'):
                pages_list.append(page)
    globs['_pages_list'] = pages_list
    return globs, includes, pages

def get_rev_dir(revision):
    "Get the dirname for a revision"
    return os.path.join(REV_DIR, str(revision))

def handle_include(from_path, to_path):
    "Copies file in from_path to to_path"

def get_files():
    "Walks through meta directory, looking for data"
    for dirname, dirpath, filenames in os.walk(META_DIR):
        for filename in filenames:
            if os.path.splitext(filename)[-1] == '.yaml':
                yield os.path.join(dirname, filename)

def get_data():
    "Loads yaml data from meta dir"
    data = []
    for filename in get_files():
        print "Checking %s" % filename
        f = open(filename)
        datum = yaml.load(f.read())
        f.close()
        if datum: data.append(datum)
    data.sort(key=(lambda datum:datum.get('revision')))
    return data

def get_base():
    f = open(BASE_YAML)
    data = yaml.load(f.read())
    f.close()
    return data

if __name__ == '__main__':
    import time, sys, traceback, datetime
    now = datetime.datetime.now()
    try:
        base = get_base()
        data = get_data()
        for r, dt in base['revisions'].items():
            if dt > now:
                print "\nRevision %s" % r
                print "----------------"
                main(r, [d for d in data if (d.get('revision') and d.get('revision') <= r)], base)
    except:
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        traceback.print_tb(exceptionTraceback, limit=100, file=sys.stdout)
        print str(exceptionType), exceptionValue
    finally:
        raw_input("Press enter to quit. ")


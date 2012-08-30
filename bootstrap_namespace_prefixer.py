#!/usr/bin/env python
""" Adds a "tb-" (configurable) prefix to all Twitter Bootstrap CSS code 
@author Francois Aucamp <francois.aucamp@gmail.com>
@license GPLv2+
"""

import sys, re

""" The CSS classname/namespace prefix to prepend to all Bootstrap CSS classes """
CSS_CLASS_PREFIX = 'tb-'

# Note: regex uses semi-Python-specific \n (newline) character
CSS_CLASS_REGEX = re.compile(r'\.([a-zA-Z][a-zA-Z0-9-_]+\w*)(?=[^\{,\n]*[\{,])')
JS_CSS_CLASS_REGEX_TEMPLATE = r"""(?<!(.\.on|\.off))(\(['"][^'"]*\.)(%s)([^'"]*['"]\))"""
JS_JQUERY_REGEX_TEMPLATE = r"""((addClass|removeClass|hasClass|toggleClass)\(['"])(%s)(['"]\))"""
JS_JQUERY_REGEX_TEMPLATE_VAR = r"""((addClass|removeClass|hasClass|toggleClass)\()([a-zA-Z0-9]+)(\))"""
JS_JQUERY_REGEX_TEMPLATE_LIST = r"""((addClass|removeClass|hasClass|toggleClass)\(\[)([^\]]*)(\])"""
# Regex for the conditional/more tricky add/remove/hasClass calls in the bootstrap.js source
JS_JQUERY_CONDITIONAL_REGEX_TEMPLATE = r"""((addClass|removeClass|hasClass|toggleClass)'\]\(['"])(%s)(['"]\))"""
# Regex for certain jquery selectors that might have been missed by the previous regexes
JS_JQUERY_SELECTOR_REGEX_TEMPLATE = r"""(:not\(\.)(%s)(\))"""
JS_INLINE_HTML_REGEX_TEMPLATE = r"""(class="[^"]*)(?<=\s|")(%s)(?=\s|")"""

def processCss(cssFilename):
    """ Adds the CSS_CLASS_PREFIX to each CSS class in the specified CSS file """
    print 'Processing CSS file:', cssFilename
    try:
        f = open(cssFilename)        
    except IOError:
        print ' Failed to open file; skipping:', cssFilename
    else:
        css = f.read()
        f.close()        
        processedFilename = cssFilename[:-4] + '.prefixed.css'
        f = open(processedFilename, 'w')
        f.write(CSS_CLASS_REGEX.sub(r'.%s\1' % CSS_CLASS_PREFIX, css))
        f.close();
        print ' Prefixed CSS file written as:', processedFilename

def collectCssClassnames(cssFilename):
    """ Returns a set of all the CSS class names in the specified CSS file """
    print 'Collecting CSS classnames from file:', cssFilename
    try:
        f = open(cssFilename)        
    except IOError:
        print ' Failed to open file; skipping:', cssFilename
    else:
        css = f.read()
        f.close()
        classes = set(CSS_CLASS_REGEX.findall(css))
        # The "popover-inner" class is referred to in javascript, but not the CSS files - force prefixing for consistency
        classes.add('popover-inner')
        return classes

def processJs(jsFilename, cssClassNames):
    """ Adds the CSS_CLASS_PREFIX to each CSS class in the specified JavaScript file.
    Requires a list of CSS classes (to avoid confusion between custom events and CSS classes, etc)
    """
    print "Processing JavaScript file:", jsFilename
    try:
        f = open(jsFilename)        
    except IOError:
        print ' Failed to open file; skipping:', jsFilename
    else:
        regexClassNamesAlternatives =  '|'.join(cssClassNames)
        js = f.read()
        f.close()        
        jsCssClassRegex = re.compile(JS_CSS_CLASS_REGEX_TEMPLATE % regexClassNamesAlternatives)
        # Replace CSS classes iteratively to ensure all classes are modified (my regex isn't clever enough to do this in one pass only)
        modJs = jsCssClassRegex.sub(r'\2%s\3\4' % CSS_CLASS_PREFIX, js)
        while modJs != js:
            js = modJs
            modJs = jsCssClassRegex.sub(r'\2%s\3\4' % CSS_CLASS_PREFIX, js)            
        js = modJs
        del modJs
        # JQuery has/add/removeClass calls
        jqueryCssClassRegex = re.compile(JS_JQUERY_REGEX_TEMPLATE % regexClassNamesAlternatives)
        js = jqueryCssClassRegex.sub(r'\1%s\3\4' % CSS_CLASS_PREFIX, js)
        jqueryCssClassRegex = re.compile(JS_JQUERY_REGEX_TEMPLATE_VAR)
        js = jqueryCssClassRegex.sub(r"\1'%s'+\3\4" % CSS_CLASS_PREFIX, js)
        # List/array of variables or string literals
        jqueryCssClassRegex = re.compile(JS_JQUERY_REGEX_TEMPLATE_LIST)
        match = jqueryCssClassRegex.search(js)
        while match:
            listStr = match.group(3)
            items = listStr.split(',')
            processed = []
            for rawItem in items:
                item = rawItem.strip()
                if item[0] in ("'", '"'): # string literal
                    item = item[0] + CSS_CLASS_PREFIX + item[1:]
                else: # variable
                    item = "'%s'+%s" % (CSS_CLASS_PREFIX, item)
                processed.append(item)
            newList = ','.join(processed)
            js = js[0:match.start(3)] + newList + js[match.end(3):]
            match = jqueryCssClassRegex.search(js, match.start(3)+len(newList))                                    
        # In-line conditional JQuery has/add/removeClass calls
        jqueryCssClassRegex = re.compile(JS_JQUERY_CONDITIONAL_REGEX_TEMPLATE % regexClassNamesAlternatives)
        js = jqueryCssClassRegex.sub(r'\1%s\3\4' % CSS_CLASS_PREFIX, js)
        # Some sepcific jquery selectors that might have been missed
        jqueryCssClassRegex = re.compile(JS_JQUERY_SELECTOR_REGEX_TEMPLATE % regexClassNamesAlternatives)
        js = jqueryCssClassRegex.sub(r'\1%s\2\3' % CSS_CLASS_PREFIX, js)
        jqueryCssClassRegex = re.compile(JS_INLINE_HTML_REGEX_TEMPLATE % regexClassNamesAlternatives)
        # Replace inline-HTML CSS classes iteratively to ensure all classes are modified (my regex isn't clever enough to do this in one pass only)
        modJs = jqueryCssClassRegex.sub(r'\1%s\2' % CSS_CLASS_PREFIX, js)
        while modJs != js:
            js = modJs
            modJs = jqueryCssClassRegex.sub(r'\1%s\2' % CSS_CLASS_PREFIX, js)
        js = modJs
        del modJs
        # Write the output file
        processedFilename = jsFilename[:-3] + '.prefixed.js'    
        f = open(processedFilename, 'w')
        f.write(js)
        f.close();
        print ' Prefixed JavaScript file written as:', processedFilename                                


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: %s <bootstrap_top_dir>' % sys.argv[0]
        sys.exit(1)
    else:
        bsTopDir = sys.argv[1]
        cssClassNames = None
        for cssFile in ('bootstrap.css', 'bootstrap.min.css', 'bootstrap-responsive.css', 'bootstrap-responsive.min.css'):
            processCss('%s/css/%s' % (bsTopDir, cssFile))
            if cssClassNames == None:
                cssClassNames = collectCssClassnames('%s/css/%s' % (bsTopDir, cssFile))
                
        if cssClassNames != None:
            for jsFile in ('bootstrap.js', 'bootstrap.min.js'):
                processJs('%s/js/%s' % (bsTopDir, jsFile), cssClassNames)
        else:
            print 'Failed to collect CSS class names - cannot modify JavaScript source files as a result'

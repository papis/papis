# Prototype WebFrontend

# requirements
- tornado, ie. "pip3 install tornado"
- libsass, e.g. "gem install sass"

# build and run

```console
# build stylesheets (for dev, or use "sass -t compress ...")
user@host~/git/github.com/alejandrogallo/papis/web sass style.scss > style.css
user@host~/git/github.com/alejandrogallo/papis/web sass normalize.scss normalize.scss  
# run frontend      
user@host~/git/github.com/alejandrogallo/papis/web python3 web.py --library /tmp/papis
```
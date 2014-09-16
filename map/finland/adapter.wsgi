import sys, os, bottle

sys.path = ['/home/keskari/webapps/api_snow/htdocs/'] + sys.path
os.chdir(os.path.dirname(__file__))

import hello_bottle # This loads your application

application = bottle.default_app()
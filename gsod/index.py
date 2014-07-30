import sys
import get_time_series

def application(environ, start_response):
    
	#add the JSON here
	output = 'Welcome to your mod_wsgi website! It uses:\n\nPython %s' % sys.version

    response_headers = [
        ('Content-Length', str(len(output))),
        ('Content-Type', 'text/plain'),
    ]

    start_response('200 OK', response_headers)

    return [output]

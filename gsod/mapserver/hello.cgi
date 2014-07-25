#!/bin/bash

echo "Content-type: text/html"
echo ""

echo '<html>'
echo '<head>'
echo '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">'
echo '<title>List of environment variables</title>'
echo '</head>'
echo '<body>'
echo '<pre>'
env
echo '</pre>'
echo '</body>'
echo '</html>'

exit 0

%#template to generate a HTML table from a list of tuples (or list of lists, or tuple of tuples or ...)
%for row in rows:
"{{row[0]}}",{{row[1]}},{{row[2]}},{{row[3]}}
%end
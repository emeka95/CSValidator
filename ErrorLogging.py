# Module for logging errors and eventually storing them in an output file
import datetime

errors = []

def log(string):
    global errors
    errors.append(string + '\n')

def write_log(scanned='', header='', directory='.'):
    global errors
    fileName = directory + '/' + "error log " + scanned + str(datetime.datetime.now()).replace(':', '.') +".txt"
    if len(errors) == 0:
        errorString = header + "No errors found."
    else:
        errorString = header + ''.join(errors)    
    with open(fileName, 'w', encoding='UTF-8') as fileObject:
        fileObject.write(errorString)
    

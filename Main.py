import os
import ErrorLogging
import ConstraintModule
import CSVWrapper
import inspect

# TODO Implement automatic constraint picking based on name of CSV file

# Get the name of the directory containing this script
# This has to work from wherever the  script is called from
filename = inspect.getframeinfo(inspect.currentframe()).filename
cwd = os.path.dirname(os.path.abspath(filename))
filesInCWD = os.listdir()

jsonFiles = [i for i in filesInCWD if i.endswith('.json')]
csvFiles = [i for i in filesInCWD if i.endswith('.csv')]

# Choose the csv file to be checked. Keep the loop going until a valid input is given
validCSVSelection = False
csvSelection = None
while not validCSVSelection:
    print("Choose a csv file to check")
    for i in range(len(csvFiles)):
        print(str(i) + ": " + csvFiles[i])

    try:
        csvSelection = int(input())
        if csvSelection in range(len(csvFiles)):
            validCSVSelection = True
        else:
            print('Unrecognised input, please try again.')
    except ValueError:
        validCSVSelection = False
        csvSelection = None

# Choose the json file to be used for checking. Keep the loop going until a valid input is given
validJSONSelection = False
jsonSelection = None
while not validJSONSelection:
    print("Choose a json file to use for checking.")
    for i in range(len(jsonFiles)):
        print(str(i) + ": " + jsonFiles[i])

    try:
        jsonSelection = int(input())
        if jsonSelection in range(len(jsonFiles)):
            validJSONSelection = True
        else:
            print('Unrecognised input, please try again.')
    except ValueError:
        validJSONSelection = False
        jsonSelection = None

constraintSet = ConstraintModule.ConstraintSet(jsonFiles[jsonSelection])
csvWrapper = CSVWrapper.CSVWrapper(csvFiles[csvSelection])
# If the csv could not be loaded, there is no point continuing. Log this issue and close the app
if csvWrapper.loaded == False:
    ErrorLogging.write_log(scanned=csvFiles[csvSelection].lower().split('.csv')[0] + ' ',
                           header="Error log for " + csvFiles[csvSelection] + ' using ' + jsonFiles[jsonSelection] + '\n',
                           directory=cwd)
    exit()

csvWrapper.loadColumns()

# Match the constraints and csvcolumns together: This is based purely on the order in which they appear
constraintSet.matchToColumns(csvWrapper)

constraintSet.validateAll()

ErrorLogging.write_log(scanned=csvFiles[csvSelection].lower().split('.csv')[0] + ' ',
                       header="Error log for " + csvFiles[csvSelection] + ' using ' + jsonFiles[jsonSelection] + '\n',
                       directory=cwd)






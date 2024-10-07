# Module for parsing json files to detect constraints for manual inputs

import json
import ErrorLogging
import CSVWrapper
import time

class ConstraintSet:

    def __init__(self):
        self.constraints = []
        self.uniqueGroups = {}
        self.oneToOnePairs = {}
        self.filePath = ''

        
    def __init__(self, filePath):
        self.constraints = []
        self.uniqueGroups = {}
        self.oneToOnePairs = {}
        self.loadConstraints(filePath)
        self.filePath = filePath

    def loadConstraints(self, filePath):
        loadedJSON = json.load(open(filePath, encoding="UTF-8"))
        for i in loadedJSON:
            newConstraint = Constraint()
            self.constraints.append(newConstraint)
            
            try:
                newConstraint.colName = i['Column']
            except KeyError:
                # If the column constraint doesn't even have a name, skip it and tell the user
                ErrorLogging.log(filePath + ' contains a column that has not been named. Please fix this.')
                self.constraints.pop()
                continue
            
            try:
                newConstraint.essential = eval(i['Essential'])
            except KeyError:
                newConstraint.essential = False

            try:
                newConstraint.hashable = eval(i['Hashable'])
            except KeyError:
                newConstraint.Hashable = False

            try:
                newConstraint.minimum = float(i['Minimum'])
            except KeyError:
                newConstraint.minimum = -float('inf')

            try:
                newConstraint.maximum = float(i['Maximum'])
            except KeyError:
                newConstraint.maximum = float('inf')

            try:
                newConstraint.possibleValues = i['Values']
                newConstraint.validate = Constraint.validateFinitePossibilities
            except KeyError:
                pass

            try:
                if i['Unique Group'].upper() != 'NONE':
                    if i['Unique Group'] in self.uniqueGroups:
                        self.uniqueGroups[i['Unique Group']].append(newConstraint)
                        newConstraint.uniqueGroup = i['Unique Group']
                    else:
                        self.uniqueGroups[i['Unique Group']] = []
                        self.uniqueGroups[i['Unique Group']].append(newConstraint)
                        newConstraint.uniqueGroup = i['Unique Group']
            except KeyError:
                pass

            try:
                newConstraint.trimmed = eval(i['Trimmed'])
            except KeyError:
                newConstraint.trimmed = False

            # If a type isn't specified let the script fail completely, that should never be allowed
            if i['Type'].upper() == 'INT' or i['Type'].upper() == 'INTEGER':
                newConstraint.colType = int
                newConstraint.decimalPlaces = 0
                newConstraint.validate = newConstraint.validateNumber
                newConstraint.validateList = newConstraint.validateNumList
            elif i['Type'].upper() == 'FLOAT' or i['Type'].upper() == 'DECIMAL':
                newConstraint.colType = float
                newConstraint.decimalPlaces = int(i['Decimal Places'])
                newConstraint.validate = newConstraint.validateNumber
                newConstraint.validateList = newConstraint.validateNumList
            elif i['Type'].upper() == 'TEXT' or i['Type'].upper() == 'STRING':
                newConstraint.colType = str
                newConstraint.decimalPlaces = 0
                newConstraint.validate = newConstraint.validateString
                newConstraint.validate = newConstraint.validateStringList

            # If a finite range of vaues has been given, that should supercede everything else
            try:
                newConstraint.values = i['Values']
                newConstraint.validate = newConstraint.validateFinitePossibilities
                newConstraint.validateList = newConstraint.validatePossibilitiesList
            except KeyError:
                # If no values were given, then use the standard validation by type method
                pass

            # Check for one to one properties and pair up the appropriate constraint objects as necessary
            try:
                newConstraint.oneToOne = i['One To One']
                if i['One To One'] in self.oneToOnePairs:
                    if len(self.oneToOnePairs[i['One To One']]) == 2:
                        ErrorLogging.log('Error with the One to One Pairing ' + i['One To One'] + '. More than 2 columns are in this pairing. This is an issue with the JSON file selected.')
                    else:
                        self.oneToOnePairs[i['One To One']].append(newConstraint)
                else:
                    self.oneToOnePairs[i['One To One']] = [newConstraint]
            except KeyError:
                pass

            try:
                if i['Case Sensitive'].upper() == 'TRUE':
                    newConstraint.caseSensitive = True
                elif i['Case Sensitive'].upper() == 'FALSE':
                    newConstraint.caseSensitive = False
                else:
                    # If a non-boolean value was entered, tell the user there's a problem.
                    ErrorLogging.log('Error with chosen json file: ' + filePath + ' . Column ' + i['Column'] + ' specifies that case sensitivity is ' + i['Case Sensitive'] + ' but only values True and False are valid. Please correct this before usinmg this json file again.')
                if newConstraint.colType != str:
                    ErrorLogging.log('Only columns of type string can use the Case Sensistive parameter. Please correct this before using this json file again.')

            except KeyError:
                # If Case was not defined, that's fine, it is not compulsory
                pass
            
    def matchToColumns(self, wrapper):
        if type(wrapper) != CSVWrapper.CSVWrapper:
            print("Constraints can conly be matched to CSVWrappers.")
            return

        if len(wrapper.columns) != len(self.constraints):
            ErrorLogging.log('The CSV file has ' + str(len(wrapper.columns)) + ' columns but there should be ' + str(len(self.constraints)) + ' columns')
            return

        for i in range(len(wrapper.columns)):
            
            # Apply trimming if the column has been flagged to be checked as trimmed
            if self.constraints[i].trimmed:
                self.constraints[i].column = [item.strip() for item in wrapper.columns[i]]
            else:
                self.constraints[i].column = wrapper.columns[i]

            # Change the "effective case" if the json file dictates that this should be done
            if not self.constraints[i].caseSensitive:
                self.constraints[i].column = [item.upper() for item in self.constraints[i].column]
                self.constraints[i].possibleValues = [item.upper() for item in self.constraints[i].possibleValues]

    def validateAll(self):
        self.validateColumns()
        self.validateGroups()
        self.validateOneToOne()

    def validateColumns(self):
        for constraint in self.constraints:
            constraint.validateList(constraint.column)
            
    def validateGroupsFast(self):
        # Any IndexErrors caused by this variable mean that there is an uneven number of columns
        # This could be alleviated by taking the length for each group, but that hides a major problem
        noOfRows = len(self.constraints[0].column)
        
        for group in self.uniqueGroups:
            uniques = set() # A set always has unique values, so duplicates won't be added
            for n in range(noOfRows):
                uniques.add(''.join([str(constraint.column[n]) for constraint in self.uniqueGroups[group]]))

            if noOfRows != len(uniques):
                # This means this group has some duplicates
                ErrorLogging.log('Unique group ' + str(group) + ' has ' + str(noOfRows - len(uniques)) + ' duplicate rows.')

    """
        def validateGroups(self):
            # A newer but possibly slower version validateGroupsFast. This version allows each duplicate row to be logged
            noOfRows = len(self.constraints[0].column)
            
            for group in self.uniqueGroups:
                uniques = []
                for n in range(noOfRows):
                    newString = ''.join([str(constraint.column[n]) for constraint in self.uniqueGroups[group]])
                    if newString not in uniques:
                        uniques.append(newString)
                    else:
                        # The + 2 is to account for the header being removed and then Python counting from 0
                        ErrorLogging.log('Row: ' + str(n + 2) + ' contains a duplicate entry for the unique group: ' + str(group) + '.')
    """
    
    def validateGroups(self):
        # An even newer version that shows exactly what has been duplicated
        noOfRows = len(self.constraints[0].column)

        for group in self.uniqueGroups:
            records = []
            for i in range(noOfRows):
                newString = ''.join([str(constraint.column[i]) for constraint in self.uniqueGroups[group]])
                records.append(newString)
                # j is the first instance of newString appearing in the list, if it is different from i, then a copy of newString was already present
                j = records.index(newString)
                if j != i:
                    # The + 2 is to account for the header being removed and python counting from 0 while excel starts at 1
                    ErrorLogging.log("Row: " + str(i + 2) + " contains the same information as row " + str(j + 2) + " for the unique group: " + str(group) + ".")

    def validateOneToOne(self):
        for pair in self.oneToOnePairs:
            if len(self.oneToOnePairs[pair]) != 2:
                ErrorLogging.log('The one to one relationship requires columns to be in pairs. However, ' + str(len(self.oneToOnePairs[pair])) + ' columns were given the property: ' + pair + '. Check the JSON files for errors.')
                continue

            n = len(self.oneToOnePairs[pair][0].column)

            # Dictionaries listing every  a to b and b to a relationship
            # The key is a string, the value is a list
            a_to_b = {}
            b_to_a = {}
            for i in range(n):
                a = self.oneToOnePairs[pair][0].column[i]
                b = self.oneToOnePairs[pair][1].column[i]

                # If the key is new, add it to the appropriate dictionary
                if a not in a_to_b:
                    a_to_b[a] = []
                if b not in b_to_a:
                    b_to_a[b] = []

                # If the value is new, add it to the list of values seen for error logging purposes
                if b not in a_to_b[a]:
                    a_to_b[a].append(b)
                if a not in b_to_a[b]:
                    b_to_a[b].append(a)

            # Log errors
            for i in a_to_b:
                if len(a_to_b[i]) != 1:
                    errorString = 'Columns ' + str(self.oneToOnePairs[pair][0].colName) + ' and ' + str(self.oneToOnePairs[pair][1].colName) + ' share a one to one relationship but '
                    errorString += 'entry ' + str(i) + ' has multiple associated values: ' + str(a_to_b[i])
                    ErrorLogging.log(errorString)
            for i in b_to_a:
                if len(b_to_a[i]) != 1:
                    errorString = 'Columns ' + str(self.oneToOnePairs[pair][1].colName) + ' and ' + str(self.oneToOnePairs[pair][0].colName) + ' share a one to one relationship but '
                    errorString += 'entry ' + str(i) + ' has multiple associated values: ' + str(b_to_a[i])
                    ErrorLogging.log(errorString)

                
            

class Constraint:
    
    def __init__(self):
        self.colName = None
        self.essential = False
        self.hashable = False
        self.colType = str
        self.minimum = -float('inf')
        self.maximum = float('inf')
        self.decimalPlaces = 0
        self.uniqueGroup = None
        self.validate = self.validateString
        self.validateList = self.validateStringList
        self.column = []
        self.possibleValues = []
        self.trimmed = False # Not a constraint per se, but it affects how they will be treated
        self.caseSensitive = True

    def validateNumber(self, num):
        if not self.essential and num == '':
            return True
        try:
            valueRangeCheck = float(num) >= self.minimum and float(num) <= self.maximum
            decimalPlacesCheck = False
            if '.' in num:
                decimalPlacesCheck = len(num.split(".")[1]) >= self.decimalPlaces
            else:
                decimalPlacesCheck = self.decimalPlaces == 0

            return valueRangeCheck and decimalPlacesCheck
        except ValueError:
            return False

    def validateString(self, string):
        if not self.essential and string == '':
            return True
        if self.hashable and string == '#':
            return True
        return len(string) >= self.minimum and len(string) <= self.maximum

    def validateFinitePossibilities(self, value):
        return value in self.possibleValues

    def validateNumList(self, target):
        n = len(target)
        for i in range(n):
            if not self.validateNumber(target[i]):
                # The plus 2 is to match the row count seen in excel etc. Here the header is skipped and counting starts from 0 so 2 rows aren't counted
                errorString = "Entry at Column: " + self.colName + ", Row: " + str(i + 2) + " has value: " + str(target[i]) + ". This column "
                if self.essential:
                    errorString += "is essential and "
                errorString += "must be a number between " + str(self.minimum) + " and " + str(self.maximum) + " with at least " + str(self.decimalPlaces) + " decimal places."
                ErrorLogging.log(errorString)

    def validateStringList(self, target):
        n = len(target)
        for i in range(n):
            if not self.validateString(target[i]):
                # The plus 2 is to match the row count seen in excel etc. Here the header is skipped and counting starts from 0 so 2 rows aren't counted
                errorString = "Entry at Column: " + self.colName + ", Row: " + str(i + 2) + " has value: " + str(target[i]) + ". This column "
                if self.essential:
                    errorString += "is essential and "
                errorString += "must be between " + str(self.minimum) + " and " + str(self.maximum) + " characters long."
                ErrorLogging.log(errorString)

    def validatePossibilitiesList(self, target):
        n = len(target)
        for i in range(n):
            if not self.validateFinitePossibilities(target[i]):
                # The plus 2 is to match the row count seen in excel etc. Here the header is skipped and counting starts from 0 so 2 rows aren't counted
                errorString = "Entry at Column: " + self.colName + ", Row: " + str(i + 2) + " has value: " + str(target[i]) + ". This column "
                if self.essential:
                    errorString += "is essential and "
                errorString += "must have one of the following values: " + str(self.possibleValues) + "."
                ErrorLogging.log(errorString)
        

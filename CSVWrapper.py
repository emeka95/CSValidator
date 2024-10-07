import ErrorLogging

class CSVWrapper:

    def __init__(self, filePath, delimiter='|', encoding='UTF-8'):
        self.filePath = filePath
        self.delimiter = delimiter
        self.lines = []
        self.encoding = encoding
        self.columns = []
        self.loaded = False
        self.loadFile(filePath)

    def loadFile(self, filePath):
        try:
            self.lines = open(filePath, encoding=self.encoding).read().split('\n')
            # Remove trailing lines that are either empty of just contain the delimter multiple times
            # This will keep going until the first non-trivial line is encountered
            # Anything above that will be checked normally
            while(self.lines[-1].replace('|', '') == ''):
                self.lines.pop()
            self.loaded = True
        except UnicodeError:
            # If the file cannot be read properly, there is not point contuning.
            # Log this error and shut down the app
            ErrorLogging.log("The file: " + filePath + " does not appear to be encoded in the UTF-8 standard so it cannot be checked.")
            

    def loadColumns(self):
        # Find the leangth of the header (ignoring empties that come after it)
        tempHeader = self.lines[0].split(self.delimiter)
        while tempHeader[-1] == '':
            tempHeader.pop()
        numberOfColumns = len(tempHeader)
        self.columns = []
        for i in range(numberOfColumns):
            self.columns.append([])

        rowCounter = 1
        while rowCounter < len(self.lines):
            separatedLine = self.lines[rowCounter].split(self.delimiter)
            # Ignore the possibly empty columns at the end; keep popping until len(separatedLines) == noOfColumns
            # Or until a non-empty string is encountered
            while len(separatedLine) > numberOfColumns and separatedLine[-1] == '':
                separatedLine.pop()
            
            if len(separatedLine) != numberOfColumns:
                ErrorLogging.log("Row: " + str(rowCounter + 1) + " has " + str(len(separatedLine)) + " columns but the header has " + str(numberOfColumns) + ".")
            else:
                for col in range(numberOfColumns):
                    self.columns[col].append(separatedLine[col])

            rowCounter += 1


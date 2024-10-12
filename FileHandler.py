import json
import csv


class Handler:
    def __init__(self, rules_path: str):
        self.rules_path: str = rules_path
        self.data: dict[str, list] = {}
        self.raw_rules: dict = {}  # The rules as they are presented in the rules file

        # Default values, will be overwitten by the rules file
        self.file_rules: dict = {
            'encoding': 'utf-8',
            'delimiter': ',',
            'quotechar': '"',
            'newline': '',
            'fieldnames': None
        }


    def load_rules(self, file_path: str) -> None:
        self.raw_rules = json.load(open(file_path, encoding="utf-8"))
        # Overwrite the default values with the file's values, but avoid reading non-standard keys
        self.file_rules = {key: self.raw_rules.get(key, self.file_rules[key]) for key in self.file_rules}


    def load_csv(self, csv_path: str) -> None:
        """
        Loads a CSV file as a dictionary of header to column
        """
        with open(csv_path, newline=self.file_rules['newline']) as file:
            reader = csv.DictReader(file)
            self.data = {field: [row[field] for row in reader] for field in reader.fieldnames}
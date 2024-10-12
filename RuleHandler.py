import ErrorLogging


class RuleSet:
    """
    This class acts as a contained for individual column rules and also manages
    rules that must look at multiple columns at once e.g. One to One checks
    """
    def __init__(self, rule_info: dict):
        self.rules: list[Rule] = []
        self.unique_groups = {}
        self.one_to_one_pairs = []
        self.load_rules(rule_info)


    def load_rules(self, rule_info: dict) -> None:
        for key, val in rule_info.items():
            self.rules.append(Rule(key, val))
            if 'unique group' in val:
                self.unique_groups[val['unique group']] = self.unique_groups.get(val['unique group'], []).append(key)
            if 'one to one' in val:
                pair = (key, val['one to one'])
                # Protection against processing the same pair twice if the rules for both columns
                # mention the column
                if not (pair in self.one_to_one_pairs or (pair[1], pair[0]) in self.one_to_one_pairs):
                    self.one_to_one_pairs.append(pair)


    def validate_unique_groups(self, data: dict[str, list]):
        """
        Check multiple columns at once and ensure that the combination of those columns
        is unique
        """
        for group_name, column_names in self.unique_groups.items():
            unique_dict: dict[tuple: int] = {}
            columns = {col: data[col] for col in column_names}  # Take only relevant cols for this group
            for idx, values in enumerate(zip(columns.values())):
                if values in unique_dict:
                    ErrorLogging.log(
                        f'Row {idx + 1} contains a duplicate value for unique group {group_name}: '
                        f'Values {values} match row {unique_dict[values] + 1}'
                    )
                else:
                    unique_dict[values] = idx
    

    def validate_one_to_one(self, data: dict[str, list]) -> int:
        """
        Checks that two columns have a one to one relationship, and returns any examples of this breaking
        """
        error_count = 0
        for pair in self.one_to_one_pairs:
            if len(pair) != 2:
                raise ValueError(f'A one to one pair must specify 2 columns, instead got {len(pair)}')
            a, b = pair

            a_to_b: dict[str, set] = {}
            b_to_a: dict[str, set] = {}

            # Generate dictionary a every a -> b and b -> a combination
            for a, b in zip(data[a], data[b]):
                if not a in a_to_b:
                    a_to_b[a] = set()
                a_to_b[a].add(b)
                if not b in b_to_a:
                    b_to_a[b] = set()
                b_to_a[b].add(a)
            
            # Log errors
            for key, val in a_to_b:
                if len(val) != 1:
                    ErrorLogging.log(f'Columns {a} and {b} have a 1-to-1 relation, but {key} matches to {val}')
                    error_count += 1
            for key, val in b_to_a:
                if len(val) != 1:
                    ErrorLogging.log(f'Columns {b} and {a} have a 1-to-1 relation, but {key} matches to {val}')
                    error_count += 1
        return error_count


class Rule:
    def __init__(self, name: str, rule_info: dict) -> None:
        self.name = name
        self.checks = []
        self.parse_rule(rule_info)

    def parse_rule(self, rule_info: dict) -> None:
        # Setup checks for type
        if not 'type' in rule_info or rule_info['type'].lower() in ('str', 'string', 'text', 'varchar'):
            self.data_type = 'str'
        elif rule_info['type'].lower() in ('int', 'integer'):
            self.data_type = 'int'
        elif rule_info['type'].lower() in ('float', 'double', 'decimal', 'number', 'numeric'):
            self.data_type = 'float'
        # TODO: Add support for date and other data types
        else:
            raise ValueError(f'Unrecognised value for type: {rule_info["type"]}')
        self.checks = [self.validate_data_type]

        # Setup checks for values
        if 'values' in rule_info:
            self.values = rule_info['values']
            self.checks.append(self.validate_possibilities_list)
        
        if 'minimum' in rule_info or 'maximum' in rule_info:
            self.minimum = float(rule_info.get('minimum', '-inf'))
            self.maximum = float(rule_info.get('maximum', 'inf'))
            self.checks.append(self.validate_min_max)
        
        # Exceptions are values that might break other rules, but should still be allowed
        # They bypass type checks and min_max checks
        # They DO NOT bypass possiblee checks; they should just be in values
        self.exceptions = set(rule_info.get('exceptions', []))
    

    def validate_data_type(self, column: list) -> int:
        if self.data_type == 'str':
            return 0  # Nothing to check here
        if self.data_type == 'int':
            bad_lines = [idx for idx, val in enumerate(column) if not self.check_int(val)]
        elif self.data_type == 'float':
            bad_lines = [idx for idx, val in enumerate(column) if not self.check_float(val)]
        
        # Log the lines that failed, and return an overall failure/success
        for line in bad_lines:
            self.log_issue(line, f'cannot be interpreted as {self.data_type}')
        return len(bad_lines)   


    def check_int(self, value: str) -> bool:
        try:
            int(value)
        except ValueError:
            return value in self.exceptions
    
    def check_float(self, value: str) -> bool:
        try:
            int(value)
        except ValueError:
            return value in self.exceptions
    

    def validate_possibilities_list(self, column: list[str]) -> int:
        bad_lines = [idx for idx, val in enumerate(column) if not val in self.values]
        for line in bad_lines:
            self.log_issue(line, f'is not among allowed values: {self.values}')
        return len(bad_lines)


    def validate_min_max(self, column: list[str]) -> int:
        if self.type == 'str':
            bad_lines = [idx for idx, val in enumerate(column) if not self.minimum <= len(val) <= self.maximum]
        elif self.type in ('int', 'float'):
            bad_lines = [idx for idx, val in enumerate(column) if not self.minimum <= val <= self.maximum]
        
        # Log the lines that failed the check
        if self.data_type == 'str':
            for line in bad_lines:
                self.log_issue(line, f'must be between {self.minimum} and {self.maximum} characters long')
        else:
            for line in bad_lines:
                self.log_issue(line, f'must have a value between {self.minimum} and {self.maximum}')
    

    def log_issue(self, row_num: int, end_text: str = '') -> None:
        """
        Several checks requried logging basically the same error structure, so this
        is used to simplify that
        """
        ErrorLogging.log(f'Entry at row: {row_num + 1} for column {self.name} {end_text}')
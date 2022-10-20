import json, os

class Config:
    def __init__(self):    
        self.path = os.path.join(os.path.dirname(__file__), 'config.json')

        # Load the config data from a JSON file
        with open(self.path, 'r') as f:
            data = json.load(f)

        self.db_path = data['db_path']
        self.update_secs = data['update_secs']
        self.auto_start = data['auto_start']
        self.from_email = data['from_email']
        self.from_password = data['from_password']
        self.to_email = data['to_email']

    def save(self):    
        data = {
            'db_path': self.db_path,
            'update_secs': self.update_secs,
            'auto_start': self.auto_start,
            'from_email': self.from_email,
            'from_password': self.from_password,
            'to_email': self.to_email,
        }

        # Write the config data to a JSON file
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=4)

config = Config()

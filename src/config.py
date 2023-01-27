import json, os

class Config:
    def __init__(self):
        # Setup the default config values
        self.db_path = 'checker.db'
        self.update_secs = 300
        self.auto_start = False
        self.from_email = ''
        self.from_password = ''
        self.to_email = ''
    
        # Find the AppData path
        self.appdata = os.path.join(os.getenv('LOCALAPPDATA'), 'CL-Checker')
        
        # Make sure the the AppData directory exists
        if not os.path.isdir(self.appdata):
            try:
                os.mkdir(self.appdata)
            except:
                print(f'Unable to create directory {self.appdata}')
        
        # Generate the config path
        self.config_path = os.path.join(self.appdata, 'config.json')
        
        # Load the data from the config if it exists, otherwise save the default values
        if self.path.exists(self.config_path):
            self.load()
        else:
            self.save()

    def load(self):
        # Load the config data from a JSON file
        with open(self.config_path, 'r') as f:
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
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=4)

config = Config()

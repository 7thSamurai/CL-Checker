import os, sys, logging

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import * 
from PyQt5.QtMultimedia import*

from updater import Updater
from config import config
from db import DB, Query
from send_email import send_email

class PrefDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Preferences')

        # Setup an email validator regular expression
        re = QRegularExpression('\\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,4}\\b')
        re.setPatternOptions(QRegularExpression.CaseInsensitiveOption);
        email_validator = QRegularExpressionValidator(re)

        # Setup the email sender stuff
        sender_group = QGroupBox('Sender')
        sender_layout = QFormLayout()
        
        self.sender_email = QLineEdit()
        self.sender_email.setText(config.from_email)
        self.sender_email.setValidator(email_validator)
        self.sender_email.textChanged.connect(self.on_sender_email_changed)
        
        self.sender_password = QLineEdit()
        self.sender_password.setText(config.from_password)
        self.sender_password.setEchoMode(QLineEdit.Password)
        
        sender_layout.addRow('Email', self.sender_email)
        password_label = QLabel('<a href="https://www.lifewire.com/get-a-password-to-access-gmail-by-pop-imap-2-1171882">Password</a>')
        password_label.setOpenExternalLinks(True)
        sender_layout.addRow(password_label, self.sender_password)
        sender_group.setLayout(sender_layout)

        # Setup the email receiver stuff
        receiver_group = QGroupBox('Receiver')
        receiver_layout = QFormLayout()
        
        self.receiver_email = QLineEdit()
        self.receiver_email.setText(config.to_email)
        self.receiver_email.setValidator(email_validator)
        self.receiver_email.textChanged.connect(self.on_receiver_email_changed)
        
        receiver_layout.addRow('Email', self.receiver_email)
        receiver_group.setLayout(receiver_layout)

        # Setup the updater stuff
        updater_group = QGroupBox('Updater')
        updater_layout = QFormLayout()
        
        self.updater_secs = QSpinBox()
        self.updater_secs.setMinimum(1)
        self.updater_secs.setMaximum(99999)
        self.updater_secs.setValue(config.update_secs)

        self.auto_start = QCheckBox()
        self.auto_start.setCheckState(Qt.CheckState.Checked if config.auto_start else Qt.CheckState.Unchecked)

        updater_layout.addRow('Update Interval (secs.)', self.updater_secs)
        updater_layout.addRow('Autostart application at boot', self.auto_start)
        updater_group.setLayout(updater_layout)

        # Setup the buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.ok_callback)
        button_box.rejected.connect(self.reject)

        # Setup the main layout
        layout = QVBoxLayout()
        layout.addWidget(sender_group)
        layout.addWidget(receiver_group)
        layout.addWidget(updater_group)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def on_sender_email_changed(self, text):
        # Update the text color depending on wether the input is valid or not
        if self.sender_email.hasAcceptableInput():
            self.sender_email.setStyleSheet('');
        else:
            self.sender_email.setStyleSheet('QLineEdit { color: red;}');

    def on_receiver_email_changed(self, text):
        # Update the text color depending on wether the input is valid or not
        if self.receiver_email.hasAcceptableInput():
            self.receiver_email.setStyleSheet('');
        else:
            self.receiver_email.setStyleSheet('QLineEdit { color: red;}');

    def ok_callback(self):
        # Setup an gmail validator regular expression
        re = QRegularExpression('\\b[A-Z0-9._%+-]+@gmail\\.com\\b')
        re.setPatternOptions(QRegularExpression.CaseInsensitiveOption);
    
        # Make sure that the sender email is a gmail address
        if not re.match(self.sender_email.text()).hasMatch():
            QMessageBox.warning(
                self, 
                'Invalid Sender Email',
                'Only gmail addresses are supported for the sender address', 
                QMessageBox.Ok
            )
            
            # Turn the text color to red to signify an error
            self.sender_email.setStyleSheet('QLineEdit { color: red;}');
            return
    
        # Update the configuration data
        config.update_secs = self.updater_secs.value()
        config.auto_start = self.auto_start.isChecked()
        config.from_email = self.sender_email.text()
        config.from_password = self.sender_password.text()
        config.to_email = self.receiver_email.text()
        
        # Update the auto-start stuff in the Windows registry
        try:
            RUN_PATH = "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
            settings = QSettings(RUN_PATH, QSettings.NativeFormat)
            
            if config.auto_start:
                settings.setValue("ClChecker", f'"{sys.argv[0]}" autostart');
            else:
                settings.remove("ClChecker")
                
        except Exception as e:
            logging.error(f'Failed to update registry: {e}')
            config.auto_start = False

        # Update the configuration file
        config.save()

        self.close()

class TableRow():
    def __init__(self, table, index, query, items_found, failed, enabled):
        # Setup the area validtor
        re = QRegularExpression('[a-z]*')
        re.setPatternOptions(QRegularExpression.CaseInsensitiveOption);
        area_validator = QRegularExpressionValidator(re)

        area = QLineEdit()
        area.setValidator(area_validator)
        area.setToolTip('Craigslist search area')
        area.setText(query.area)
        area.textChanged.connect(self.area_changed)
        area.setEnabled(enabled)

        section = QComboBox()
        section.setToolTip('Craigslist section')
        section.addItems(Query.sections.keys())
        section.setCurrentText(query.section)
        section.currentTextChanged.connect(self.section_changed)
        section.setEnabled(enabled)

        search = QLineEdit()
        search.setToolTip('Search query for Craigslist')
        search.setText(query.query)
        search.textChanged.connect(self.query_changed)
        search.setEnabled(enabled)
            
        email = QCheckBox()
        email.setToolTip('Enable/Disable sending email alerts')
        email.setChecked(query.email)
        email.stateChanged.connect(self.email_changed)
        email.setEnabled(enabled)

        alarm = QCheckBox()
        alarm.setToolTip('Enable/Disable sounding an alarm')
        alarm.setChecked(query.alarm)
        alarm.stateChanged.connect(self.alarm_changed)
        alarm.setEnabled(enabled)

        # Update the color of both checkboxs to make them more visible
        checkbox_palette = email.palette()
        checkbox_palette.setColor(QPalette.Active, QPalette.Background, QColor(102, 102, 102))
        checkbox_palette.setColor(QPalette.Disabled, QPalette.Background, QColor(102, 102, 102))
        email.setPalette(checkbox_palette)
        alarm.setPalette(checkbox_palette)

        # Check if the query had previous failed, and if so highlight everything red
        if failed:
            area.setStyleSheet('QLineEdit { color: red;}');
            section.setStyleSheet('QComboBox { color: red;}');
            search.setStyleSheet('QLineEdit { color: red;}');

        db = DB(config.db_path)
        total_items_found = db.get_num_products(query.url())

        found = QPushButton(str(total_items_found))
        found.setToolTip('Number of items found in the last update')
        found.clicked.connect(self.list_products)
        found.setEnabled(True)
        
        if items_found > 0:
            found.setStyleSheet('QPushButton { color: green; }');

        table.setCellWidget(index, 0, area)
        table.setCellWidget(index, 1, section)
        table.setCellWidget(index, 2, search)
        table.setCellWidget(index, 3, email)
        table.setCellWidget(index, 4, alarm)
        table.setCellWidget(index, 5, found)

        self.id = query.id

    def area_changed(self, text):
        # Update the query's area in the database
        db = DB(config.db_path)
        query = db.get_query(self.id)
        query.area = text
        
        db.update_query(query)

    def section_changed(self, text):
        # Update the query's section in the database
        db = DB(config.db_path)
        query = db.get_query(self.id)
        query.section = text
        
        db.update_query(query)

    def query_changed(self, text):
        # Update the query's query search in the database
        db = DB(config.db_path)
        query = db.get_query(self.id)
        query.query = text
        
        db.update_query(query)
     
    def email_changed(self, state):
        # Update the query's email flag in the database
        db = DB(config.db_path)
        query = db.get_query(self.id)
        query.email = state != 0
        
        db.update_query(query)
        
    def alarm_changed(self, state):
        # Update the query's alarm flag in the database
        db = DB(config.db_path)
        query = db.get_query(self.id)
        query.alarm = state != 0

        db.update_query(query)

    def list_products(self):
        db = DB(config.db_path)
        query = db.get_query(self.id)
        products = db.get_products(query.url())     

        dlg = QDialog()
        dlg.setWindowTitle(f'Products found by {query.name()}')
        
        layout = QVBoxLayout()
        browser = QTextBrowser(minimumWidth=450, minimumHeight=600)
        browser.setOpenExternalLinks(True)
        
        for product in products:
            browser.append(f'<a href="{product.url}">{product.name}</a>')
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dlg.accept)
        
        layout.addWidget(browser)
        layout.addWidget(button_box)
        dlg.setLayout(layout)
        dlg.exec()

class Main(QMainWindow):
    def __init__(self, app, hide_window):
        super(QMainWindow, self).__init__()
        
        self.found = {}
        self.failed_queries = set()

        # Setup the UI
        self.make_ui(app)
        self.setFixedSize(self.size());
        
        if hide_window:
            self.hide()
        
        # Start the update schedule
        self.counter = config.update_secs
        self.updater = Updater()
        self.updater.finished.connect(self.finish_update)
        self.start_update()
        
    def make_ui(self, app):
        """
        Generate and build the UI
        """

        bar = self.menuBar()
        
        # Create the file menu
        app_menu = bar.addMenu('&App')
        
        # Add the hide option
        hide_action = QAction('&Hide', self)
        hide_action.setToolTip('Hides this window')
        hide_action.triggered.connect(self.hide)
        app_menu.addAction(hide_action)
        
        # Add the exit option
        exit_action = QAction('&Exit', self)
        exit_action.setToolTip('Exists the entire program')
        exit_action.triggered.connect(lambda: self.close(app))
        app_menu.addAction(exit_action)
        
        # Create the settings menu
        settings_menu = bar.addMenu('&Settings')
        
        # Add the preferences option
        pref_action = QAction('&Preferences', self)
        pref_action.setToolTip('Shows a preferences dialog')
        pref_action.triggered.connect(self.pref_dialog)
        settings_menu.addAction(pref_action)
        
        # Create the help menu
        help_menu = bar.addMenu('&Help')

        # Create the about menu
        about_action = QAction('&About', self)
        about_action.setToolTip('Shows an about dialog')
        about_action.triggered.connect(self.about_dialog)
        help_menu.addAction(about_action)
        
        # Load the icona
        self.icon = QIcon(os.path.join(os.path.dirname(__file__), 'icon.png'))
        self.icon_error = QIcon(os.path.join(os.path.dirname(__file__), 'icon_error.png'))
        
        # Setup the icon on the system tray
        self.tray = QSystemTrayIcon(self.icon, app)
        self.tray.setToolTip('CL-Checker')
        
        # Create the show option
        menu = QMenu()
        show = menu.addAction('Show')
        show.setToolTip('Shows the main window')
        show.triggered.connect(self.show)
        
        # Create the quit option
        quit = menu.addAction('Quit')
        quit.setToolTip('Exists the entire program')
        quit.triggered.connect(lambda: self.close(app))
        
        # Add options to system tray
        self.tray.setContextMenu(menu)
        self.tray.show()
        
        # Setup the buttons
        updater_buttons_layout = QHBoxLayout()
        
        self.start_button = QPushButton('Start')
        self.start_button.setToolTip('Start the checker')
        self.start_button.setStyleSheet('QPushButton { background-color: grey; }');
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_updater)
        updater_buttons_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton('Stop')
        self.stop_button.setToolTip('Stop the checker')
        self.stop_button.setStyleSheet('QPushButton { background-color: red; }');
        self.stop_button.clicked.connect(self.stop_updater)
        updater_buttons_layout.addWidget(self.stop_button)
        
        # Setup the table
        table_layout = QHBoxLayout()
        
        self.table = QTableWidget()
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.table.setColumnCount(6)
        self.table.setRowCount(10)
        self.table.setHorizontalHeaderLabels(['Area', 'Section', 'URL', 'Email', 'Alarm', 'Found'])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        table_layout.addWidget(self.table)
        
        table_buttons_layout = QVBoxLayout()
        add_button = QPushButton('Add')
        add_button.setToolTip('Adds a query')
        add_button.clicked.connect(self.add_query)
        table_buttons_layout.addWidget(add_button)
        
        del_button = QPushButton('Delete')
        del_button.setToolTip('Deletes the currently selected query')
        del_button.clicked.connect(self.del_query)
        table_buttons_layout.addWidget(del_button)
        table_buttons_layout.addStretch()
        table_layout.addLayout(table_buttons_layout)
        
        # Setup the main layout
        layout = QVBoxLayout()
        layout.addLayout(updater_buttons_layout)
        layout.addLayout(table_layout)

        # Set the main layout
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Create the progress bar for the status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, config.update_secs)
        self.progress_bar.setValue(config.update_secs)
        self.statusBar().addPermanentWidget(self.progress_bar, 1)

        self.setWindowTitle('CL-Checker')
        self.show()
        self.update_table(False)

    def close(self, app):
        # Make sure that the thread is stopped
        self.stop_updater()
        self.updater.wait()
        self.updater.quit()
        
        app.quit()

    def update_table(self, enabled):
        db = DB(config.db_path)
        queries = db.get_queries()

        self.rows = []

        self.table.clear()
        self.table.setColumnCount(6)
        self.table.setRowCount(len(queries))
        self.table.setHorizontalHeaderLabels(['Area', 'Section', 'Query', 'Email', 'Alarm', 'Found'])

        # Generate the rows
        for i, query in enumerate(queries):
            found = 0 if query.id not in self.found else self.found[query.id]
            failed = query.url() in self.failed_queries
            self.rows.append(TableRow(self.table, i, query, found, failed, enabled))

    def about_dialog(self):
        # Setup the about dialog
        about = QMessageBox(self)
        about.setWindowTitle('About')
        about.setText(
            '<h1 align=center>CL-Checker 1.0</h1>'
            '<p>Simple system-tray utility program to automatically check for new Craigslist postings based on custom search queries, using a headless version of Chrome.</p><br>'
            '<p align=center><small>Written in 2022 by <a href="https://github.com/7thSamurai">Zach C.<a/></small></p>'
        )
        
        about.exec()

    def pref_dialog(self):
        # Setup the preferences dialog
        pref = PrefDialog(self)
        pref.exec()

    def start_updater(self):
        self.counter = config.update_secs - 1
        self.start_update()
    
        self.start_button.setEnabled(False)
        self.start_button.setStyleSheet('QPushButton { background-color: grey; }');
        
        self.stop_button.setEnabled(True)
        self.stop_button.setStyleSheet('QPushButton { background-color: red; }');
    
        self.update_table(False)
    
    def stop_updater(self):    
        # First set all the buttons to grey
        self.start_button.setEnabled(False)
        self.start_button.setStyleSheet('QPushButton { background-color: grey; }');
        
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet('QPushButton { background-color: grey; }');
        
        # Then stop the thread
        self.progress_bar.setFormat('Stopping...')

        # Stop the timer if it's already running
        try:
            self.update_timer.stop()
        except:
            pass
    
        # Stop the thread
        if self.updater.isRunning():
            self.updater.finished.disconnect()
            self.updater.finished.connect(self.finish_stopped_update)
            self.updater.requestInterruption()

        else:
            # Now set the start button to green
            self.start_button.setEnabled(True)
            self.start_button.setStyleSheet('QPushButton { background-color: green; }');
            self.update_table(True)

        self.progress_bar.setValue(0)
        self.progress_bar.setFormat('Stopped')

    def finish_stopped_update(self):
        self.statusBar().showMessage('Stopped')
    
        # Now set the start button to green
        self.start_button.setEnabled(True)
        self.start_button.setStyleSheet('QPushButton { background-color: green; }');

        # Make sure that we finish the update if there was any products found
        if self.updater.total_products != {}:
            self.finish_update(restart_timer=False)

        self.update_table(True)
        self.updater.finished.disconnect()
        self.updater.finished.connect(self.finish_update)

    def add_query(self):
        if self.stop_button.isEnabled():
            QMessageBox.warning(
                self, 
                'Error: The Checker is running',
                'Please first stop the Checker before making any changes to the table. You may accomplish this by clicking the large red button at the top of the window.', 
                QMessageBox.Ok
            )
            
            return
    
        # Add a new query to the database
        db = DB(config.db_path)
        db.add_query(Query('', 'all', '', 0, 0))
        self.update_table(True)
    
    def del_query(self):    
        if self.stop_button.isEnabled():
            QMessageBox.warning(
                self, 
                'Error: The Checker is running',
                'Please first stop the Checker before making any changes to the table. You may accomplish this by clicking the large red button at the top of the window.', 
                QMessageBox.Ok
            )
            
            return

        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, 
                'Error: No Queries selected',
                'Please select a Query from the table.', 
                QMessageBox.Ok
            )
            return 

        # Get the ID of the query to delete
        id = self.rows[row].id
        
        # Grab the query
        db = DB(config.db_path)
        query = db.get_query(id)   
        
        # Only confirm the choice if the query string is not empty
        if len(query.query) != 0 or len(query.area) != 0:
            # Make sure that the user is sure
            ret = QMessageBox.question(
                self, 
                'Are you sure?',
                f'Are you sure that you want to delete query <b>#{row+1}</b> (<a href="{query.url()}">{query.url()}</a>)?', 
            )
            
            if ret != QMessageBox.Yes:
                return
            
        # Delete the query
        db.delete_query(id)
        self.update_table(True)

    def start_update(self):
        """
        Starts the updater thread
        """
    
        self.counter += 1

        # Update the progress bar status
        self.progress_bar.setRange(0, config.update_secs)
        self.progress_bar.setValue(self.counter)

        # Check if it's time to update or not
        if self.counter < config.update_secs:
            self.progress_bar.setFormat(f'Updating in {config.update_secs - self.counter} seconds')
            return
    
        try:
            self.update_timer.stop()
        except:
            pass
    
        logging.info('Starting update thread...')
        
        # Start the updater thread
        self.updater.start()
        
        # Alert the user that we are updating the update
        self.progress_bar.setFormat('Updating...')

    def finish_update(self, restart_timer=True):
        """
        Finishes the work that the updater thread started, mainly updating the UI
        """
    
        # Update the icon
        if self.updater.status == 'ok':
            self.tray.setIcon(self.icon)
        else:
            self.tray.setIcon(self.icon_error)

        # Check if any of the queries failed, and if so, mark them down
        for url, status in self.updater.query_statuses.items():
            if status == 'ok':
                self.failed_queries.discard(url)
            else:
                self.failed_queries.add(url)

        # Grab the list of new products
        total_products = self.updater.total_products
        
        # Find the total number of products found
        total_found = 0
        for id, products in total_products.items():
            total_found += len(products)
            self.found[id] = len(products)
        
        # Alert the user with a notification that new products have been found
        if total_found != 0:
            self.tray.showMessage('CL-Checker', f'{total_found} New Products Found!', self.icon, msecs=999999)
    
        # Open the database
        db = DB(config.db_path)
        play_alarm = False
        email_products = {}
        
        # Check if products were found with a query that had the alarm or email enabled
        for id, products in total_products.items():
            # Check if any products were found
            if len(products) == 0:
                continue
                
            # Grab the query and check if the alarm is enabled
            query = db.get_query(id)
            if query.alarm:
                play_alarm = True
   
            # Check if the query had email enabled, and if so add the products to the list to email
            if query.email:
                email_products[query.name()] = products
   
        # Play the alarm if we found any queries that had it enabled
        if play_alarm:
            QSound.play(os.path.join(os.path.dirname(__file__), 'alert.wav'))
    
        # Restart the update timer
        if restart_timer:
            self.start_update_timer()

        # Alert the user that the update has finished
        self.statusBar().showMessage('Finished update')
        self.updater.total_products = {}
        self.update_table(False)

        # Check if we need to send an email
        if email_products != {}:
            self.statusBar().showMessage('Sending email...')
            
            # Attempt to send the email
            if not send_email(email_products):
                self.statusBar().showMessage('Failed to send email')
                
                # Notify the user that the email failed to send
                QMessageBox.critical(
                    self, 
                    'Error: Email failed to send',
                    f'Error: Failed to send email to <a href="mailto:{config.to_email}">{config.to_email}</a>', 
                    QMessageBox.Ok
                )                
                
                return
            
            self.statusBar().showMessage('Email sent')

    def start_update_timer(self):
        """
        Starts the timer for the updater
        """
    
        # Stop the timer if it's already running
        try:
            self.update_timer.stop()
        except:
            pass
            
        # Start the timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.start_update)
        self.update_timer.setSingleShot(False)
        self.update_timer.start(1000)
        self.counter = 0

        self.progress_bar.setFormat(f'Updating in {config.update_secs} seconds')

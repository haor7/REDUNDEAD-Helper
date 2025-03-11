import sys
import os
import subprocess
import ctypes
import win32api
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QListWidget, 
                           QFileDialog, QProgressBar, QMessageBox, QDialog,
                           QRadioButton, QButtonGroup, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont

# Multi language
class Translations:
    """Language translation class"""
    
    def __init__(self):
        # Chinese
        self.zh = {
            "app_title": "REDundead数据恢复助手",
            "language_select": "请选择语言 / Please select language:",
            "language_zh": "中文",
            "language_en": "English",
            "confirm": "确认",
            "step1_title": "步骤1: 请选择需要恢复数据的驱动器",
            "step2_title": "步骤2: 请选择恢复数据的保存位置",
            "step3_title": "步骤3: 数据恢复进度",
            "refresh_drives": "刷新驱动器列表",
            "target_path": "目标路径:",
            "not_selected": "未选择",
            "browse": "浏览...",
            "ready_to_start": "准备开始恢复...",
            "back": "返回",
            "next": "下一步",
            "start_recovery": "开始恢复",
            "finish": "完成",
            "local_disk": "本地磁盘",
            "inaccessible": "不可访问",
            "select_folder": "选择目标文件夹",
            "warning": "警告",
            "select_drive": "请选择一个驱动器",
            "select_folder_warning": "请选择目标文件夹",
            "source_target_same": "目标路径不能在源驱动器上",
            "admin_required": "权限不足",
            "admin_message": "REDundead需要管理员权限才能运行。\n请右键点击本程序，选择'以管理员身份运行'。",
            "recovering": "正在从 {source} 恢复数据到 {target}\\RecoveryFolder...",
            "success": "成功",
            "error": "错误",
            "recovery_failed": "恢复失败: {message}",
            "log_output": "日志输出"
        }
        
        # English
        self.en = {
            "app_title": "REDundead Recovery Assistant",
            "language_select": "Please select language / 请选择语言:",
            "language_zh": "中文",
            "language_en": "English",
            "confirm": "Confirm",
            "step1_title": "Step 1: Select the drive to recover data from",
            "step2_title": "Step 2: Select destination location",
            "step3_title": "Step 3: Recovery progress",
            "refresh_drives": "Refresh Drives",
            "target_path": "Target path:",
            "not_selected": "Not selected",
            "browse": "Browse...",
            "ready_to_start": "Ready to start recovery...",
            "back": "Back",
            "next": "Next",
            "start_recovery": "Start Recovery",
            "finish": "Finish",
            "local_disk": "Local Disk",
            "inaccessible": "Inaccessible",
            "select_folder": "Select Destination Folder",
            "warning": "Warning",
            "select_drive": "Please select a drive",
            "select_folder_warning": "Please select a destination folder",
            "source_target_same": "Target path cannot be on source drive",
            "admin_required": "Admin Rights Required",
            "admin_message": "REDundead requires administrator privileges to run.\nPlease right-click the program and select 'Run as administrator'.",
            "recovering": "Recovering data from {source} to {target}\\RecoveryFolder...",
            "success": "Success",
            "error": "Error",
            "recovery_failed": "Recovery failed: {message}",
            "log_output": "Log output"
        }
        
        # Default is English
        self.current = self.en
    
    def set_language(self, lang):
        """Set the current language"""
        if lang == "zh":
            self.current = self.zh
        else:
            self.current = self.en
    
    def get(self, key):
        """Get translated text"""
        return self.current.get(key, key)


class LanguageDialog(QDialog):
    """Language selection dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_language = "en"  # Default English
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Language / 语言")
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout()
        
        # Title Tag
        label = QLabel("请选择语言 / Please select language:")
        layout.addWidget(label)
        
        # Radio Button
        self.radio_zh = QRadioButton("中文")
        self.radio_en = QRadioButton("English")
        self.radio_en.setChecked(True)
        
        # Add to button group
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.radio_zh, 1)
        self.button_group.addButton(self.radio_en, 2)
        
        layout.addWidget(self.radio_zh)
        layout.addWidget(self.radio_en)
        layout.addSpacing(10)
        
        # Confirm button
        confirm_button = QPushButton("确认 / Confirm")
        confirm_button.clicked.connect(self.confirm_language)
        layout.addWidget(confirm_button)
        
        self.setLayout(layout)
    
    def confirm_language(self):
        """Confirm language selection"""
        if self.radio_zh.isChecked():
            self.selected_language = "zh"
        else:
            self.selected_language = "en"
        self.accept()


class RecoveryWorker(QObject):
    """Background worker thread responsible for performing data recovery operations"""
    progress_update = pyqtSignal(int)
    log_update = pyqtSignal(str)
    operation_complete = pyqtSignal(bool, str)
    
    def __init__(self, source_drive, target_path):
        super().__init__()
        # source_drive is already in the correct format (such as "disk0").
        self.source_drive = source_drive  
        self.target_path = target_path
        
    def run(self):
        """Executes REDundead command and sends progress updates"""
        try:
            # Make sure the destination folder exists
            recovery_folder = os.path.join(self.target_path, "RecoveryFolder")
            if not os.path.exists(recovery_folder):
                os.makedirs(recovery_folder)
            
            # Directly use the obtained device identifier
            command = f'REDundead {self.source_drive} "{recovery_folder}"'
            self.log_update.emit(f"{command}")
            
            # Execute commands using subprocess
            process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Store output
            stdout_output = ""
            stderr_output = ""
            progress_value = 0
            
            # Non-blocking read output
            import time
            
            while True:
                # Check if the process has ended
                return_code = process.poll()
                
                # Try reading from stdout
                stdout_line = ""
                if process.stdout:
                    stdout_line = process.stdout.readline()
                    if stdout_line:
                        stdout_output += stdout_line
                        self.log_update.emit(f"{stdout_line.strip()}")
                        
                        # stdout_line can be parsed here to update the actual progress
                        # For example, if the output contains progress information
                
                # Try reading from stderr
                stderr_line = ""
                if process.stderr:
                    stderr_line = process.stderr.readline()
                    if stderr_line:
                        stderr_output += stderr_line
                        self.log_update.emit(f"Error: {stderr_line.strip()}")
                
                # Exit loop if process has ended and no more output
                if return_code is not None and not (stdout_line or stderr_line):
                    break
                    
                # Simulate progress update (0-95%)
                if progress_value < 95:
                    progress_value += 1
                    self.progress_update.emit(progress_value)
                
                time.sleep(0.1)  # Shorter delay for better responsiveness
            
            # Collect remaining output
            stdout_remainder, stderr_remainder = process.communicate()
            if stdout_remainder:
                stdout_output += stdout_remainder
                self.log_update.emit(f"Final output: {stdout_remainder.strip()}")
            if stderr_remainder:
                stderr_output += stderr_remainder
                self.log_update.emit(f"Final error: {stderr_remainder.strip()}")
            
            # Post-process after command completion
            # if return_code == 0:
            self.progress_update.emit(100)
            self.operation_complete.emit(True, "Success")
            # else:
            #     self.progress_update.emit(100)
            #     error_msg = stderr_output if stderr_output else f"Command execution failed, return code: {return_code}"
            #     self.log_update.emit(f"Process return code: {return_code}")
            #     self.operation_complete.emit(False, error_msg)
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.log_update.emit(f"Exception: {str(e)}\n{error_details}")
            self.operation_complete.emit(False, str(e))


class REDundeadGUI(QMainWindow):
    """Main window of REDundead Recovery Assistant"""
    
    def __init__(self):
        super().__init__()
        
        # Create translation object
        self.tr = Translations()
        
        # Show language selection dialog
        lang_dialog = LanguageDialog(self)
        if lang_dialog.exec_():
            self.tr.set_language(lang_dialog.selected_language)
        
        self.initUI()
        self.current_step = 1
        self.source_drive = None
        self.target_path = None
        self.recovery_worker = None
        self.recovery_thread = None
        
    def initUI(self):
        """Initialize UI"""
        self.setWindowTitle(self.tr.get("app_title"))
        self.setGeometry(300, 300, 600, 400)
        
        # Main window widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Step 1: Select source drive
        self.step1_widget = QWidget()
        self.step1_layout = QVBoxLayout(self.step1_widget)
        
        self.step1_label = QLabel(self.tr.get("step1_title"))
        self.step1_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.step1_layout.addWidget(self.step1_label)
        
        self.drive_list = QListWidget()
        self.step1_layout.addWidget(self.drive_list)
        self.refresh_drives()  # Populate drive list
        
        self.refresh_button = QPushButton(self.tr.get("refresh_drives"))
        self.refresh_button.clicked.connect(self.refresh_drives)
        self.step1_layout.addWidget(self.refresh_button)
        
        # Step 2: Select target path
        self.step2_widget = QWidget()
        self.step2_layout = QVBoxLayout(self.step2_widget)
        
        self.step2_label = QLabel(self.tr.get("step2_title"))
        self.step2_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.step2_layout.addWidget(self.step2_label)
        
        self.target_path_label = QLabel(self.tr.get("target_path"))
        self.step2_layout.addWidget(self.target_path_label)
        
        self.path_selection_layout = QHBoxLayout()
        self.selected_path_label = QLabel(self.tr.get("not_selected"))
        self.path_selection_layout.addWidget(self.selected_path_label, 1)
        
        self.browse_button = QPushButton(self.tr.get("browse"))
        self.browse_button.clicked.connect(self.browse_target_path)
        self.path_selection_layout.addWidget(self.browse_button)
        
        self.step2_layout.addLayout(self.path_selection_layout)
        
        # Step 3: Recovery progress
        self.step3_widget = QWidget()
        self.step3_layout = QVBoxLayout(self.step3_widget)

        self.step3_label = QLabel(self.tr.get("step3_title"))
        self.step3_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.step3_layout.addWidget(self.step3_label)

        self.recovery_info_label = QLabel(self.tr.get("ready_to_start"))
        self.step3_layout.addWidget(self.recovery_info_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.step3_layout.addWidget(self.progress_bar)

        # Add log output area
        self.log_label = QLabel(self.tr.get("log_output"))
        self.step3_layout.addWidget(self.log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(150)
        self.step3_layout.addWidget(self.log_text)

        # Navigation buttons
        self.nav_layout = QHBoxLayout()
        
        self.back_button = QPushButton(self.tr.get("back"))
        self.back_button.clicked.connect(self.go_back)
        self.nav_layout.addWidget(self.back_button)
        
        self.next_button = QPushButton(self.tr.get("next"))
        self.next_button.clicked.connect(self.go_next)
        self.nav_layout.addWidget(self.next_button)
        
        self.start_button = QPushButton(self.tr.get("start_recovery"))
        self.start_button.clicked.connect(self.start_recovery)
        self.start_button.setVisible(False)
        self.nav_layout.addWidget(self.start_button)
        
        self.finish_button = QPushButton(self.tr.get("finish"))
        self.finish_button.clicked.connect(self.close)
        self.finish_button.setVisible(False)
        self.nav_layout.addWidget(self.finish_button)
        
        self.main_layout.addLayout(self.nav_layout)
        
        # Initially show step 1
        self.main_layout.insertWidget(0, self.step1_widget)
        self.step2_widget.setVisible(False)
        self.step3_widget.setVisible(False)
        self.back_button.setEnabled(False)
        
    def refresh_drives(self):
        """Refresh available disk list"""
        self.drive_list.clear()
        disks = self.get_physical_disks()
        for disk in disks:
            self.drive_list.addItem(f"{disk['name']} - {disk['description']}")
    
    def get_physical_disks(self):
        """Get available physical disks using REDundead command"""
        disks = []
        try:
            # Use REDundead command directly to get device list
            result = subprocess.run(
                ['REDundead'], 
                capture_output=True, 
                text=True, 
                shell=True
            )
            
            output = result.stdout
            
            # Add output to log
            if hasattr(self, 'log_text'):
                self.log_text.append(f"REDundead device list output:\n{output}")
            
            # Parse output to get device list
            lines = output.strip().split('\n')
            device_section_started = False
            
            for line in lines:
                # Find device list header line
                if "Device    Size       Name" in line:
                    device_section_started = True
                    continue
                    
                # Start parsing device list section
                if device_section_started and line.strip():
                    # Check if there is a device identifier starting with "disk"
                    parts = line.strip().split()
                    if parts and parts[0].startswith('disk'):
                        # Extract device information
                        device_id = parts[0]  # e.g. 'disk0'
                        size = parts[1] + " " + parts[2]  # e.g. '954 GB'
                        
                        # Names may contain spaces and require special handling
                        name_parts = parts[3:]
                        device_name = ' '.join(name_parts)
                        
                        # Create disk dictionary and add to list
                        disk = {
                            'name': device_id,
                            'description': f"{size} - {device_name}"
                        }
                        disks.append(disk)
            
            # Fallback if no devices found
            if not disks:
                error_msg = "Failed to parse device list from REDundead output"
                print(error_msg)
                if hasattr(self, 'log_text'):
                    self.log_text.append(error_msg)
                    self.log_text.append("Attempting to use fallback method")
                
                # Use an alternate method to obtain disk information
                return self.get_physical_disks_fallback()
                
        except Exception as e:
            error_msg = f"Error executing REDundead command: {str(e)}"
            print(error_msg)
            if hasattr(self, 'log_text'):
                self.log_text.append(error_msg)
                self.log_text.append("Using fallback method")
            
            # Fallback method when errors occur
            return self.get_physical_disks_fallback()
        
        return disks

    def get_physical_disks_fallback(self):
        """Fallback method: Get physical disk info using wmic command"""
        disks = []
        try:
            # Use wmic command to obtain physical disk information
            result = subprocess.run(
                ['wmic', 'diskdrive', 'get', 'index,caption,size'], 
                capture_output=True, text=True, shell=True
            )
            
            lines = result.stdout.strip().split('\n')
            # Skip header row
            for line in lines[1:]:
                parts = line.strip().split()
                if not parts:
                    continue
                
                try:
                    index = parts[0]
                    if index.isdigit():
                        # Concatenate the rest as a description
                        description = ' '.join(parts[1:])
                        
                        # Create Disk Item
                        disk = {
                            'name': f"disk{index}",
                            'description': description
                        }
                        disks.append(disk)
                except:
                    pass
        except Exception as e:
            error_msg = f"Fallback method error: {e}"
            print(error_msg)
            if hasattr(self, 'log_text'):
                self.log_text.append(error_msg)
        
        return disks
    
    def browse_target_path(self):
        """Open dialog to select target path"""
        folder = QFileDialog.getExistingDirectory(self, self.tr.get("select_folder"))
        if folder:
            self.target_path = folder
            self.selected_path_label.setText(folder)
    
    def go_back(self):
        """Navigate to previous step"""
        if self.current_step == 2:
            self.step2_widget.setVisible(False)
            self.main_layout.insertWidget(0, self.step1_widget)
            self.step1_widget.setVisible(True)
            self.current_step = 1
            self.back_button.setEnabled(False)
            self.next_button.setText(self.tr.get("next"))
            self.next_button.setEnabled(True)
            self.start_button.setVisible(False)
        elif self.current_step == 3:
            self.step3_widget.setVisible(False)
            self.main_layout.insertWidget(0, self.step2_widget)
            self.step2_widget.setVisible(True)
            self.current_step = 2
            self.back_button.setEnabled(True)
            self.next_button.setVisible(True)
            self.start_button.setVisible(True)
            self.finish_button.setVisible(False)

    def go_next(self):
        """Navigate to next step"""
        if self.current_step == 1:
            # From step 1 to step 2
            if not self.drive_list.currentItem():
                QMessageBox.warning(self, self.tr.get("warning"), self.tr.get("select_drive"))
                return
                
            selected_drive = self.drive_list.currentItem().text().split(" - ")[0]
            self.source_drive = selected_drive
            
            self.step1_widget.setVisible(False)
            self.main_layout.insertWidget(0, self.step2_widget)
            self.step2_widget.setVisible(True)
            self.current_step = 2
            self.back_button.setEnabled(True)
            self.next_button.setText(self.tr.get("next"))
            self.start_button.setVisible(False)
            
        elif self.current_step == 2:
            # From step 2 to step 3
            if not self.target_path:
                QMessageBox.warning(self, self.tr.get("warning"), self.tr.get("select_folder_warning"))
                return
                
            # Check that the destination path is not on the source drive
            if self.target_path.startswith(self.source_drive):
                QMessageBox.warning(self, self.tr.get("warning"), self.tr.get("source_target_same"))
                return
                
            self.step2_widget.setVisible(False)
            self.main_layout.insertWidget(0, self.step3_widget)
            self.step3_widget.setVisible(True)
            self.current_step = 3
            self.back_button.setEnabled(True)
            self.next_button.setVisible(False)
            self.start_button.setVisible(True)
    
    def is_admin(self):
        """Check if running with admin privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def start_recovery(self):
        """Start data recovery process"""
        # Check administrator rights
        if not self.is_admin():
            QMessageBox.warning(
                self, 
                self.tr.get("admin_required"), 
                self.tr.get("admin_message")
            )
            return
            
        # Disable navigation buttons
        self.back_button.setEnabled(False)
        self.start_button.setEnabled(False)
        
        # Clear log
        self.log_text.clear()
        
        # Update UI
        self.recovery_info_label.setText(
            self.tr.get("recovering").format(source=self.source_drive, target=self.target_path)
        )
        
        # Create recovery worker thread
        self.recovery_worker = RecoveryWorker(self.source_drive, self.target_path)
        self.recovery_worker.progress_update.connect(self.update_progress)
        self.recovery_worker.log_update.connect(self.update_log)  # Connection log update signal
        self.recovery_worker.operation_complete.connect(self.recovery_finished)
        
        # Corrected progress bar value
        self.recovery_worker.progress_bar_value = 0
        
        # Starting a Thread
        self.recovery_thread = threading.Thread(target=self.recovery_worker.run)
        self.recovery_thread.daemon = True  # Make sure the thread exits when the main program exits
        self.recovery_thread.start()

    # Add a new method to update the log
    def update_log(self, message):
        """Changelog text box"""
        self.log_text.append(message)
        # Scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
    
    def recovery_finished(self, success, message):
        """Handle recovery completion"""
        if success:
            self.recovery_info_label.setText(message)
            QMessageBox.information(self, self.tr.get("success"), message)
        else:
            self.recovery_info_label.setText(self.tr.get("recovery_failed").format(message=message))
            QMessageBox.critical(self, self.tr.get("error"), message)
        
        # Update IO
        self.finish_button.setVisible(True)
        self.start_button.setVisible(False)
        self.back_button.setEnabled(True)


if __name__ == "__main__":
    # Restart with admin rights if needed
    if not ctypes.windll.shell32.IsUserAnAdmin():
        # Try restarting as an administrator
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()
        except:
            # UAC
            pass
    
    app = QApplication(sys.argv)
    ex = REDundeadGUI()
    ex.show()
    sys.exit(app.exec_())
import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTextEdit, QTabWidget,
    QAction, QMessageBox, QToolBar, QStatusBar, QLabel, QComboBox, QInputDialog
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt

SUPPORTED_EXTENSIONS = {
    ".py": "Python",
    ".bat": "Batch",
    ".ps1": "PowerShell"
}

class ScriptTab(QTextEdit):
    def __init__(self, file_path=None):
        super().__init__()
        self.file_path = file_path
        self.setFont(QFont("Consolas", 12))
        self.setWordWrapMode(False)
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                self.setText(f.read())

    def save(self):
        if not self.file_path:
            self.file_path, _ = QFileDialog.getSaveFileName(self, "Save Script", "", "All Files (*)")
        if self.file_path:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(self.toPlainText())
            return True
        return False

class ScriptEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows Script Editor")
        self.resize(900, 700)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.language_label = QLabel("Language: ")
        self.status.addPermanentWidget(self.language_label)
        self.init_toolbar()
        self.tabs.currentChanged.connect(self.update_status)

    def init_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(Qt.QSize(24, 24))
        self.addToolBar(toolbar)
        # File actions
        open_action = QAction(QIcon.fromTheme("document-open"), "Open", self)
        open_action.triggered.connect(self.open_file)
        save_action = QAction(QIcon.fromTheme("document-save"), "Save", self)
        save_action.triggered.connect(self.save_file)
        new_action = QAction(QIcon.fromTheme("document-new"), "New", self)
        new_action.triggered.connect(self.new_file)
        close_action = QAction(QIcon.fromTheme("window-close"), "Close Tab", self)
        close_action.triggered.connect(self.close_tab)
        toolbar.addAction(open_action)
        toolbar.addAction(save_action)
        toolbar.addAction(new_action)
        toolbar.addAction(close_action)
        toolbar.addSeparator()
        # Edit actions
        undo_action = QAction(QIcon.fromTheme("edit-undo"), "Undo", self)
        undo_action.triggered.connect(lambda: self.current_tab().undo())
        redo_action = QAction(QIcon.fromTheme("edit-redo"), "Redo", self)
        redo_action.triggered.connect(lambda: self.current_tab().redo())
        cut_action = QAction(QIcon.fromTheme("edit-cut"), "Cut", self)
        cut_action.triggered.connect(lambda: self.current_tab().cut())
        copy_action = QAction(QIcon.fromTheme("edit-copy"), "Copy", self)
        copy_action.triggered.connect(lambda: self.current_tab().copy())
        paste_action = QAction(QIcon.fromTheme("edit-paste"), "Paste", self)
        paste_action.triggered.connect(lambda: self.current_tab().paste())
        find_action = QAction(QIcon.fromTheme("edit-find"), "Find", self)
        find_action.triggered.connect(self.find_text)
        toolbar.addAction(undo_action)
        toolbar.addAction(redo_action)
        toolbar.addAction(cut_action)
        toolbar.addAction(copy_action)
        toolbar.addAction(paste_action)
        toolbar.addAction(find_action)
        toolbar.addSeparator()
        # Execute
        run_action = QAction(QIcon.fromTheme("system-run"), "Run Script", self)
        run_action.triggered.connect(self.run_script)
        toolbar.addAction(run_action)
        # Language selection
        self.language_combo = QComboBox()
        self.language_combo.addItems(list(SUPPORTED_EXTENSIONS.values()))
        self.language_combo.currentTextChanged.connect(self.change_language)
        toolbar.addWidget(self.language_combo)

    def current_tab(self):
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, ScriptTab) else None

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Script", "", "All Files (*);;Python (*.py);;Batch (*.bat);;PowerShell (*.ps1)")
        if file_path:
            ext = os.path.splitext(file_path)[1]
            tab = ScriptTab(file_path)
            self.tabs.addTab(tab, os.path.basename(file_path))
            self.tabs.setCurrentWidget(tab)
            self.language_label.setText(f"Language: {SUPPORTED_EXTENSIONS.get(ext, 'Unknown')}")

    def save_file(self):
        tab = self.current_tab()
        if tab and tab.save():
            self.status.showMessage("File saved!", 3000)

    def new_file(self):
        lang = self.language_combo.currentText()
        ext = next(k for k, v in SUPPORTED_EXTENSIONS.items() if v == lang)
        file_path, _ = QFileDialog.getSaveFileName(self, "New Script", f"untitled{ext}", f"{lang} (*{ext})")
        if file_path:
            tab = ScriptTab(file_path)
            tab.setText("")  # Start empty
            self.tabs.addTab(tab, os.path.basename(file_path))
            self.tabs.setCurrentWidget(tab)
            self.language_label.setText(f"Language: {lang}")

    def close_tab(self):
        idx = self.tabs.currentIndex()
        if idx >= 0:
            self.tabs.removeTab(idx)

    def find_text(self):
        tab = self.current_tab()
        if not tab:
            return
        text, ok = QInputDialog.getText(self, "Find Text", "Enter the text to find:")
        if ok and text:
            result = tab.find(text)
            if not result:
                QMessageBox.information(self, "Find", "Text not found!")

    def change_language(self, lang):
        self.language_label.setText(f"Language: {lang}")

    def run_script(self):
        tab = self.current_tab()
        if not tab or not tab.file_path:
            QMessageBox.warning(self, "Run Script", "You must save your script before running it!")
            return
        ext = os.path.splitext(tab.file_path)[1]
        if ext == ".py":
            cmd = ["python", tab.file_path]
        elif ext == ".bat":
            cmd = ["cmd.exe", "/c", tab.file_path]
        elif ext == ".ps1":
            cmd = ["powershell", "-File", tab.file_path]
        else:
            QMessageBox.warning(self, "Run Script", "Unsupported script type!")
            return
        tab.save()  # Save before running
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, shell=True)
            QMessageBox.information(self, "Execution Output", output)
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(self, "Execution Error", e.output)

    def update_status(self):
        tab = self.current_tab()
        if tab and tab.file_path:
            ext = os.path.splitext(tab.file_path)[1]
            self.language_label.setText(f"Language: {SUPPORTED_EXTENSIONS.get(ext, 'Unknown')}")
        else:
            self.language_label.setText("Language: ")

def main():
    app = QApplication(sys.argv)
    editor = ScriptEditor()
    editor.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

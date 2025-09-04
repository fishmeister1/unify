import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QDockWidget, QTextEdit, QTabWidget,
    QAction, QMessageBox, QToolBar, QStatusBar, QLabel, QComboBox, QInputDialog,
    QTreeView, QFileSystemModel, QWidget, QHBoxLayout, QVBoxLayout
)
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette
from PyQt5.QtCore import Qt, QProcess

# Optional: QScintilla for syntax highlighting
try:
    from PyQt5.Qsci import QsciScintilla, QsciLexerPython, QsciLexerBatch, QsciLexerPowerShell
    USE_QSCINTILLA = True
except ImportError:
    USE_QSCINTILLA = False

# Optional: Jedi for Python completion
try:
    import jedi
    USE_JEDI = True
except ImportError:
    USE_JEDI = False

SUPPORTED_EXTENSIONS = {
    ".py": "Python",
    ".bat": "Batch",
    ".ps1": "PowerShell"
}

LEXERS = {
    "Python": QsciLexerPython if USE_QSCINTILLA else None,
    "Batch": QsciLexerBatch if USE_QSCINTILLA else None,
    "PowerShell": QsciLexerPowerShell if USE_QSCINTILLA else None
}

class ScriptTab(QsciScintilla if USE_QSCINTILLA else QTextEdit):
    def __init__(self, file_path=None):
        super().__init__()
        self.file_path = file_path
        self.setFont(QFont("Consolas", 12))
        if USE_QSCINTILLA:
            self.setUtf8(True)
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                if USE_QSCINTILLA:
                    self.setText(text)
                else:
                    self.setText(text)
            self.set_lexer_by_extension(file_path)
    
    def set_lexer_by_extension(self, file_path):
        if not USE_QSCINTILLA:
            return
        ext = os.path.splitext(file_path)[1]
        lang = SUPPORTED_EXTENSIONS.get(ext)
        lexer_cls = LEXERS.get(lang)
        if lexer_cls:
            lexer = lexer_cls()
            lexer.setDefaultFont(QFont("Consolas", 12))
            self.setLexer(lexer)

    def save(self):
        if not self.file_path:
            self.file_path, _ = QFileDialog.getSaveFileName(self, "Save Script", "", "All Files (*)")
        if self.file_path:
            text = self.text() if USE_QSCINTILLA else self.toPlainText()
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(text)
            return True
        return False

class TerminalWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.process = QProcess()
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.input = QTextEdit()
        self.input.setMaximumHeight(40)
        self.input.keyPressEvent = self.handle_keypress
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Terminal"))
        layout.addWidget(self.output)
        layout.addWidget(self.input)
        self.setLayout(layout)
        self.process.readyReadStandardOutput.connect(self.on_stdout)
        self.process.readyReadStandardError.connect(self.on_stderr)

    def handle_keypress(self, event):
        if event.key() == Qt.Key_Return:
            command = self.input.toPlainText().strip()
            self.input.clear()
            if command:
                self.process.write((command + "\n").encode('utf-8'))

    def start(self, shell="cmd.exe"):
        self.process.start(shell)

    def on_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.output.append(data)

    def on_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.output.append(data)

class ExplorerDock(QDockWidget):
    def __init__(self, root_path):
        super().__init__("File Explorer")
        self.tree = QTreeView()
        self.model = QFileSystemModel()
        self.model.setRootPath(root_path)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(root_path))
        self.setWidget(self.tree)

class ScriptEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows Script Editor - Advanced")
        self.resize(1100, 800)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.language_label = QLabel("Language: ")
        self.status.addPermanentWidget(self.language_label)
        self.init_toolbar()
        self.init_explorer()
        self.init_terminal()
        self.init_theme()
        self.tabs.currentChanged.connect(self.update_status)

    def init_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(Qt.QSize(24, 24))
        self.addToolBar(toolbar)
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
        run_action = QAction(QIcon.fromTheme("system-run"), "Run Script", self)
        run_action.triggered.connect(self.run_script)
        toolbar.addAction(run_action)
        self.language_combo = QComboBox()
        self.language_combo.addItems(list(SUPPORTED_EXTENSIONS.values()))
        self.language_combo.currentTextChanged.connect(self.change_language)
        toolbar.addWidget(self.language_combo)
        theme_action = QAction("Toggle Theme", self)
        theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(theme_action)

    def init_explorer(self):
        cwd = os.getcwd()
        self.explorer = ExplorerDock(cwd)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.explorer)
        self.explorer.tree.doubleClicked.connect(self.load_file_from_explorer)

    def init_terminal(self):
        self.terminal = TerminalWidget()
        dock = QDockWidget("Terminal")
        dock.setWidget(self.terminal)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock)
        self.terminal.start()

    def init_theme(self):
        self.dark_mode = False
        self.set_light_palette()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.set_dark_palette()
        else:
            self.set_light_palette()

    def set_light_palette(self):
        app = QApplication.instance()
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, Qt.black)
        palette.setColor(QPalette.Base, Qt.white)
        palette.setColor(QPalette.Text, Qt.black)
        app.setPalette(palette)

    def set_dark_palette(self):
        app = QApplication.instance()
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.Text, Qt.white)
        app.setPalette(palette)

    def current_tab(self):
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, ScriptTab) else None

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Script", "", "All Files (*)")
        if file_path:
            tab = ScriptTab(file_path)
            self.tabs.addTab(tab, os.path.basename(file_path))
            self.tabs.setCurrentWidget(tab)
            tab.set_lexer_by_extension(file_path)
            self.language_label.setText(f"Language: {self.detect_language(file_path)}")

    def load_file_from_explorer(self, index):
        file_path = self.explorer.model.filePath(index)
        if os.path.isfile(file_path):
            tab = ScriptTab(file_path)
            self.tabs.addTab(tab, os.path.basename(file_path))
            self.tabs.setCurrentWidget(tab)
            tab.set_lexer_by_extension(file_path)
            self.language_label.setText(f"Language: {self.detect_language(file_path)}")

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
            tab.set_lexer_by_extension(file_path)
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
            if USE_QSCINTILLA:
                pos = tab.findFirst(text, False, False, False, True)
                if not pos:
                    QMessageBox.information(self, "Find", "Text not found!")
            else:
                result = tab.find(text)
                if not result:
                    QMessageBox.information(self, "Find", "Text not found!")

    def change_language(self, lang):
        self.language_label.setText(f"Language: {lang}")

    def detect_language(self, file_path):
        ext = os.path.splitext(file_path)[1]
        return SUPPORTED_EXTENSIONS.get(ext, 'Unknown')

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
            self.language_label.setText(f"Language: {self.detect_language(tab.file_path)}")
        else:
            self.language_label.setText("Language: ")

def main():
    app = QApplication(sys.argv)
    editor = ScriptEditor()
    editor.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
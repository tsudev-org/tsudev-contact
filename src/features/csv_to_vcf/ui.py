# -*- coding: utf-8 -*-
"""Cửa sổ chính: chọn file, ánh xạ cột CSV ↔ trường vCard, chạy chuyển đổi."""
import os
import queue
import threading
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import ttk, filedialog, messagebox

from src.app_info import APP_NAME, APP_VERSION, APP_AUTHOR, SUPPORT_URL
from src.features.csv_to_vcf import converter
from src.features.csv_to_vcf.converter import SKIP_OPTION, VCARD_FIELDS
from src.features.preview.ui import PreviewWindow
from src.services import settings
from src.services.database import DatabaseManager
from src.services.tokens import loadTokens

MAPPING_COLUMNS = 3          # số cột lưới của khu vực ghép nối
IMPORT_PROGRESS_SHARE = 80   # % tiến trình dành cho giai đoạn nạp CSV
LOG_HEIGHT_ROWS = 5
UI_QUEUE_POLL_MS = 30        # nhịp main thread lấy việc do thread nền gửi lên


class ContactsApp:
    def __init__(self, root, iconPhoto):
        self.root = root
        self.iconPhoto = iconPhoto
        self.tokens = loadTokens(settings.loadSettings()['theme'])
        self.db = DatabaseManager()
        self.lastSavedFolder = None
        self.previewColumns = {}
        self.uiQueue = queue.Queue()
        self.uiPumpJobId = None

        self.root.title(f"{APP_NAME} - Chuyển đổi CSV sang vCard (v{APP_VERSION})")
        if self.iconPhoto:
            try:
                self.root.iconphoto(True, self.iconPhoto)
            except tk.TclError:
                pass

        self._configureStyles()
        self._createMenu()
        self._createWidgets()
        self._pumpUiQueue()
        self.root.bind('<Destroy>', self._onRootDestroyed, add='+')

    # ------------------------------------------------------------------ style
    def _configureStyles(self):
        t = self.tokens
        self.style = getattr(self, 'style', None) or ttk.Style(self.root)
        # 'vista' vẽ widget theo native Windows (đẹp nhưng bỏ qua màu nền) - chỉ hợp chủ đề
        # sáng. Chủ đề ấm/tối cần đổi nền nên phải dùng 'clam' (tôn trọng mọi màu).
        for themeName in (('vista', 'clam') if t.theme == 'light' else ('clam',)):
            try:
                self.style.theme_use(themeName)
                break
            except tk.TclError:
                continue

        bg = t.color('bg-base')
        self.root.configure(bg=bg)
        self.style.configure('TLabel', font=t.font(), background=bg,
                             foreground=t.color('text-primary'))
        self.style.configure('TButton', font=t.font(weightName='semibold'),
                             padding=t.space(2))
        self.style.configure('TFrame', background=bg)
        self.style.configure('TLabelframe', padding=t.space(3), background=bg)
        self.style.configure('TLabelframe.Label', font=t.font('body-desktop-lg', 'semibold'),
                             foreground=t.color('primary'), background=bg)
        self.style.configure('Link.TLabel', font=t.font('sm', underline=True),
                             foreground=t.color('text-link'), background=bg)
        self.style.configure('Watermark.TLabel', font=t.font('sm', slant='italic'),
                             foreground=t.color('text-muted'), background=bg)
        self.style.configure('Muted.TLabel', font=t.font('sm'),
                             foreground=t.color('text-secondary'), background=bg)
        self.style.configure('Required.TLabel', font=t.font(weightName='semibold'),
                             foreground=t.color('danger'), background=bg)
        self.style.configure('Success.Horizontal.TProgressbar', background=t.color('success'))
        if self.style.theme_use() != 'vista':
            self._configureNonNativeStyles()

    def _configureNonNativeStyles(self):
        """Theme 'clam' không vẽ theo native nên phải tô màu từng nhóm widget từ tokens."""
        t = self.tokens
        surface, text = t.color('bg-surface'), t.color('text-primary')
        self.style.configure('TButton', background=surface, foreground=text,
                             bordercolor=t.color('border'), focuscolor=t.color('focus-ring'),
                             lightcolor=surface, darkcolor=surface)
        self.style.map('TButton',
                       background=[('active', t.color('bg-hover')),
                                   ('disabled', t.color('bg-subtle'))],
                       foreground=[('disabled', t.color('text-muted'))])
        self.style.configure('TEntry', fieldbackground=surface, foreground=text,
                             bordercolor=t.color('border'), insertcolor=text)
        self.style.configure('TCombobox', fieldbackground=surface, background=surface,
                             foreground=text, arrowcolor=t.color('text-secondary'),
                             bordercolor=t.color('border'))
        self.style.map('TCombobox', fieldbackground=[('readonly', surface)],
                       foreground=[('readonly', text)])
        # Danh sách thả xuống của Combobox là widget Tk cổ điển, chỉ đổi màu qua option database
        for option, value in (('background', surface), ('foreground', text),
                              ('selectBackground', t.color('primary')),
                              ('selectForeground', t.color('on-primary'))):
            self.root.option_add(f'*TCombobox*Listbox.{option}', value)
        for progressStyle in ('TProgressbar', 'Horizontal.TProgressbar',
                              'Success.Horizontal.TProgressbar'):
            self.style.configure(progressStyle, troughcolor=t.color('bg-subtle'),
                                 bordercolor=t.color('border'), lightcolor=t.color('bg-subtle'),
                                 darkcolor=t.color('bg-subtle'))
        self.style.configure('Success.Horizontal.TProgressbar', background=t.color('success'))
        self.style.configure('Treeview', background=surface, fieldbackground=surface,
                             foreground=text, bordercolor=t.color('border'))
        self.style.configure('Treeview.Heading', background=t.color('bg-subtle'),
                             foreground=text)
        self.style.map('Treeview', background=[('selected', t.color('primary'))],
                       foreground=[('selected', t.color('on-primary'))])
        self.style.configure('TScrollbar', background=t.color('bg-subtle'),
                             troughcolor=t.color('bg-base'),
                             bordercolor=t.color('border'),
                             arrowcolor=t.color('text-secondary'))
        self.style.configure('TLabelframe', bordercolor=t.color('border'))

    # ------------------------------------------------------------------ chủ đề
    def _applyTheme(self, themeName: str):
        """Đổi chủ đề giao diện lúc chạy và ghi nhớ lựa chọn cho lần mở sau."""
        self.tokens = loadTokens(themeName)
        settings.saveSetting('theme', themeName)
        self._configureStyles()
        self._restyleClassicWidgets()

    def _restyleClassicWidgets(self):
        """Widget Tk cổ điển (không phải ttk) không theo Style - phải tô lại thủ công."""
        t = self.tokens
        self.convertButton.config(bg=t.color('primary'), fg=t.color('on-primary'),
                                  activebackground=t.color('primary-hover'),
                                  activeforeground=t.color('on-primary'),
                                  disabledforeground=t.color('text-muted'))
        self.statusLog.config(bg=t.color('bg-surface'), fg=t.color('text-primary'),
                              insertbackground=t.color('text-primary'))
        self.statusLog.tag_configure("success", foreground=t.color('success'))
        self.statusLog.tag_configure("error", foreground=t.color('danger'),
                                     font=t.font('sm', 'semibold', mono=True))

    # ------------------------------------------------------------------- menu
    def _createMenu(self):
        menuBar = tk.Menu(self.root)
        self.root.config(menu=menuBar)

        fileMenu = tk.Menu(menuBar, tearoff=0)
        menuBar.add_cascade(label="Tệp", menu=fileMenu)
        fileMenu.add_command(label="Chọn file CSV...", command=self._browseCsv, accelerator="Ctrl+O")
        fileMenu.add_command(label="Chọn nơi lưu VCF...", command=self._browseVcf, accelerator="Ctrl+S")
        fileMenu.add_separator()
        fileMenu.add_command(label="Thoát", command=self.root.quit)

        self.themeVar = tk.StringVar(value=self.tokens.theme)
        themeMenu = tk.Menu(menuBar, tearoff=0)
        menuBar.add_cascade(label="Giao diện", menu=themeMenu)
        for themeName in settings.THEMES:
            themeMenu.add_radiobutton(
                label=settings.THEME_LABELS[themeName], value=themeName, variable=self.themeVar,
                command=lambda name=themeName: self._applyTheme(name))

        helpMenu = tk.Menu(menuBar, tearoff=0)
        menuBar.add_cascade(label="Trợ giúp", menu=helpMenu)
        helpMenu.add_command(label="Về ứng dụng", command=self._showAboutDialog, accelerator="F1")

        self.root.bind("<Control-o>", lambda e: self._browseCsv())
        self.root.bind("<Control-s>", lambda e: self._browseVcf())
        self.root.bind("<F1>", lambda e: self._showAboutDialog())

    # ---------------------------------------------------------------- widgets
    def _createWidgets(self):
        t = self.tokens
        mainFrame = ttk.Frame(self.root, padding=t.space(5))
        mainFrame.pack(fill=tk.BOTH, expand=True)
        mainFrame.columnconfigure(0, weight=1)

        fileFrame = ttk.LabelFrame(mainFrame, text="Bước 1: Chọn File Nguồn và Đích")
        fileFrame.grid(row=0, column=0, sticky="ew", pady=(0, t.space(3)))
        fileFrame.columnconfigure(1, weight=1)

        ttk.Label(fileFrame, text="File CSV:").grid(row=0, column=0, sticky="w",
                                                   padx=t.space(1), pady=t.space(1))
        self.csvPathVar = tk.StringVar()
        ttk.Entry(fileFrame, textvariable=self.csvPathVar, state='readonly').grid(
            row=0, column=1, sticky="ew", padx=t.space(1))
        ttk.Button(fileFrame, text="Chọn...", command=self._browseCsv).grid(
            row=0, column=2, padx=t.space(1))

        ttk.Label(fileFrame, text="Lưu VCF:").grid(row=1, column=0, sticky="w",
                                                  padx=t.space(1), pady=t.space(1))
        self.vcfPathVar = tk.StringVar()
        ttk.Entry(fileFrame, textvariable=self.vcfPathVar, state='readonly').grid(
            row=1, column=1, sticky="ew", padx=t.space(1))
        ttk.Button(fileFrame, text="Lưu tại...", command=self._browseVcf).grid(
            row=1, column=2, padx=t.space(1))

        self.mappingFrame = ttk.LabelFrame(mainFrame, text="Bước 2: Ghép Nối Dữ Liệu")
        self.mappingFrame.grid(row=1, column=0, sticky="ew", pady=t.space(3))
        self.mappingFrame.columnconfigure(tuple(range(MAPPING_COLUMNS)), weight=1)
        self.fieldMappings = {}
        self._createFieldMappingWidgets()

        actionFrame = ttk.Frame(mainFrame)
        actionFrame.grid(row=2, column=0, pady=t.space(4))
        # Dùng tk.Button (không phải ttk): theme 'vista' bỏ qua -background nên nút ttk
        # sẽ hiện chữ trắng trên nền trắng khi có focus. Màu vẫn lấy từ tokens.
        self.convertButton = tk.Button(actionFrame, text="BẮT ĐẦU CHUYỂN ĐỔI",
                                       command=self._startConversion,
                                       font=t.font(weightName='semibold'),
                                       bg=t.color('primary'), fg=t.color('on-primary'),
                                       activebackground=t.color('primary-hover'),
                                       activeforeground=t.color('on-primary'),
                                       disabledforeground=t.color('text-muted'),
                                       relief=tk.FLAT, borderwidth=0, cursor='hand2',
                                       padx=t.space(5), pady=t.space(3))
        self.convertButton.pack()

        self.statusText = tk.StringVar(value="Chưa chọn file CSV")
        ttk.Label(mainFrame, textvariable=self.statusText, style='Muted.TLabel').grid(
            row=3, column=0, sticky="ew", pady=(0, t.space(1)))
        self.progress = ttk.Progressbar(mainFrame, orient="horizontal", mode="determinate")
        self.progress.grid(row=4, column=0, sticky="ew")

        logContainer = ttk.LabelFrame(mainFrame, text="Nhật Ký Chuyển Đổi")
        logContainer.grid(row=5, column=0, sticky="nsew", pady=(t.space(3), 0))
        logContainer.columnconfigure(0, weight=1)
        logContainer.rowconfigure(0, weight=1)
        mainFrame.rowconfigure(5, weight=1)
        # Text + ttk.Scrollbar thay cho ScrolledText: thanh cuộn cổ điển của Tk được Windows
        # vẽ native nên không đổi màu theo chủ đề, còn ttk.Scrollbar thì theo Style.
        self.statusLog = tk.Text(
            logContainer, height=LOG_HEIGHT_ROWS, font=t.font('sm', mono=True),
            wrap=tk.WORD, relief=tk.SOLID, borderwidth=1, state="disabled",
            bg=t.color('bg-surface'), fg=t.color('text-primary'),
            insertbackground=t.color('text-primary'))
        self.statusLog.grid(row=0, column=0, sticky="nsew")
        logScroll = ttk.Scrollbar(logContainer, orient="vertical", command=self.statusLog.yview)
        logScroll.grid(row=0, column=1, sticky="ns")
        self.statusLog.configure(yscrollcommand=logScroll.set)
        self.statusLog.tag_configure("success", foreground=t.color('success'))
        self.statusLog.tag_configure("error", foreground=t.color('danger'),
                                     font=t.font('sm', 'semibold', mono=True))

        bottomFrame = ttk.Frame(mainFrame)
        bottomFrame.grid(row=6, column=0, sticky="ew", pady=(t.space(3), 0))
        self.openFolderButton = ttk.Button(bottomFrame, text="Mở thư mục",
                                           command=self._openSavedFolder, state="disabled")
        self.openFolderButton.pack(side=tk.LEFT)
        self.previewButton = ttk.Button(bottomFrame, text="Xem thử Danh bạ",
                                        command=self._showPreviewDialog, state="disabled")
        self.previewButton.pack(side=tk.LEFT, padx=t.space(1))

        authorFrame = ttk.Frame(bottomFrame)
        authorFrame.pack(side=tk.RIGHT)
        ttk.Label(authorFrame, text=APP_AUTHOR, style='Watermark.TLabel').pack(anchor='e')
        supportLabel = ttk.Label(authorFrame, text="contact.tsudev.com",
                                 style='Link.TLabel', cursor="hand2")
        supportLabel.pack(anchor='e')
        supportLabel.bind("<Button-1>", lambda e: webbrowser.open_new(SUPPORT_URL))
        self._restyleClassicWidgets()

    def _createFieldMappingWidgets(self, headers=None):
        t = self.tokens
        headers = headers or []
        for widget in self.mappingFrame.winfo_children():
            widget.destroy()
        options = [SKIP_OPTION] + headers

        for i, (field, labelText) in enumerate(VCARD_FIELDS.items()):
            row, col = divmod(i, MAPPING_COLUMNS)
            fieldFrame = ttk.Frame(self.mappingFrame)
            fieldFrame.grid(row=row, column=col, padx=t.space(1), pady=t.space(1), sticky='ew')

            if '*' in labelText:
                labelContainer = ttk.Frame(fieldFrame)
                labelContainer.pack(side=tk.LEFT, padx=(0, t.space(1)))
                ttk.Label(labelContainer, text=labelText.replace('*', '')).pack(side=tk.LEFT)
                ttk.Label(labelContainer, text='*', style='Required.TLabel').pack(side=tk.LEFT)
            else:
                ttk.Label(fieldFrame, text=labelText).pack(side=tk.LEFT, padx=(0, t.space(1)))

            combo = ttk.Combobox(fieldFrame, values=options, state='readonly', width=15)
            combo.pack(side=tk.LEFT, expand=True, fill=tk.X)
            combo.set(converter.guessHeader(field, headers, options[0]))
            self.fieldMappings[field] = combo

    # ------------------------------------------------------------------ hành động
    def _browseCsv(self):
        filepath = filedialog.askopenfilename(
            title="Chọn file danh bạ CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not filepath:
            return
        self.csvPathVar.set(filepath)
        self.vcfPathVar.set(os.path.splitext(filepath)[0] + '.vcf')
        self._logMessage(f"Đã chọn file CSV: {os.path.basename(filepath)}")
        self.statusText.set("Sẵn sàng, vui lòng ghép nối dữ liệu và bắt đầu.")
        self._loadCsvHeaders()

    def _browseVcf(self):
        filepath = filedialog.asksaveasfilename(
            title="Lưu file vCard", defaultextension=".vcf",
            filetypes=[("vCard files", "*.vcf"), ("All files", "*.*")])
        if filepath:
            self.vcfPathVar.set(filepath)
            self._logMessage(f"Sẽ lưu file VCF tại: {os.path.basename(filepath)}")

    def _loadCsvHeaders(self):
        try:
            self._createFieldMappingWidgets(converter.readCsvHeaders(self.csvPathVar.get()))
            self._logMessage("Đã đọc các cột từ CSV. Vui lòng kiểm tra và ghép nối.")
        except Exception as e:
            messagebox.showerror("Lỗi đọc file",
                                 f"Không thể đọc header từ file CSV:\n{e}", parent=self.root)
            self._logMessage(f"Lỗi đọc file CSV: {e}", "error")

    def _startConversion(self):
        if not self.csvPathVar.get() or not self.vcfPathVar.get():
            messagebox.showwarning("Thiếu thông tin",
                                   "Vui lòng chọn file CSV nguồn và nơi lưu VCF.", parent=self.root)
            return
        if any(self.fieldMappings[f].get() == SKIP_OPTION for f in converter.REQUIRED_FIELDS):
            messagebox.showwarning("Thiếu thông tin",
                                   "Bạn phải chọn cột cho 'Tên' và 'SĐT'.", parent=self.root)
            return

        self.convertButton.config(state="disabled")
        for btn in (self.previewButton, self.openFolderButton):
            btn.config(state="disabled")

        mappings = {field: combo.get() for field, combo in self.fieldMappings.items()}
        self.previewColumns = {f: h for f, h in mappings.items() if h != SKIP_OPTION}
        threading.Thread(
            target=self._conversionWorker,
            args=(self.csvPathVar.get(), self.vcfPathVar.get(), mappings),
            daemon=True).start()

    def _conversionWorker(self, csvPath, vcfPath, mappings):
        """Chạy trong thread nền - mọi cập nhật UI phải đi qua `root.after`."""
        try:
            def onImportProgress(rowIndex, totalRows):
                self._uiCall(self._updateProgress,
                             rowIndex / totalRows * IMPORT_PROGRESS_SHARE,
                             f"Đang nhập dòng {rowIndex + 1}/{totalRows + 1}...")

            def onRowError(rowNumber):
                self._uiCall(self._logMessage, f"Lỗi dòng {rowNumber}: Thiếu Tên/SĐT.", "error")

            totalRows = converter.importCsvToDb(csvPath, mappings, self.db,
                                                onProgress=onImportProgress, onRowError=onRowError)

            def onExportProgress(index, total):
                percent = IMPORT_PROGRESS_SHARE + index / total * (100 - IMPORT_PROGRESS_SHARE)
                self._uiCall(self._updateProgress, percent,
                             f"Đang xuất liên hệ {index}/{total}...")

            totalSuccess = converter.exportVcfFromDb(self.db, vcfPath, onProgress=onExportProgress)

            self._uiCall(self._logMessage, "--- HOÀN THÀNH ---", "success")
            self._uiCall(self._logMessage, f"Đã xuất thành công: {totalSuccess} liên hệ.", "success")
            if skipped := totalRows - totalSuccess:
                self._uiCall(self._logMessage, f"Đã bỏ qua do lỗi: {skipped} dòng.")
            self._uiCall(self._updateProgress, 100, f"Hoàn tất! Đã lưu {totalSuccess} liên hệ.")
            self.lastSavedFolder = os.path.dirname(vcfPath)
            self._uiCall(self._onConversionSucceeded, totalSuccess)
        except Exception as e:
            self._uiCall(self._logMessage, f"Lỗi nghiêm trọng: {e}", "error")
            self._uiCall(self._updateProgress, 0, "Chuyển đổi thất bại!")
            self._uiCall(messagebox.showerror, "Đã xảy ra lỗi",
                         f"Một lỗi đã xảy ra:\n{e}")
        finally:
            self._uiCall(self.convertButton.config, state="normal")

    def _uiCall(self, callback, *args, **kwargs):
        """Xếp lời gọi vào hàng đợi để main thread thực thi.

        KHÔNG gọi thẳng `root.after` từ thread nền: tkinter không an toàn đa luồng,
        Tcl ném `RuntimeError: main thread is not in main loop`. Chỉ `queue.Queue`
        được chạm từ thread nền; mọi widget đều do `_pumpUiQueue` đụng tới.
        """
        self.uiQueue.put((callback, args, kwargs))

    def _pumpUiQueue(self):
        """Chạy trên main thread: rút hết việc trong hàng đợi rồi tự hẹn lượt sau."""
        while True:
            try:
                callback, args, kwargs = self.uiQueue.get_nowait()
            except queue.Empty:
                break
            callback(*args, **kwargs)
        try:
            self.uiPumpJobId = self.root.after(UI_QUEUE_POLL_MS, self._pumpUiQueue)
        except tk.TclError:
            self.uiPumpJobId = None  # cửa sổ đã đóng - dừng vòng lặp

    def _onRootDestroyed(self, event):
        """Hủy lượt hẹn đang treo, tránh Tcl báo `invalid command name` lúc thoát."""
        if event.widget is not self.root or self.uiPumpJobId is None:
            return
        try:
            self.root.after_cancel(self.uiPumpJobId)
        except tk.TclError:
            pass
        self.uiPumpJobId = None

    def _onConversionSucceeded(self, totalSuccess):
        for btn in (self.previewButton, self.openFolderButton):
            btn.config(state="normal")
        messagebox.showinfo("Thành công",
                            f"Đã xử lý và lưu thành công {totalSuccess} liên hệ.", parent=self.root)

    # ------------------------------------------------------------------ hiển thị
    def _updateProgress(self, value, text):
        self.progress['value'] = value
        self.progress.config(style='Success.Horizontal.TProgressbar' if value >= 100
                             else 'Horizontal.TProgressbar')
        self.statusText.set(text if value >= 100 else f"{text} ({value:.0f}%)")

    def _logMessage(self, message, level="normal"):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.statusLog.config(state=tk.NORMAL)
        self.statusLog.insert(tk.END, f"[{timestamp}] {message}\n")
        if level in ("success", "error"):
            self.statusLog.tag_add(level, f"end-{len(message) + 2}c", "end-1c")
        self.statusLog.see(tk.END)
        self.statusLog.config(state=tk.DISABLED)

    def _openSavedFolder(self):
        if self.lastSavedFolder:
            webbrowser.open(os.path.realpath(self.lastSavedFolder))

    def _showAboutDialog(self):
        messagebox.showinfo(
            "Về ứng dụng",
            f"{APP_NAME} - Chuyển đổi CSV sang vCard\n"
            f"Phiên bản: {APP_VERSION}\n\nTác giả: {APP_AUTHOR}",
            parent=self.root)

    def _showPreviewDialog(self):
        totalContacts = self.db.getContactCount()
        if not totalContacts:
            messagebox.showinfo("CSDL Rỗng", "Chưa có dữ liệu.", parent=self.root)
            return
        PreviewWindow(self.root, self.db, self.previewColumns, totalContacts, self.iconPhoto,
                      theme=self.tokens.theme)

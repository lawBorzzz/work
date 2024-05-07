import tkinter as tk
from tkinter import Scrollbar, filedialog, messagebox
import configparser
import os
import pandas as pd
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Cm
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Cm
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

def split_text(text, max_length=50):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_length:
            current_line += " " + word
        else:
            lines.append(current_line.strip())
            current_line = word
    lines.append(current_line.strip())
    return "\n".join(lines)

class MailRegistryAppWithWord:
    def __init__(self, master):
        self.master = master
        self.master.title("Менеджер писем")
        self.master.geometry("400x120")  # Устанавливаем размер окна
        self.center_window()  # Центрируем окно по горизонтали и вертикали
        
        # Определяем путь к файлу конфигурации
        config_dir = os.path.join(os.getenv('APPDATA'), 'MailRegistryApp')
        config_file = os.path.join(config_dir, 'config.ini')

        # Создаем директорию для файла конфигурации, если ее нет
        os.makedirs(config_dir, exist_ok=True)

        # Создаем файл конфигурации, если он отсутствует
        if not os.path.exists(config_file):
            with open(config_file, 'w'):
                pass

        # Путь к файлу базы данных
        self.registry_path = ""

        # Кнопки
        self.btn_create_registry = tk.Button(master, text="  Реестр писем", command=self.create_registry)
        self.btn_create_registry.pack(pady=10)

        self.btn_settings = tk.Button(master, text="    Настройки    ", command=self.open_settings)
        self.btn_settings.pack(pady=10)

        # Инициализация файла конфигурации
        self.config = configparser.ConfigParser()
        self.config_file = os.path.join(os.getenv("APPDATA"), "MailRegistryApp", "config.ini")
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            if 'Paths' in self.config:
                self.registry_path = self.config['Paths'].get('registry', '')

    def center_window(self):
        # Получаем размеры экрана
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Получаем размеры окна
        window_width = self.master.winfo_reqwidth()
        window_height = self.master.winfo_reqheight()

        # Вычисляем координаты для размещения окна по центру экрана
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # Устанавливаем положение окна
        self.master.geometry("+{}+{}".format(x, y))

    def create_registry(self):
        self.center_window()  # Центрируем окно по горизонтали и вертикали
        if not self.registry_path:
            print("Сначала выберите файл базы данных реестра через настройки")
            messagebox.showwarning("Внимание", "Сначала выберите файл базы данных реестра через настройки.")
            return

        # Чтение данных из файла
        try:
            df = pd.read_excel(self.registry_path)  # Поддерживаем различные форматы Excel
            adresat_column = df['ADRESAT']  # Выбираем столбец с именами
            adresat_values = adresat_column.tolist()  # Преобразуем в список

            # Открываем окно для выбора имен
            self.select_names_window(adresat_values)
        except Exception as e:
            print("Ошибка чтения файла реестра писем:", e)

    def select_names_window(self, adresat_values):
        # Создаем новое окно для выбора имен
        select_names_window = tk.Toplevel(self.master)
        select_names_window.title("Выбор имен")
        select_names_window.geometry("600x600")

        # Сортируем имена в алфавитном порядке
        adresat_values.sort()

        # Создаем список имен с прокруткой
        lb_names = tk.Listbox(select_names_window, selectmode=tk.MULTIPLE, width=50, height=20)
        for name in adresat_values:
            lb_names.insert(tk.END, name)
        lb_names.pack(pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Создаем и настраиваем скроллбар
        scrollbar = Scrollbar(select_names_window, orient=tk.VERTICAL, command=lb_names.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        lb_names.config(yscrollcommand=scrollbar.set)

        # Кнопка для создания списка писем
        btn_create_list = tk.Button(select_names_window, text="Создать список писем", command=lambda: self.create_word_document(lb_names), bg="blue", fg="white", width=20)
        btn_create_list.pack(pady=10)

        # Кнопка для выхода из программы
        btn_exit = tk.Button(select_names_window, text="Выход", command=select_names_window.destroy, bg="red", fg="white", width=20, height=1)
        btn_exit.pack(pady=10)

    def create_word_document(self, lb_names):
        # Получаем выбранные имена
        selected_indices = lb_names.curselection()
        selected_names = [lb_names.get(idx) for idx in selected_indices]
        print("Выбранные имена:", selected_names)

        if not selected_names:
            print("Выберите хотя бы одно имя из списка")
            return

        # Чтение данных из файла
        try:
            df = pd.read_excel(self.registry_path)  # Поддерживаем различные форматы Excel

            # Создаем новый документ Word
            doc = Document()

            # Добавляем в верхний левый угол на всех листах информацию об отправителе
            sender_info = " От кого: Девятнадцатый арбитражный\n                           апелляционный суд\n Откуда: г. Воронеж, ул. Платонова, д. 8"
            for section in doc.sections:
                header = section.header
                paragraph = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
                paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT  # Выравниваем по центру
                paragraph.text = sender_info

            for section in doc.sections:
                section.page_width = Cm(22.9)  # Устанавливаем ширину листа
                section.page_height = Cm(16.2)  # Устанавливаем высоту листа (албомная ориентация)
                section.left_margin = Cm(1)  # Устанавливаем левый отступ
                section.right_margin = Cm(1)  # Устанавливаем правый отступ
                section.top_margin = Cm(1)  # Устанавливаем верхний отступ
                section.bottom_margin = Cm(1)  # Устанавливаем нижний отступ

            for name in selected_names:
                # Фильтруем строки по выбранному имени
                selected_rows = df[df['ADRESAT'] == name]

                # Создаем новый параграф
                p = doc.add_paragraph()
                p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT  # Выравниваем по правому краю

                # Добавляем пропуски перед данными
                for _ in range(14):
                    p.add_run("\n")

                # Добавляем данные из выбранных строк
                for index, row in selected_rows.iterrows():
                    # Добавляем адресат_2
                        p = doc.add_paragraph()
                        p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT  # Выравниваем по правому краю
                        value = row['ADRESAT_2']
                        if not pd.isnull(value):
                            # Разбиваем текст на строки, если больше 75 символов
                            if len(value) > 75:
                                value = split_text(value)
                            run = p.add_run(f"{value}")
                            run.font.size = Pt(10)  # Устанавливаем размер шрифта
                            run.font.italic = True  # Устанавливаем курсив
                        
                    # Добавляем адресат
                        p = doc.add_paragraph()
                        p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT  # Выравниваем по правому краю
                        value = row['ADRESAT']
                        if not pd.isnull(value):
                            run = p.add_run(f"{value}")
                            run.font.size = Pt(10)  # Устанавливаем размер шрифта
                            run.font.bold = True  # Устанавливаем жирный шрифт
                            run.font.italic = True  # Устанавливаем курсив

                        # Добавляем адрес
                        p = doc.add_paragraph()
                        p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT  # Выравниваем по правому краю
                        value = row['ADDRESSLINE']
                        if not pd.isnull(value):
                            run = p.add_run(f"{value}")
                            run.font.size = Pt(10)  # Устанавливаем размер шрифта
                            run.font.italic = True  # Устанавливаем курсив

                # Добавляем разрыв страницы между именами
                if name != selected_names[-1]:
                    doc.add_page_break()

            # Сохраняем документ
            output_path = filedialog.asksaveasfilename(defaultextension=".docx")
            if output_path:
                doc.save(output_path)
                print("Документ успешно создан и сохранен в файле:", output_path)
        except Exception as e:
            print("Ошибка при создании документа Word:", e)
    
    def open_settings(self):
        # Создаем новое окно настроек
        settings_window = tk.Toplevel(self.master)
        settings_window.title("Настройки")
        
        # Поля для путей к базам данных
        registry_path_var = tk.StringVar()

        # Загрузка путей из конфигурации
        if 'Paths' in self.config:
            registry_path_var.set(self.config['Paths'].get('registry', ''))

        # Функции выбора пути для баз данных
        def choose_registry_path():
            path = filedialog.askopenfilename(
                title="Выберите файл базы данных реестра",
                filetypes=[("Excel files", "*.xls;*.xlsx"), ("All files", "*.*")])

            if path:
                registry_path_var.set(path)
                save_paths()  # Сохраняем путь при выборе файла

        # Функция сохранения путей в файл конфигурации
        def save_paths():
            self.registry_path = registry_path_var.get()  # Обновляем путь к файлу реестра
            self.config['Paths'] = {
                'registry': registry_path_var.get(),
            }
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
            settings_window.destroy()  # Закрываем окно настроек после сохранения
            # Сохраняем путь при выборе файла
            if self.registry_path:
                self.config['Paths'] = {'registry': self.registry_path}
                with open(self.config_file, 'w') as configfile:
                    self.config.write(configfile)
                settings_window.destroy()  # Закрываем окно настроек после сохранения

        # Кнопки выбора пути к базам данных
        btn_registry_path = tk.Button(settings_window, text="Выбрать файл базы данных реестра", command=choose_registry_path)
        btn_registry_path.pack(pady=10)

        entry_registry_path = tk.Entry(settings_window, textvariable=registry_path_var, state='readonly', width=50)
        entry_registry_path.pack(pady=5)


        # Кнопка "Сохранить"
        btn_save = tk.Button(settings_window, text="Сохранить", command=save_paths)
        btn_save.pack(pady=10)

        # Устанавливаем начальные значения в полях
        entry_registry_path.insert(0, registry_path_var.get())

        # Устанавливаем окно настроек модальным
        settings_window.transient(self.master)
        settings_window.grab_set()
        self.master.wait_window(settings_window)

def main():
    root = tk.Tk()
    app = MailRegistryAppWithWord(root)
    root.mainloop()

if __name__ == "__main__":
    main()

import os
import time
import tarfile
import tkinter as tk
from tkinter import scrolledtext
import logging
import sys

# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Установите уровень логирования

# Создание обработчика для записи логов в файл
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.DEBUG)  # Установите уровень логирования для обработчика

# Создание форматера для логов
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Добавление обработчика к логгеру
logger.addHandler(file_handler)

class Emulator:
    """
    Класс для эмуляции файловой системы и выполнения команд, аналогичных shell-командам.

    Атрибуты:
        vfs_path (str): Путь к tar-файлу с виртуальной файловой системой.
        current_dir (str): Текущая рабочая директория в виртуальной файловой системе.
        start_time (float): Время запуска эмулятора для расчета uptime.
    """

    def __init__(self, vfs_path):
        """
        Инициализирует эмулятор и виртуальную файловую систему.

        Параметры:
            vfs_path (str): Путь к tar-файлу с виртуальной файловой системой.
        """
        self.vfs_path = vfs_path
        self.current_dir = ''
        self.init_vfs()

        self.start_time = time.time()  # Время старта для расчета uptime
        logger.debug('Emulator started')

    def init_vfs(self):
        """
        Инициализирует виртуальную файловую систему: открывает TAR-файл.
        """
        self.tar_ref = tarfile.open(self.vfs_path, 'r')
        logger.debug('VFS initialized: vfs_path=%s', self.vfs_path)

    def cleanup(self):
        """
        Очищает временную директорию после завершения работы эмулятора.
        """
        logger.debug('Cleaning up...')
        self.tar_ref.close()

    def run_command(self, command, output_widget=None):
        """
        Выполняет указанную команду и выводит результат.

        Параметры:
            command (str): Команда для выполнения.
            output_widget (tk.Text, optional): Виджет для вывода результата в GUI.
        """
        parts = command.split()
        if not parts:
            return

        cmd = parts[0]
        args = parts[1:]

        if output_widget:
            # Вывод текущей директории перед командой, как в реальном терминале
            output_widget.insert(tk.END, f"{self.whoami()}$ {command}\n")

        # Выполнение команды
        if cmd == 'ls':
            result = self.ls()
        elif cmd == 'cd':
            if args:
                result = self.cd(args[0])
            else:
                result = "cd: missing path"
        elif cmd == 'exit':
            result = self.exit()
        elif cmd == 'uptime':
            result = self.uptime()
        elif cmd == 'tail':
            if args:
                result = self.tail(args[0])
            else:
                result = "tail: missing file"
        elif cmd == 'uniq':
            if args:
                result = self.uniq(args[0])
            else:
                result = "uniq: missing file"
        else:
            result = f"{cmd}: command not found"

        # Вывод результата команды
        if output_widget:
            output_widget.insert(tk.END, result + "\n")
            output_widget.see(tk.END)  # Автопрокрутка вниз

        logger.debug('Command executed: %s', command)

    def ls(self):
        """
        Выполняет команду 'ls': выводит список файлов и директорий в текущей директории.

        Возвращает:
            str: Список файлов и директорий.
        """
        logger.debug('Listing files in current directory: %s', self.current_dir)
        files = [f for f in self.tar_ref.getnames() if f.startswith(self.current_dir)]
        current_dir_files = set()

        for f in files:
            relative_path = f.replace(self.current_dir, '', 1).lstrip('/')
            if '/' not in relative_path:
                current_dir_files.add(relative_path)
            else:
                dir_name = relative_path.split('/')[0]
                current_dir_files.add(dir_name)

        return "\n".join(sorted(current_dir_files))

    def cd(self, path):
        """
        Выполняет команду 'cd': изменяет текущую рабочую директорию.

        Параметры:
            path (str): Путь к новой директории.

        Возвращает:
            str: Сообщение о результате операции.
        """
        logger.debug('Changing directory: %s', path)

        if path == '..':
            if self.current_dir:
                self.current_dir = os.path.normpath(os.path.join(self.current_dir, '..'))
                if self.current_dir == '.':
                    self.current_dir = ''
            return f"Changed directory to {self.current_dir}"
        else:
            new_path = os.path.join(self.current_dir, path)
            if not new_path.endswith('/'):
                new_path += '/'

            if any(name.startswith(new_path) for name in self.tar_ref.getnames()):
                self.current_dir = new_path
                return f"Changed directory to {self.current_dir}"
            else:
                return f"cd: {path}: No such file or directory"

    def exit(self):
        """
        Выполняет команду 'exit': завершает работу эмулятора.

        Возвращает:
            str: Сообщение о завершении работы.
        """
        logger.debug('Exiting emulator...')
        self.cleanup()
        exit()
        return "Exiting emulator..."

    def uptime(self):
        """
        Выполняет команду 'uptime': выводит время работы эмулятора.

        Возвращает:
            str: Время работы эмулятора в секундах.
        """
        logger.debug('Getting uptime...')
        uptime_seconds = time.time() - self.start_time
        return f"Uptime: {uptime_seconds:.2f} seconds"

    def tail(self, file_path):
        """
        Выполняет команду 'tail': выводит последние строки файла.

        Параметры:
            file_path (str): Путь к файлу.

        Возвращает:
            str: Последние строки файла.
        """
        logger.debug('Tailing file: %s', file_path)
        try:
            # Полный путь к файлу с учетом текущей директории
            full_path = os.path.join(self.current_dir, file_path)
            file_obj = self.tar_ref.extractfile(full_path)
            lines = file_obj.readlines()[-6:]  # Последние 6 строк
            return "".join(line.decode('utf-8') for line in lines)
        except KeyError:
            return f"tail: {file_path}: No such file"

    def uniq(self, file_path):
        """
        Выполняет команду 'uniq': выводит только уникальные строки файла.

        Параметры:
            file_path (str): Путь к файлу.

        Возвращает:
            str: Уникальные строки файла.
        """
        logger.debug('Uniq file: %s', file_path)
        try:
            # Полный путь к файлу с учетом текущей директории
            full_path = os.path.join(self.current_dir, file_path)
            file_obj = self.tar_ref.extractfile(full_path)
            lines = file_obj.readlines()
            unique_lines = []
            seen = set()
            for line in lines:
                if line not in seen:
                    unique_lines.append(line)
                    seen.add(line)
            return "".join(line.decode('utf-8') for line in unique_lines)
        except KeyError:
            return f"uniq: {file_path}: No such file"

    def whoami(self):
        """
        Выполняет команду 'whoami': выводит имя текущего пользователя.

        Возвращает:
            str: Имя пользователя.
        """
        logger.debug('Getting current user...')
        return os.getlogin()

class ShellGUI:
    """
    Класс для создания GUI оболочки, которая позволяет вводить команды и видеть результат их выполнения.

    Атрибуты:
        emulator (Emulator): Объект эмулятора, управляющий командной оболочкой.
        root (tk.Tk): Корневое окно приложения.
        output (tk.scrolledtext.ScrolledText): Текстовое поле для вывода результатов команд.
        entry (tk.Entry): Поле ввода для команд.
    """

    def __init__(self, emulator):
        """
        Инициализация GUI для эмулятора.

        Параметры:
            emulator (Emulator): Объект эмулятора, управляющий командной оболочкой.
        """
        logger.debug('Initializing GUI...')
        self.emulator = emulator
        self.root = tk.Tk()
        self.root.title("Shell Emulator")

        # Текстовое поле для вывода
        self.output = scrolledtext.ScrolledText(self.root, height=20, width=80, state=tk.NORMAL)
        self.output.pack()

        # Поле ввода для команд
        self.entry = tk.Entry(self.root, width=80)
        self.entry.pack()
        self.entry.bind('<Return>', self.execute_command)

    def execute_command(self, event):
        """
        Обработчик ввода команды: выполняет команду и выводит результат.

        Параметры:
            event (tk.Event): Событие нажатия клавиши <Return>.
        """
        logger.debug('Executing command: %s', self.entry.get())
        command = self.entry.get()
        self.emulator.run_command(command, output_widget=self.output)
        self.entry.delete(0, tk.END)

    def run(self):
        """
        Запуск главного цикла GUI.
        """
        logger.debug('Starting GUI main loop...')
        self.root.mainloop()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python emulator.py <path_to_vfs_tar>")
        sys.exit(1)

    vfs_path = sys.argv[1]
    emulator = Emulator(vfs_path)
    gui = ShellGUI(emulator)
    gui.run()

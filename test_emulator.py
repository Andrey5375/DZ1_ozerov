import tarfile
import io
import tempfile
import os
from prak1 import Emulator

def create_test_tar():
    
    temp_tar_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tar')
    temp_tar_path = temp_tar_file.name

    
    file_content = b"line 1\nline 2\nline 3\nline 4\nline 5\nline 6\nline 7\nline 8\nline 9\nline 10\n"
    dir_content = b"Hello, world!\n"

    with tarfile.open(temp_tar_path, 'w') as tar:
        info = tarfile.TarInfo(name='file1.txt')
        info.size = len(file_content)
        tar.addfile(tarinfo=info, fileobj=io.BytesIO(file_content))

        info = tarfile.TarInfo(name='dir1/')
        info.type = tarfile.DIRTYPE
        tar.addfile(tarinfo=info)

        info = tarfile.TarInfo(name='dir1/file2.txt')
        info.size = len(dir_content)
        tar.addfile(tarinfo=info, fileobj=io.BytesIO(dir_content))

    return temp_tar_path

def test_ls(emulator):
    result = emulator.ls()
    assert 'file1.txt' in result, f"Expected 'file1.txt' in result, but got {result}"
    assert 'dir1' in result, f"Expected 'dir1' in result, but got {result}"
    print("test_ls passed")

def test_cd(emulator):
    result = emulator.cd('dir1')
    assert result == "Changed directory to dir1/", f"Expected 'Changed directory to dir1/', but got {result}"
    result = emulator.cd('..')
    assert result == "Changed directory to ", f"Expected 'Changed directory to ', but got {result}"
    print("test_cd passed")

def test_uptime(emulator):
    result = emulator.uptime()
    assert 'Uptime' in result, f"Expected 'Uptime' in result, but got {result}"
    print("test_uptime passed")

def test_tail(emulator):
    result = emulator.tail('file1.txt')
    assert 'line 5' in result, f"Expected 'line 5' in result, but got {result}"
    assert 'line 10' in result, f"Expected 'line 10' in result, but got {result}"
    print("test_tail passed")

def test_uniq(emulator):
    result = emulator.uniq('file1.txt')
    assert 'line 1' in result, f"Expected 'line 1' in result, but got {result}"
    assert 'line 10' in result, f"Expected 'line 10' in result, but got {result}"
    print("test_uniq passed")

def test_exit(emulator):
    try:
        emulator.exit()
    except SystemExit:
        print("test_exit passed")

def run_tests():
    temp_tar_path = create_test_tar()
    emulator = Emulator(temp_tar_path)

    test_ls(emulator)
    test_cd(emulator)
    test_uptime(emulator)
    test_tail(emulator)
    test_uniq(emulator)
    test_exit(emulator)

    # Удаление временного tar-файла после тестирования
    os.remove(temp_tar_path)

if __name__ == '__main__':
    run_tests()

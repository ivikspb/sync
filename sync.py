import sys
import os
from datetime import datetime
import time
import shutil


class Log:
    messages = None
    filename = None

    def __init__(self, filename):
        self.filename = filename
        self.messages = []

    def log(self, message):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.messages.append(now + ': ' + message)

    def cleanmessages(self):
        self.messages = []

    def write(self):
        if self.messages is not None and len(self.messages) > 0:
            with open(self.filename, 'a') as file:
                for text in self.messages:
                    file.write(text + '\n')
            self.cleanmessages()


class Synchronization:
    source = None
    destination = None
    _log = None

    def __init__(self, src, dest, log=None):
        self.source = src
        self.destination = dest
        self._log = log

    def getfilelist(self, path):
        fileslist = []
        currentdir = os.listdir(path)
        for f in currentdir:
            if os.path.isfile(os.path.join(path, f)):
                fileslist.append(f)
            elif os.path.isdir(os.path.join(path, f)):
                fileslist.append(f)
                for s in self.getfilelist(os.path.join(path, f)):
                    fileslist.append(os.path.join(f, s))
        return fileslist

    def log(self, message):
        print(message)
        if self._log is not None:
            self._log.log(message)

    def sync(self):
        sourcefiles = set(self.getfilelist(self.source))
        destfiles = set(self.getfilelist(self.destination))

        # deleting files
        deldir = []
        for file in list(destfiles - sourcefiles):
            path = os.path.join(self.destination, file)
            if os.path.isfile(path):
                self.log('Deleting file ' + path)
                os.remove(path)
            elif os.path.isdir(path):
                deldir.append(path)
        if len(deldir) > 0:
            for path in deldir:
                self.log('Deleting dir ' + path)
                os.rmdir(path)
        del deldir

        # exist files
        for file in list(sourcefiles & destfiles):
            filesource = os.path.join(self.source, file)
            filedestination = os.path.join(self.destination, file)
            if (os.path.isfile(filesource) and os.path.isfile(filedestination) and
                    (os.stat(filesource).st_mtime != os.stat(filedestination).st_mtime or
                     os.stat(filesource).st_size != os.stat(filedestination).st_size)):
                self.log('Deleting file ' + filedestination)
                os.remove(filedestination)
                self.log('Copy file ' + file)
                shutil.copy2(filesource, filedestination, follow_symlinks=False)
            elif os.path.isfile(filesource) and os.path.isdir(filedestination):
                self.log('Deleting dir ' + filedestination)
                os.rmdir(filedestination)
                self.log('Copy file ' + file)
                shutil.copy2(filesource, filedestination, follow_symlinks=False)
            elif os.path.isdir(filesource) and os.path.isfile(filedestination):
                self.log('Deleting file ' + filedestination)
                os.remove(filedestination)
                self.log('Create dir ' + file)
                os.mkdir(filedestination)

        # new files
        newfiles = []
        for file in list(sourcefiles - destfiles):
            path = os.path.join(self.source, file)
            if os.path.isdir(path):
                self.log('Create dir ' + file)
                os.mkdir(os.path.join(self.destination, file))
            elif os.path.isfile(path):
                newfiles.append(file)
        if len(newfiles) > 0:
            for file in newfiles:
                self.log('Copy file ' + file)
                shutil.copy2(os.path.join(self.source, file), os.path.join(self.destination, file),
                             follow_symlinks=False)


if __name__ == '__main__':
    showdoc = False
    if len(sys.argv) == 5:
        try:
            interval = int(sys.argv[4])
        except ValueError:
            interval = 0
        if (interval > 0 and os.path.isdir(sys.argv[1]) and os.path.isdir(sys.argv[2]) and
                not os.path.isdir(sys.argv[3]) and os.path.isdir(os.path.dirname(sys.argv[3]))):
            log = Log(sys.argv[3])
            sync = Synchronization(sys.argv[1], sys.argv[2], log)

            while True:
                start_time = time.time()
                sync.sync()
                log.write()
                time.sleep(interval - (time.time() - start_time) % interval)

        else:
            showdoc = True
    else:
        showdoc = True

    if showdoc is True:
        print(__file__ + ' sourcepath destinationpath logfile interval')
        print('\nПрограмма синхронизирует данные из папки источника в папку назначения, записывая изменения'
              ' в указанный log файл, синхронизация происходит через заданный интервал времени')
        print('sourcepath - Путь к каталогу источника')
        print('destinationpath - Путь к каталогу назначения')
        print('logfile - Путь к лог файлу')
        print('interval - Интервал в секундах в течении, которого происходит синхронизация')

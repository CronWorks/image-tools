from datetime import datetime
from os.path import basename, dirname, getmtime, splitext
import pyexiv2
import re


EXIF_DATETIME_KEY = 'Exif.Photo.DateTimeOriginal'

SEPARATOR = '[-_\. /]'  # date or title separator
REGEX_FILENAME_SHOULD_BE_CHANGED = '(\d{3,}%s\d{3,})|(\d{5,})|((IMG|P|DSCF?)_?\d{4,})' % SEPARATOR
REGEX_JPG_FILENAME = '.*\.(jpg|jpeg)$'
REGEX_IMAGE_FILENAME = '.*\.(jpg|jpeg|png|gif|bmp)$'
TIME_SEPARATOR = '[\.:]?'  # hour/minute/second separator
MONTH_ALPHA = '(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|june|july|sept|january|february|march|april|august|september|october|november|december)'
REGEX_LIST = [['^(\d{2}|\d{4})%s(\d{2})%s(\d{2})%s(\d{2})%s(\d{2})%s+(.+)\.(\w{1,4})' % (SEPARATOR, SEPARATOR, SEPARATOR, TIME_SEPARATOR, SEPARATOR),
               'year', 'month', 'day', 'hour', 'minute', 'title', 'extension'],
              ['^(\d{2}|\d{4})%s(\d{2})%s(\d{2})%s+(.+)\.(\w{1,4})' % (SEPARATOR, SEPARATOR, SEPARATOR),
               'year', 'month', 'day', 'title', 'extension'],
              ['^%s%s(\d{2})%s(.+)\.(\w{1,4})' % (MONTH_ALPHA, SEPARATOR, SEPARATOR),
               'month_alpha', 'year', 'title', 'extension'],
              ['^(.+)\.(\w{1,4})',
               'title', 'extension'],
              ]

def getTestFilePaths():
    from os import listdir
    testPath = '%s/test' % dirname(__file__)
    testFiles = sorted(['%s/%s' % (testPath, f) for f in listdir(testPath)])
    return testFiles

class ImageFileInfoTool:

    def __init__(self, out, system):
        self.out = out
        self.system = system

    def getFileInfo(self, fileNameFullPath, okToUseFileName=False, okToUseFileCreationTime=False):
        try:
            fileInfo = self._getFileInfo(fileNameFullPath, okToUseFileName, okToUseFileCreationTime)
        except:
            self.out.put("Error while reading file (do you have file permissions?): %s" % fileNameFullPath, self.out.LOG_LEVEL_VERBOSE)
            return {}
        if not fileInfo:
            self.out.put("Could not read EXIF, file or filename data for %s" % fileNameFullPath, self.out.LOG_LEVEL_VERBOSE)
            return {}
        return self.normalizeFileInfo(fileInfo)

    def _getFileInfo(self, fileNameFullPath, okToUseFileName, okToUseFileCreationTime):
        '''
        do the work of getting file information, from EXIF, filename, and file creation time.
        order of priority for each field is EXIF > filename > creation time.
        '''
        fileInfo = {}
        if okToUseFileCreationTime:
            fileInfo.update(self.getFileInfoFromFilesystem(fileNameFullPath))
            self.out.put("- after reading from filesystem: %s" % fileInfo.__str__(), self.out.LOG_LEVEL_VERBOSE)
        if okToUseFileName:
            fileInfo.update(self.getFileInfoFromFilename(basename(fileNameFullPath)))
            self.out.put("- after reading from filename: %s" % fileInfo.__str__(), self.out.LOG_LEVEL_VERBOSE)
        if self.isJpg(fileNameFullPath):
            try:
                fileInfo.update(self.getFileInfoFromExifData(fileNameFullPath))
                self.out.put("- after reading from EXIF: %s" % fileInfo.__str__(), self.out.LOG_LEVEL_VERBOSE)
            except:
                self.out.put("Error happened while trying to read EXIF tags.", self.out.LOG_LEVEL_VERBOSE)
        return fileInfo

    def isImageFilename(self, originalFileName):
        return re.match(REGEX_IMAGE_FILENAME, originalFileName, re.I)

    def isJpg(self, fileName):
        return (re.match(REGEX_JPG_FILENAME, fileName, re.I) != None)

    def getFileInfoFromFilename(self, fileName):
        result = {}
        for patternConfig in REGEX_LIST:
            pattern = patternConfig[0]
            m = re.match(pattern, fileName)
            if not m:
                continue
            for i in range(1, len(patternConfig)):
                result[patternConfig[i]] = m.group(i)
            self.out.put("Returning filename info for %s: %s" % (fileName, result), self.out.LOG_LEVEL_VERBOSE)
            return result
        self.out.put("Found no filename pattern match to get file info for %s" % (fileName), self.out.LOG_LEVEL_VERBOSE)
        return result

    def getFileInfoFromExifData(self, fullPath):
        metadata = self.readExifMetadata(fullPath)
        result = self.getFileInfoFromFilename(basename(fullPath))
        try:
            dt = metadata[EXIF_DATETIME_KEY].value
            result['year'] = str(dt.year)
            result['month'] = str(dt.month)
            result['day'] = str(dt.day)
            result['hour'] = str(dt.hour)
            result['minute'] = str(dt.minute)

        except:
            self.out.put('Unable to get all EXIF information from %s' % basename(fullPath))
        return result

    def copyExifMetadata(self, sourceFullPath, targetFullPath):
        md = self.readExifMetadata(sourceFullPath)
        self.writeExifMetadata(targetFullPath, md)

    def readExifMetadata(self, fullPath):
        metadata = pyexiv2.ImageMetadata(fullPath)
        metadata.read()
        return metadata

    def writeExifMetadata(self, fullPath, mdSource):
        mdDest = pyexiv2.ImageMetadata(fullPath)
        mdDest.read()
        mdSource.copy(mdDest)
        mdDest.write(preserve_timestamps=True)

    def getFileInfoFromFilesystem(self, fullPath):
        result = self.getFileInfoFromFilename(basename(fullPath))
        unixTime = getmtime(fullPath)
        dt = datetime.fromtimestamp(unixTime)
        result['year'] = str(dt.year)
        result['month'] = str(dt.month)
        result['day'] = str(dt.day)
        result['hour'] = str(dt.hour)
        result['minute'] = str(dt.minute)
        return result

    def normalizeFileInfo(self, fileInfo):
        fileInfo['year'] = ("20" + fileInfo['year'])[-4:]  # force 4-digit year. Concat and take the last 4 digits
        fileInfo['month'] = ("0" + fileInfo['month'])[-2:]
        fileInfo['day'] = ("0" + fileInfo['day'])[-2:]
        fileInfo['hour'] = ("0" + fileInfo['hour'])[-2:]
        fileInfo['minute'] = ("0" + fileInfo['minute'])[-2:]
        fileInfo['extension'] = fileInfo['extension'].lower()
        return fileInfo

    def renameFileIfNecessary(self, fullPath):
        """
        if the file is not yet named with a descriptive name (it's still IMG_12345.JPG or whatever),
        then ask the user for a new filename to name it to.
        
        This prevents the non-descriptive filename from propagating all over your hard drive by
        getting copied to all star folders.
        
        NOTE: only works in GUI mode (see askUserForNewFileName())
        """
        fileInfo = self.getFileInfoFromFilename(basename(fullPath))
        if not re.search(REGEX_FILENAME_SHOULD_BE_CHANGED, fileInfo['title']):
            return fullPath
        newFullPath = self.askUserForNewFileName(fullPath)
        if newFullPath == fullPath:
            # probably not in GUI mode. Or, an input box was presented but they didn't rename.
            # trust the user, I guess. Sometimes they're idiots though.
            return fullPath
        # user has selected a different filename, so rename the file
        self.system.rename(fullPath, newFullPath)
        return newFullPath

    def askUserForNewFileName(self, fullPath):
        self.out.put('File %s should be renamed, but this is disabled in the console version' % basename(fullPath),
                     self.out.LOG_LEVEL_VERBOSE)
        return fullPath

    def getImageRotationByExif(self, fullPath):
        metadata = self.readExifMetadata(fullPath)
        rotationDegrees = {1: 0,
                           3: 180,
                           6:-90,
                           8: 90}
        key = metadata['Exif.Image.Orientation'].value
        if key in rotationDegrees:
            return rotationDegrees[key]
        return 0

if __name__ == "__main__":

    from PySystemMock import PySystemMock
    from JobOutput import JobOutput

    out = JobOutput()
    out.disableLogFile()
    system = PySystemMock(out)
    t = ImageFileInfoTool(out, system)
    TEST_FILE = 'test/Named image file.JPG'
    print "reading rotation degrees of %s (not the actual EXIF index; should be 0)" % TEST_FILE
    print t.getImageRotationByExif(TEST_FILE)

#!/usr/bin/python
from datetime import datetime
from os import listdir
from os.path import abspath, basename, dirname, isdir
import re
import sys
import traceback
from urllib import unquote

from image_tools.ImageToolsShared import ImageFileInfoTool, getTestFilePaths
from py_base.Job import Job


FILE_FORMAT_DATE = '%s-%s-%s %s.%s'  # 'Y-M-D H.M'
FILE_FORMAT_DATETIME = '%s-%s-%s %s.%s %s.%s'  # 'Y-M-D H.M S.ms'
TIME_FORMAT_BRIEF = '{0:%Y-%m-%d %H%M}'  #
TIME_FORMAT_VERBOSE = '{0:%Y-%m-%d %H:%M:%S}'

class ImageDateStamper(Job):

    def __init__(self):
        super(ImageDateStamper, self).__init__()

    def doRunSteps(self):
        self.stamp()

    def defineCustomArguments(self, parser):
        parser.add_argument('-s',
                            '--strip',
                            action='store_true',
                            default=False,
                            help="Strip any existing date/time stamps from filename (ignores -t)",
                            )
        parser.add_argument('-t',
                            '--time',
                            action='store_true',
                            default=False,
                            help="Include time in date stamp",
                            )
        parser.add_argument('path',
                            nargs='*',
                            help="Path(s) of the image(s) to date stamp, space separated if multiple",
                            )

    def stamp(self):
        imageTool = ImageFileInfoTool(self.out, self.system)
        filesToStamp = []
        for filename in self.getNormalizedPathArgument():
            if isdir(filename):
                for child in listdir(filename):  # doesn't descend into subdirs
                    child = '%s/%s' % (filename, child)
                    filesToStamp.append(child)
            else:
                filesToStamp.append(filename)

        for filename in sorted(filesToStamp):
            if not imageTool.isImageFilename(filename):
                self.out.put("Skipping %s because it doesn't look like an image file." % filename, self.out.LOG_LEVEL_IMPORTANT)
                continue
            try:
                fileInfo = imageTool.getFileInfo(filename, okToUseFileName=True)
            except:
                fileInfo = False
                self.out.put("File is broken or has no data!", self.out.LOG_LEVEL_WARN)
                self.out.put(traceback.format_exc(), self.out.LOG_LEVEL_DEBUG)
            if not fileInfo:
                self.out.put("Unable to stamp file: %s" % basename(filename), self.out.LOG_LEVEL_IMPORTANT)
                continue
            self.out.put("Stamping %s..." % filename, self.out.LOG_LEVEL_IMPORTANT)
            self.rename(filename, fileInfo)


    def rename(self, originalFileNameFullPath, fileInfo):
        newFileName = self.getTargetFileName(fileInfo)
        if newFileName != basename(originalFileNameFullPath):
            newFileNameFullPath = '%s/%s' % (dirname(originalFileNameFullPath), newFileName)
            self.system.rename(originalFileNameFullPath, newFileNameFullPath)

    def getTargetFileName(self, fileInfo):
        if self.arguments['strip']:
            # always strip time as well as date (not doing so may lead to huge headaches)
            fileName = '%s.%s' % (fileInfo['title'],
                                  fileInfo['extension'])
        elif self.arguments['time']:
            fileName = FILE_FORMAT_DATETIME % (fileInfo['year'],
                                               fileInfo['month'],
                                               fileInfo['day'],
                                               fileInfo['hour'],
                                               fileInfo['minute'],
                                               fileInfo['title'],
                                               fileInfo['extension'])
        else:
            fileName = FILE_FORMAT_DATE % (fileInfo['year'],
                                           fileInfo['month'],
                                           fileInfo['day'],
                                           fileInfo['title'],
                                           fileInfo['extension'])
        return fileName


if __name__ == "__main__":
    from py_base.Job import runMockJob
    runMockJob(ImageDateStamper, arguments={  # 'time': True,
                                            'path': getTestFilePaths() + ['bad/path.JPG']})

#!/usr/bin/python
from PIL import Image
from os.path import abspath, dirname, expanduser, splitext
import pyexiv2

from image_tools.ImageToolsShared import ImageFileInfoTool, getTestFilePaths
from py_base.Job import Job
from py_base.PySystemMock import PySystemMock

FILENAME_SCALED_SUFFIX = '.scaled'
DEFAULT_SCALE_SIZE = 1200

class ImageScaler(Job):

    def defineCustomArguments(self, parser):
        parser.add_argument('-l',
                            '--limit-size',
                            metavar='x',
                            default=DEFAULT_SCALE_SIZE,
                            help="Limit the size of the longest dimension of the original to x pixels (default %d)" % DEFAULT_SCALE_SIZE,
                            )
        parser.add_argument('-g',
                            '--greyscale',
                            action='store_true',
                            default=False,
                            help="Convert to greyscale",
                            )
        parser.add_argument('path',
                            nargs='*',
                            help="Path(s) of the image(s) to scale, space separated if multiple",
                            )

    def doRunSteps(self, imageTool=None):
        if imageTool == None:
            self.imageTool = ImageFileInfoTool(self.out, self.system)
        else:
            self.imageTool = imageTool
        for filename in self.getNormalizedPathArgument():
            if self.imageTool.isImageFilename(filename):
                self.processImageFile(filename)

    def processImageFile(self, sourceFileName):
        self.out.indent("Scaling file: %s" % sourceFileName)
        targetFileName = self.getTargetFileName(sourceFileName)

        self.out.put("reading image file...", self.out.LOG_LEVEL_MUNDANE)
        sourceImage = Image.open(sourceFileName)

        self.processImage(sourceImage, targetFileName)
        try:
            self.imageTool.copyExifMetadata(sourceFileName, targetFileName)
        except:
            # probably in debug mode - no .scaled.jpg file was created
            if not self.inDebugMode():
                self.out.put("ERROR: Unable to copy EXIF metadata to %s. Was it scaled/saved correctly?" % targetFileName,
                             self.out.LOG_LEVEL_ERROR)

        self.out.unIndent()

    def processImage(self, sourceImage, targetFileName):
        size = (self.arguments['limit_size'], self.arguments['limit_size'])
        if self.arguments['greyscale']:
            self.out.put("converting image to greyscale...", self.out.LOG_LEVEL_VERBOSE)
            sourceImage = sourceImage.convert("L")

        self.out.put("scaling image...", self.out.LOG_LEVEL_MUNDANE)
        sourceImage.thumbnail(size, Image.ANTIALIAS)

        if self.inDebugMode():
            # if we're running in mock mode, then we shouldn't be changing anything on the filesystem.
            self.out.put("DEBUG: Not writing image file because we're in mock mode")
        else:
            self.out.put("writing image file...", self.out.LOG_LEVEL_MUNDANE)
            sourceImage.save(targetFileName)

    def getTargetFileName(self, sourceFileName):
        self.out.put("Setting target filename...", self.out.LOG_LEVEL_VERBOSE)
        splitFileName = splitext(sourceFileName)
        targetFileName = splitFileName[0] + FILENAME_SCALED_SUFFIX + splitFileName[1]
        self.out.put("source path: %s" % sourceFileName, self.out.LOG_LEVEL_VERBOSE)
        self.out.put("target path: %s" % targetFileName, self.out.LOG_LEVEL_VERBOSE)
        return targetFileName

    def inDebugMode(self):
        return self.system.__class__ == PySystemMock

if __name__ == "__main__":
    from py_base.Job import runMockJob

    # clean out old runs
    from subprocess import Popen
    Popen(['rm', '-f', '%s/test/*.scaled.jpg' % dirname(__file__)])

    runMockJob(ImageScaler,
               arguments={'limit_size': 100,
                          'greyscale': True,
                          'path': getTestFilePaths()})

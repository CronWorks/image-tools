from os.path import dirname, realpath
import unittest

from image_tools.ImageDateStamper import ImageDateStamper
from image_tools.ImageScaler import ImageScaler
from image_tools.ImageToolsShared import ImageFileInfoTool
from py_base.JobOutput import JobOutput


class ImageToolsTest(unittest.TestCase):
    out = None
    sys = None
    dateStamper = None
    infoGrabber = None
    scaler = None
    testDir = None

    def setUp(self):
        self.out = JobOutput()
        self.out.disableLogFile()
        self.sys = PySystemMock(self.out)
        self.dateStamper = ImageDateStamper(self.out, self.sys)
        self.testDir = '%s/test' % realpath(dirname(__file__))
        self.dateStamper.arguments['path'] = [self.testDir]
        self.infoGrabber = ImageFileInfoTool(self.out, self.sys)
        self.scaler = ImageScaler(self.out, self.sys)

    def testTrivialShouldPass(self):
        pass

    def testGetFileInfoFromFilename(self):
        expectedResult = {'year':'2011', 'month':'02', 'day':'12', 'title':'The title of the Picture', 'extension':'Jpg'}
        self.assertEqual(self.infoGrabber.getFileInfoFromFilename('2011-02.12-The title of the Picture.Jpg'), expectedResult)
        self.assertEqual(self.infoGrabber.getFileInfoFromFilename('2011.02-12 _  The title of the Picture.Jpg'), expectedResult)

        expectedResult['hour'] = '11'
        expectedResult['minute'] = '33'
        self.assertEqual(self.infoGrabber.getFileInfoFromFilename('2011-02.12 11:33-The title of the Picture.Jpg'), expectedResult)
        self.assertEqual(self.infoGrabber.getFileInfoFromFilename('2011.02_12.11.33   The title of the Picture.Jpg'), expectedResult)
        self.assertEqual(self.infoGrabber.getFileInfoFromFilename('2011 02 12 11:33  The title of the Picture.Jpg'), expectedResult)

    def testGetTargetFileName(self):
        # very brief. Partly we're testing that Jpg is not converted to jpg; otherwise, very stupid test.
        fileInfo = {'year':'11', 'month':'2', 'day':'12', 'hour':'11', 'minute':'33', 'title':'The title of the Picture', 'extension':'Jpg'}
        self.assertEqual(self.dateStamper.getTargetFileName(fileInfo), '11-2-12 The title of the Picture.Jpg')
        fileInfo['year'] = '2011'
        fileInfo['month'] = '02'
        self.assertEqual(self.dateStamper.getTargetFileName(fileInfo), '2011-02-12 The title of the Picture.Jpg')
        self.dateStamper.arguments['time'] = True
        self.assertEqual(self.dateStamper.getTargetFileName(fileInfo), '2011-02-12 11.33 The title of the Picture.Jpg')

    def testGetFileNamesToStamp(self):
        fileNames = ['2011-07-30 P0002394.JPG',
                     'ImageDateStamperTest.pyc',
                     'Named image file.JPG',
                     'Non Image File.txt']
        self.assertEqual(self.dateStamper.getFileNamesToStamp(), fileNames)

    def testGetFileInfo(self):
        self.assertEqual([], self.infoGrabber.getFileInfo('%s/Named image file.JPG' % self.testDir))

    def testScaleImage(self):
        self.scaler.scaleImageFile('/home/luke/Public/AllStarTest/2011.07.25 picture folder name with spaces/subfolder/P1040425.JPG')

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

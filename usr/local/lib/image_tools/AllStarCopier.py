#!/usr/bin/python
from os import listdir
from os.path import abspath, basename, dirname, exists, isdir
from re import match
import sys

from image_tools.ImageToolsShared import ImageFileInfoTool, getTestFilePaths
from py_base.Job import Job


REGEX_ALL_STARS_FOLDER = '^[Aa]ll ?[Ss]tars?$'
DEFAULT_ALL_STAR_FOLDER_NAME = 'AllStars'

class AllStarCopier(Job):

    def defineCustomArguments(self, parser):
        parser.add_argument('path',
                            nargs='*',
                            help="Path(s) of the image(s) to scale, space separated if multiple",
                            )
    def doRunSteps(self, imageTool=None):
        if imageTool == None:
            imageTool = ImageFileInfoTool(self.out, self.system)
        for fullPath in self.getNormalizedPathArgument():
            fullPath = imageTool.renameFileIfNecessary(fullPath)
            self.copyToAllStars(fullPath)

    def copyToAllStars(self, sourceFullPath, currentPath=None):
        '''
        Recursive function to copy an image (sourceFullPath) to the first all star folder.

        Recursion level is indicated by currentPath: if None, it's the first level;
        if /path/to/some/directory, then that's the current PARENT folder that's being searched.

        REMEMBER: all-star folders are always CHILDREN of some ancestor of the original image.
        '''
        if currentPath == None:
            currentPath = dirname(sourceFullPath)
        self.out.put('looking in %s for an AllStars folder...' % currentPath)
        if currentPath == '/':
            # we got all the way to the root without finding an all star folder to use.
            # create a new all star folder as a sibling of the image.
            currentPath = dirname(sourceFullPath)
            allStarsFullPath = '%s/%s' % (currentPath, DEFAULT_ALL_STAR_FOLDER_NAME)

            self.out.put("Creating new all-star folder %s..." % (allStarsFullPath))
            self.system.mkdir(allStarsFullPath)
            self._copyToAllStars(sourceFullPath, allStarsFullPath)
        else:
            allStarsFullPaths = self.getAllStarsFullPaths(currentPath)
            if not allStarsFullPaths:
                # recurse
                self.out.put('no all star folders at the current level.')
                self.copyToAllStars(sourceFullPath, currentPath=dirname(currentPath))
            for allStarsFullPath in allStarsFullPaths:
                self.out.put('found existing AllStar folder %s.' % allStarsFullPath)
                self._copyToAllStars(sourceFullPath, allStarsFullPath)

    def _copyToAllStars(self, sourceFullPath, allStarsFullPath):
        targetFullPath = '%s/%s' % (allStarsFullPath, basename(sourceFullPath))
        self.out.put("Copying %s to All-Star folder %s..." % (sourceFullPath, allStarsFullPath))
        self.system.copy(sourceFullPath, targetFullPath)

    def getAllStarsFullPaths(self, path):
        self.out.put("Looking for all stars path in %s" % (path), self.out.LOG_LEVEL_VERBOSE)
        result = []

        # list the subfolder contents of path
        # I'm using sorted() here so that there is consistency
        # in the order of preference when multiple folders exist
        for filename in sorted(listdir(path)):
            # does this name match the regex?
            if not self.isAllStarFolder(filename):
                self.out.put("- filename %s failed all star regex" % filename, self.out.LOG_LEVEL_DEBUG)
                continue

            self.out.put("- all star filename %s found! (not a confirmed directory yet)" % filename, self.out.LOG_LEVEL_DEBUG)

            # is the matching name a folder?
            allStarsFullPath = "%s/%s" % (path, filename)
            if isdir(allStarsFullPath):
                # we've found what we are looking for
                self.out.put("- full path %s is a confirmed directory! Adding to result list." % allStarsFullPath, self.out.LOG_LEVEL_DEBUG)
                result.append(allStarsFullPath)
        return result

    def isAllStarFolder(self, filename):
        return match(REGEX_ALL_STARS_FOLDER, filename)

if __name__ == "__main__":
    from py_base.Job import runMockJob
    runMockJob(AllStarCopier, arguments={'path': getTestFilePaths()})

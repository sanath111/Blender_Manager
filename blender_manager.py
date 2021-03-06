#!/usr/bin/python3
# *-* coding: utf-8 *-*
__author__ = "Sanath Shetty K"
__license__ = "GPL"
__email__ = "sanathshetty111@gmail.com"

import debug
import argparse
import glob
import os
import sys
import re
import pexpect
import setproctitle
import subprocess
import shlex
from collections import OrderedDict
import time
import threading
import traceback
import pathlib
import json
from PIL import Image
from multiprocessing import Pool
from bs4 import BeautifulSoup
import urllib
import re

from PyQt5.QtWidgets import QApplication, QFileSystemModel, QListWidgetItem
from PyQt5 import QtCore, uic, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


projDir = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-1])
sys.path.append(projDir)

homeDir = os.path.expanduser("~")
assDir = homeDir + "/Documents/blender_manager/"
if os.path.exists(assDir):
    pass
else:
    os.mkdir(assDir)

main_ui_file = os.path.join(projDir, "blender_manager.ui")
debug.info(main_ui_file)

confFile = homeDir+os.sep+".config"+os.sep+"blender_manager.json"

addedLinks = {'lts':{},'stable':{},'daily':{}}
versionLinks = {'lts':{},'stable':{},'daily':{}}

ltsVers = ["Blender2.83","Blender2.93"]
stableVers = ["Blender2.79","Blender2.80","Blender2.81","Blender2.82","Blender2.90","Blender2.91","Blender2.92","Blender3.0"]



class blenderLauncherWidget():
    def __init__(self):
        global listIcon
        global iconsIcon

        # self.threadpool = QtCore.QThreadPool()

        self.main_ui = uic.loadUi(main_ui_file)
        self.main_ui.setWindowTitle("BLENDER MANAGER")
        self.main_ui.setWindowIcon(QtGui.QIcon(os.path.join(projDir, "icons", "blender_logo.svg")))

        sS = open(os.path.join(projDir, "dark.qss"), "r")
        self.main_ui.setStyleSheet(sS.read())
        sS.close()

        self.main_ui.comboBox_LTS.setToolTip("Add a version")
        self.main_ui.comboBox_Stable.setToolTip("Add a version")
        self.main_ui.comboBox_Daily.setToolTip("Add a version")

        self.initLoad()

        self.main_ui.comboBox_LTS.currentIndexChanged.connect(lambda x, combo_ui=self.main_ui.comboBox_LTS,
                                                                     list_ui=self.main_ui.listWidget_LTS,
                                                                     type="lts": self.addItemToList(combo_ui,list_ui,type))
        self.main_ui.comboBox_Stable.currentIndexChanged.connect(lambda x, combo_ui=self.main_ui.comboBox_Stable,
                                                                        list_ui=self.main_ui.listWidget_Stable,
                                                                        type="stable": self.addItemToList(combo_ui,list_ui,type))
        self.main_ui.comboBox_Daily.currentIndexChanged.connect(lambda x, combo_ui=self.main_ui.comboBox_Daily,
                                                                       list_ui=self.main_ui.listWidget_Daily,
                                                                       type="daily": self.addItemToList(combo_ui,list_ui, type))

        self.main_ui.setDownloadPathAction.triggered.connect(self.setDownloadPath)
        self.main_ui.clearLocalDownloadsAction.triggered.connect(self.clearLocalDownloads)

        self.main_ui.show()
        self.main_ui.update()

        qtRectangle = self.main_ui.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.main_ui.move(qtRectangle.topLeft())


    def initLoad(self):
        for ver in ltsVers:
            self.loadVersions(self.main_ui.comboBox_LTS,"download.blender.org/release/",ver,"lts")
        for ver in stableVers:
            self.loadVersions(self.main_ui.comboBox_Stable,"download.blender.org/release/",ver,"stable")
        self.loadVersions(self.main_ui.comboBox_Daily,"builder.blender.org/download/","daily","daily")

        global confFile
        global addedLinks

        if os.path.exists(confFile):
            f = open(confFile)
            data = json.load(f)
            addedLinks = data
        else:
            with open(confFile, 'w') as conf_file:
                json.dump(addedLinks, conf_file, sort_keys=True, indent=4)

        self.initLtsList()
        self.initDailyList()
        self.initStableList()


    def initLtsList(self):
        self.initList(self.main_ui.listWidget_LTS,"lts")


    def initStableList(self):
        self.initList(self.main_ui.listWidget_Stable, "stable")


    def initDailyList(self):
        self.initList(self.main_ui.listWidget_Daily, "daily")


    def initList(self, list_ui, type):
        list_ui.clear()
        for key in addedLinks[type]:
            self.loadItems(list_ui,str(key),type)


    def loadVersions(self, ui, site, ver, type):
        ui.clear()
        ui.clearEditText()

        build_str = "https://"+site+ver+"/"

        lT = getlinkThread(build_str,type,app)
        lT.finished.connect(lambda ui=ui, type=type: self.loadLinks(ui, type))
        lT.start()


    def loadLinks(self,ui,type):
        labels = [""]+[str(key) for key in versionLinks[type]]
        labels.sort()
        # debug.info(labels)
        ui.clear()
        ui.addItems(labels)


    def addItemToList(self, combo_ui, list_ui, type):
        currText = str(combo_ui.currentText()).strip()
        debug.info(currText)
        if currText:
            if currText in [key for key in addedLinks[type]]:
                pass
            else:
                addedLinks[type][currText] = versionLinks[type][currText]
                with open(confFile, 'w') as conf_file:
                    json.dump(addedLinks, conf_file, sort_keys=True, indent=4)

                self.loadItems(list_ui,currText,type)
            combo_ui.setCurrentIndex(0)


    def delItemFromList(self, list_ui, label, type):
        confirm = QtWidgets.QMessageBox()
        self.setStyle(confirm)
        confirm.setWindowTitle("Warning!")
        confirm.setText("<b>Permanently Delete downloaded file?</b>" + "\n")
        confirm.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
        selection = confirm.exec_()
        if (selection == QtWidgets.QMessageBox.Yes):
            # debug.info(list_ui)
            # debug.info(label)
            # debug.info(type)
            items = os.listdir(assDir)
            for item in items:
                if label in item:
                    # debug.info("Removing: " + assDir+item)
                    removeCmd = "rm -frv \"{0}\" ".format(assDir+item)
                    debug.info(shlex.split(removeCmd))
                    if removeCmd:
                        p = subprocess.Popen(shlex.split(removeCmd))
                        p.communicate()
                    #     self.initLoad()

            del addedLinks[type][label]
            with open(confFile, 'w') as conf_file:
                json.dump(addedLinks, conf_file, sort_keys=True, indent=4)
            self.initList(list_ui, type)


    # def rmItemFromList(self, list_ui, label, type):
    #     # addedLinks[type].pop(label)
    #     del addedLinks[type][label]
    #     with open(confFile, 'w') as conf_file:
    #         json.dump(addedLinks, conf_file, sort_keys=True, indent=4)
    #     self.initList(list_ui,type)


    def loadItems(self, list_ui, label, type):
        if label:
            name = ""
            link = ""
            # debug.info(addedLinks[type][label])
            for key,value in addedLinks[type][label].items():
                name = key
                link = value
            labelDir = assDir+'.'.join(name.split('.')[:-2])

            downloadButt = QtWidgets.QPushButton()
            progBar = QtWidgets.QProgressBar()
            versionLabel = QtWidgets.QLabel()
            # rmButt = QtWidgets.QPushButton()
            delButt = QtWidgets.QPushButton()

            downloadButt.setMaximumWidth(200)
            progBar.setMaximumWidth(200)
            delButt.setMaximumWidth(30)
            # rmButt.setMaximumWidth(30)

            delButt.setToolTip("Delete version from disk")
            # rmButt.setToolTip("Remove version from list")

            if os.path.exists(labelDir):
                downloadButt.setText("Launch")
                downloadButt.clicked.connect(lambda x, path=labelDir: self.launchVersion(path))
            else:
                downloadButt.setText("Download")
                downloadButt.clicked.connect(lambda x, list_ui=list_ui,type=type,link=link,
                                             name=name,dbutt=downloadButt,bar=progBar,delButt=delButt :
                                             self.downloadVersion(list_ui,type,link,name,dbutt,bar,delButt))

            versionLabel.setText(str(label))

            # rmButt.setIcon(QtGui.QIcon(os.path.join(projDir, "icons", "minus.svg")))
            delButt.setIcon(QtGui.QIcon(os.path.join(projDir, "icons", "delete.svg")))

            delButt.clicked.connect(lambda x, list_ui=list_ui, label=label: self.delItemFromList(list_ui,label,type))
            # rmButt.clicked.connect(lambda x, list_ui=list_ui, label=label: self.rmItemFromList(list_ui,label,type))

            itemWidget = QtWidgets.QWidget()
            hl = QtWidgets.QHBoxLayout()
            itemWidget.setLayout(hl)
            hl.addWidget(downloadButt)
            hl.addWidget(progBar)
            hl.addWidget(versionLabel)
            hl.addWidget(delButt)
            # hl.addWidget(rmButt)

            progBar.hide()

            item = QListWidgetItemSort()
            item.setSizeHint(itemWidget.sizeHint() + QtCore.QSize(10, 10))
            list_ui.addItem(item)
            list_ui.setItemWidget(item, itemWidget)


    def updatePrgress(self, prctg, bar):
        bar.setValue(int(prctg))


    def downloadVersion(self,list_ui,type,link,name,dbutt,bar,delButt):
        dbutt.hide()
        bar.show()
        delButt.setEnabled(False)

        dT = downloadThread(link, name, app)
        dT.finished.connect(lambda list_ui=list_ui, type=type : self.initList(list_ui,type))
        dT.progress.connect(lambda x, bar=bar : self.updatePrgress(x,bar))
        dT.start()


    def launchVersion(self,path):
        lT = launchThread(path, app)
        lT.start()


    def setDownloadPath(self):
        debug.info("setting download path")


    def clearLocalDownloads(self):
        debug.info("clearing local downloads")

        confirm = QtWidgets.QMessageBox()
        self.setStyle(confirm)
        confirm.setWindowTitle("Warning!")
        # confirm.setIcon(QtGui.QIcon(QtGui.QPixmap(os.path.join(projDir, "imageFiles", "help-icon-1.png"))))
        # confirm.setIconPixmap(QtGui.QPixmap(os.path.join(projDir, "imageFiles", "help-icon-1.png")))
        confirm.setText("<b>Permanently Delete all item(s)?</b>" + "\n")
        # confirm.setInformativeText(",\n".join(i for i in fileNames))
        confirm.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
        selection = confirm.exec_()
        if (selection == QtWidgets.QMessageBox.Yes):
            items = os.listdir(assDir)
            for item in items:
                removeCmd = "rm -frv \"{0}\" ".format(assDir+item)
                debug.info(shlex.split(removeCmd))
                if removeCmd:
                    p = subprocess.Popen(shlex.split(removeCmd))
                    p.communicate()
                    self.initLoad()
            debug.info("Deleted all downloaded files from "+assDir)


    def setStyle(self,ui):
        sS = open(os.path.join(projDir, "dark.qss"), "r")
        ui.setStyleSheet(sS.read())
        sS.close()



class QListWidgetItemSort(QtWidgets.QListWidgetItem):
    def __lt__(self, other):
        return self.data(QtCore.Qt.UserRole) < other.data(QtCore.Qt.UserRole)

    def __ge__(self, other):
        return self.data(QtCore.Qt.UserRole) > other.data(QtCore.Qt.UserRole)


class downloadThread(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self,link,name,parent):
        super(downloadThread, self).__init__(parent)
        self.link = link
        self.name = name

    def run(self):
        downCmd = "aria2c --summary-interval 1 --download-result=hide -c -s 10 -x 10 -d " + assDir + " " + self.link
        debug.info(downCmd)
        # subprocess.call(shlex.split(downCmd))
        try:
            p = subprocess.Popen(shlex.split(downCmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1,
                                 universal_newlines=True)

            for line in iter(p.stdout.readline, b''):
                if "Download complete" in line:
                    untarCmd = "tar -xvf " + assDir + self.name + " -C " + assDir
                    debug.info(untarCmd)
                    try:
                        subprocess.call(shlex.split(untarCmd))
                        self.finished.emit()
                        return
                    except:
                        debug.info(str(sys.exc_info()))
                    return
                elif "%" in line:
                    synData = (tuple(filter(None, line.strip().split('('))))
                    if synData:
                        prctg = synData[1].split("%")[0].strip()
                        self.progress.emit(int(prctg))
        except:
            debug.info(str(sys.exc_info()))
            return


class launchThread(QThread):
    finished = pyqtSignal()

    def __init__(self,path,parent):
        super(launchThread, self).__init__(parent)
        self.path = path

    def run(self):
        openCmd = self.path + "/blender"
        debug.info(openCmd)
        try:
            subprocess.Popen(shlex.split(openCmd))
            self.finished.emit()
            return
        except:
            debug.info(str(sys.exc_info()))


class getlinkThread(QThread):
    finished = pyqtSignal()

    def __init__(self,build_str,type,parent):
        super(getlinkThread, self).__init__(parent)
        self.build_str = build_str
        self.type = type

    def run(self):
        try:
            htmlPage = urllib.request.urlopen(self.build_str)
            soup = BeautifulSoup(htmlPage, 'html.parser')

            for link in soup.findAll('a', attrs={'href': re.compile("(?=.*linux)(?=.*64)(?=.*.tar)")}):
                downloadLabel = str(link.get('href'))
                downloadLabel = str(downloadLabel.replace(self.build_str, ""))
                name = downloadLabel.split('-')[1:2][0]
                if self.type == "daily":
                    name = "-".join(downloadLabel.split('-')[1:3])
                # debug.info(name)
                downloadLink = self.build_str + downloadLabel
                if downloadLabel.endswith(".tar.xz") or downloadLabel.endswith(".tar.bz2"):
                    versionLinks[self.type][name] = {}
                    versionLinks[self.type][name][downloadLabel] = downloadLink
            self.finished.emit()
            return
        except:
            debug.info(str(sys.exc_info()))


if __name__ == '__main__':
    setproctitle.setproctitle("BLENDER_MANAGER")
    app = QtWidgets.QApplication(sys.argv)
    window = blenderLauncherWidget()
    sys.exit(app.exec_())

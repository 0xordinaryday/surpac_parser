# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SurpacParser
                                 A QGIS plugin
 Imports data from and exports data to Surpac String File Format
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-11-12
        git sha              : $Format:%H$
        copyright            : (C) 2019 by David Gibbons
        email                : david@gibbons.digital
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import json
from datetime import datetime
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog
from qgis.core import QgsProject, Qgis, QgsFeatureRequest, QgsDistanceArea, QgsGeometry, QgsPoint, QgsPointXY, QgsWkbTypes

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .surpac_parser_dialog import SurpacParserDialog
import os.path


class SurpacParser:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SurpacParser_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SurpacParser')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SurpacParser', message)
        
    def select_output_file(self):
        filename, _filter = QFileDialog.getSaveFileName(
            self.dlg, "Select output file ","", '*.str')
        self.dlg.lineEdit.setText(filename)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/surpac_parser/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Surpac Parser'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&SurpacParser'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = SurpacParserDialog()
            self.dlg.pushButton.clicked.connect(self.select_output_file)
                
        # Fetch the currently loaded layers
        layers = QgsProject.instance().layerTreeRoot().children()
        # Clear the contents of the layerBox from previous runs
        self.dlg.layerBox.clear()
        # Populate the layerBox with names of all the loaded layers
        self.dlg.layerBox.addItems([layer.name() for layer in layers])

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            filename = self.dlg.lineEdit.text()
            with open(filename, 'w') as output_file:
                selectedLayerIndex = self.dlg.layerBox.currentIndex()
                selectedLayer = layers[selectedLayerIndex].layer()
                fieldnames = [field.name() for field in selectedLayer.fields()]
                # write header
                # get date/time
                now = datetime.now()
                dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                header1 = 'Exported from QGIS,' + dt_string + ',,' + '\n'
                header2 = '0,           0.000,           0.000,           0.000,           0.000,           0.000,           0.000' + '\n'
                SEGBREAK = '0, 0.000, 0.000, 0.000,' + '\n'
                output_file.write(header1)
                output_file.write(header2)
                # write feature attributes
                for f in selectedLayer.getFeatures():
                
                    # 
                    # retrieve every feature with its geometry and attributes
                    # print("Feature ID: ", f.id()) # don't need this
                    # fetch geometry
                    # show some information about the feature geometry
                    geom = f.geometry()
                    geomSingleType = QgsWkbTypes.isSingleType(geom.wkbType())
                    
                    # fetch attributes - need for D fields
                    attrs = f.attributes()
                    # attrs is a list. It contains all the attribute values of this feature
                    # print(attrs)
                    
                    d_fields = ''
                    if len(attrs) > 0:  # has at least one D field
                        for item in attrs:
                            d_fields = d_fields + str(item) + ','
                            
                    DUMMY_Z = '0'  # change this later
                    DUMMY_STR = '1'  # change this later
                    
                    if geom.type() == QgsWkbTypes.PointGeometry:
                        # the geometry type can be of single or multi type
                        if geomSingleType:
                            parsed_json = json.loads(geom.asJson())  # convert to python dictionary
                            coordinate_list = parsed_json.get('coordinates')  # is a single list of coordinates of length 2, 3 or 4 (XY), (XYZ) or (XYZM)
                            if len(coordinate_list) > 2:
                                    DUMMY_Z = str(coordinate_list[2])
                            line = DUMMY_STR + ',' + str(coordinate_list[1]) + ',' + str(coordinate_list[0]) + ',' + DUMMY_Z + ',' + d_fields + '\n' + SEGBREAK
                            output_file.write(line)
                        else:
                            ''' multipoint geometry delivers results as a *list* of qgis points if called via geom.asMultiPoint()
                                however, like asPoint, this drops the Z values (if present)
                                calling asJson gives a JSON object that includes the Z values
                                so we call asJson, convert to a Python dictionary and then get the coordinates which have a key value
                                of 'coordinates'. The value is a list of lists, where each inner list has this form:
                                [485490.1175313188, 5438619.58900284, 0.0]
                                there may be only one inner list
                                the inner list length will be two (2) if there are no Z coordinates
                            '''
                            parsed_json = json.loads(geom.asJson())  # convert to python dictionary
                            coordinate_list = parsed_json.get('coordinates')
                            for inner_list in coordinate_list:
                                if len(inner_list) > 2:
                                    DUMMY_Z = str(inner_list[2])
                                line = DUMMY_STR + ',' + str(inner_list[1]) + ',' + str(inner_list[0]) + ',' + DUMMY_Z + ',' + d_fields + '\n' + SEGBREAK
                                output_file.write(line)
                    elif geom.type() == QgsWkbTypes.LineGeometry:
                        if geomSingleType:
                            parsed_json = json.loads(geom.asJson())  # convert to python dictionary
                            coordinate_list = parsed_json.get('coordinates')
                            for inner_list in coordinate_list:
                                if len(inner_list) > 2:
                                    DUMMY_Z = str(inner_list[2])
                                line = DUMMY_STR + ',' + str(inner_list[1]) + ',' + str(inner_list[0]) + ',' + DUMMY_Z + ',' + d_fields + '\n'
                                output_file.write(line)
                            output_file.write(SEGBREAK)
                        else:
                            # multipolyline - nests two deep - so outer list, middle list is a list of segments, inner lists are lists of points
                            parsed_json = json.loads(geom.asJson())  # convert to python dictionary
                            coordinate_list = parsed_json.get('coordinates')
                            for segment_list in coordinate_list:
                                for inner_list in segment_list:
                                    if len(inner_list) > 2:
                                        DUMMY_Z = str(inner_list[2])
                                    line = DUMMY_STR + ',' + str(inner_list[1]) + ',' + str(inner_list[0]) + ',' + DUMMY_Z + ',' + d_fields + '\n'
                                    output_file.write(line)
                                output_file.write(SEGBREAK)  # after each segment
                    elif geom.type() == QgsWkbTypes.PolygonGeometry:
                        if geomSingleType:  # essentially the same as multipolyline
                            parsed_json = json.loads(geom.asJson())  # convert to python dictionary
                            coordinate_list = parsed_json.get('coordinates')
                            for segment_list in coordinate_list:
                                for inner_list in segment_list:
                                    if len(inner_list) > 2:
                                        DUMMY_Z = str(inner_list[2])
                                    line = DUMMY_STR + ',' + str(inner_list[1]) + ',' + str(inner_list[0]) + ',' + DUMMY_Z + ',' + d_fields + '\n'
                                    output_file.write(line)
                                output_file.write(SEGBREAK)  # after each segment
                        else:
                            # this one nests four deep for some reason
                            parsed_json = json.loads(geom.asJson())  # convert to python dictionary
                            coordinate_list = parsed_json.get('coordinates')
                            for outer_most_list in coordinate_list:
                                for segment_list in outer_most_list:
                                    for inner_list in segment_list:
                                        if len(inner_list) > 2:
                                            DUMMY_Z = str(inner_list[2])
                                        line = DUMMY_STR + ',' + str(inner_list[1]) + ',' + str(inner_list[0]) + ',' + DUMMY_Z + ',' + d_fields + '\n'
                                        output_file.write(line)
                                    output_file.write(SEGBREAK)  # after each segment
                    else:
                        print("Unknown or invalid geometry")
                                    
                    # line = ','.join(str(f[name]) for name in fieldnames) + '\n'
                    # output_file.write(line)
                footer1 = '0, 0.000, 0.000, 0.000,' + '\n'   # always have SEGBREAK at end of segment, so don't need this
                footer2 = '0, 0.000, 0.000, 0.000, END' + '\n'
                # output_file.write(footer1)
                output_file.write(footer2)
            self.iface.messageBar().pushMessage("Success", "Output file written at " + filename, level=Qgis.Success, duration=3)

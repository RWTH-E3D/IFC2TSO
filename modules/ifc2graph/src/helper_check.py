import os

import uuid
import shutil
from zipfile import ZipFile
from lxml import etree as ET
from datetime import datetime

from rtree import index
import numpy as np


# Funktionen zum Analysieren der enthaltenen Informationen zu technischen Systemen in einem IFC-Modell
def check_header(model, link):
    # Analyse der Headerinformationen zu Autor, exportierendem System, IFC-Version und MVD
    header = model.wrapped_data.header

    result_dict = dict()
    result_dict['ifc_mvd'] = header.file_description.description[0]
    result_dict['ifc_author'] = header.file_name.author[0]
    result_dict['ifc_originating_system'] = header.file_name.originating_system
    result_dict['ifc_schema'] = model.wrapped_data.schema
    result_dict['ifc_name'] = link

    return result_dict


def check_for_relationships(model):
    # Analyse der verwendeten Beziehungsklasse zur Zuordnung von Ports
    global NESTS

    result_dict = dict()
    ifcrelconnectsporttoelement = 0
    ifcrelnests = 0
    ports = model.by_type('IfcDistributionPort')
    for port in ports:
        try:
            if port.ContainedIn:
                ifcrelconnectsporttoelement += 1
        except AttributeError:
            pass

        try:
            if port.Nests:
                ifcrelnests += 1
        except AttributeError:
            pass

    if ifcrelnests > ifcrelconnectsporttoelement:
        rel = 'IfcRelNests'
        NESTS = True
    else:
        rel = 'IfcRelConnectsPortToElement'
        NESTS = False

    result_dict['IfcRelNests'] = ifcrelnests
    result_dict['IfcRelConnectesPortToElement'] = ifcrelconnectsporttoelement
    result_dict['RelPortToElement'] = rel

    return result_dict, NESTS


def check_classes(model):
    # Analyse, Gruppierung und Ablage der Elementklassifizierungen im IFC-Modell für nachgelagerte Prozesse

    main_classes = ['IfcSpatialElement', 'IfcBuildingElement', 'IfcDistributionElement', 'IfcDistributionPort']

    result_dict = dict()
    for ifc_class in main_classes:
        list_entities = model.by_type(ifc_class)
        for ifc_entity in list_entities:
            classification = ifc_entity.is_a()
            if classification not in result_dict:
                result_dict[classification] = {}

            try:
                entity_type = ifc_entity.PredefinedType
                if not entity_type:
                    entity_type = 'NOTDEFINED'
            except AttributeError:
                entity_type = 'NOTDEFINED'

            if entity_type in result_dict[classification]:
                result_dict[classification][entity_type] += 1
            else:
                result_dict[classification][entity_type] = 1

    return result_dict


def check_systems(model):
    # Analyse der Systemzuordnungen im IFC-Modell für nachgelagerte Prozesse
    result_dict = dict()
    list_entities = model.by_type('IfcSystem')

    for ifc_entity in list_entities:
        classification = ifc_entity.is_a()
        name = ifc_entity.Name
        globalid = ifc_entity.GlobalId
        try:
            entity_type = ifc_entity.PredefinedType
            if not entity_type:
                entity_type = 'NOTDEFINED'
        except AttributeError:
            entity_type = 'NOTDEFINED'

        result_dict[globalid] = {'Name': name, 'Classification': classification, 'Type': entity_type}

    return result_dict


def check_classes_for_ports(model):
    # Check if there are distribution elements without an assigned port

    main_classes = ['IfcDistributionElement', 'IfcBuildingElementProxy']

    result_dict = dict()
    result_dict['Without_ports'] = dict()
    result_dict['With_unassigned_ports'] = dict()
    result_dict['Elements_without_ports'] = dict()
    result_dict['Elements_without_ports']['GlobalIds'] = []
    for ifc_class in main_classes:
        list_entities = model.by_type(ifc_class)
        for ifc_entity in list_entities:
            classification = ifc_entity.is_a()
            try:
                entity_type = ifc_entity.PredefinedType
                if not entity_type:
                    entity_type = 'NOTDEFINED'
            except AttributeError:
                entity_type = 'NOTDEFINED'
            classification = classification + '.' + entity_type

            if NESTS:
                if not ifc_entity.IsNestedBy:
                    if classification in result_dict['Without_ports']:
                        result_dict['Without_ports'][classification].append(ifc_entity.GlobalId)
                        result_dict['Elements_without_ports']['GlobalIds'].append(ifc_entity.GlobalId)
                    else:
                        result_dict['Without_ports'][classification] = []
                        result_dict['Without_ports'][classification].append(ifc_entity.GlobalId)
                        result_dict['Elements_without_ports']['GlobalIds'].append(ifc_entity.GlobalId)
                else:
                    tmp_list = []
                    for port in ifc_entity.IsNestedBy[0].RelatedObjects:
                        if (len(port.ConnectedTo) + len(port.ConnectedFrom)) == 0:
                            tmp_list.append(port)

                    if len(tmp_list) > 0:
                        if classification in result_dict['With_unassigned_ports']:
                            result_dict['With_unassigned_ports'][classification].append(ifc_entity.GlobalId)
                        else:
                            result_dict['With_unassigned_ports'][classification] = []
                            result_dict['With_unassigned_ports'][classification].append(ifc_entity.GlobalId)

    return result_dict


def check_ports_for_unassigned(model):
    # Check if there are distribution ports which are not connected to another port

    main_classes = ['IfcDistributionPort']

    result_dict = dict()
    for ifc_class in main_classes:
        list_entities = model.by_type(ifc_class)
        for ifc_entity in list_entities:
            classification = ifc_entity.is_a()

            if ifc_entity.ConnectedTo:
                connections = True
            else:
                if ifc_entity.ConnectedFrom:
                    connections = True
                else:
                    connections = False

            if not connections:
                if classification in result_dict:
                    result_dict[classification].append(ifc_entity.GlobalId)
                else:
                    result_dict[classification] = []

    return result_dict


def write_infos(input_dict, args):
    # Konsolidierung und Ausgabe der Analyseergebnisse in einer Datei im TXT-Format

    f = open(os.path.dirname(args.input_file) + '/INFO_' + os.path.basename(args.input_file)[:-4] + ".txt", "w")
    for categorie, main_dict in input_dict.items():
        f.write(categorie.upper() + '\n')
        if categorie.upper() == 'INVESTIGATED CLASSES':
            for key, value in main_dict.items():
                f.write("\t{}".format(key.ljust(40)) + '\n')
                for key_class, total in value.items():
                    f.write("\t\t{}\t\t{}".format(key_class.ljust(40), total) + '\n')
                f.write('\n')
        elif categorie.upper() == 'INVESTIGATED SYSTEMS':
            for key, value in main_dict.items():
                f.write("\t{}".format(key.ljust(40)) + '\n')
                for key_class, total in value.items():
                    f.write("\t\t{}\t\t{}".format(key_class.ljust(40), total) + '\n')
                f.write('\n')
        elif categorie.upper() == 'POSSIBLE MATCHES':
            for x in main_dict:
                f.write("\tElement-ID {} Port-ID {}\t\t\tPort-ID {} Element-ID {}".format(x['source_elem_id'], x['source_port_id'], x['sink_port_id'], x['sink_elem_id']) + '\n')
        else:
            for key, value in main_dict.items():
                f.write("\t{}\t\t\t{}".format(key.ljust(40), value) + '\n')
        f.write("\n")


# Funktionen zum Anlagen von BCF-Datein
def create_bcf(bcf_dict, args, zipped=True):
    # Erstellung einer BCF_Datei der Version 2.1
    # Strukur der BCF-Datei kann der Dokumentation von buildingSMART entnommen werden

    input_dict = dict()
    input_dict['markup'] = dict()
    input_dict['markup']['guid'] = str(uuid.uuid4())
    input_dict['markup']['viewpoint_guid'] = str(uuid.uuid4())

    input_dict['markup']['title'] = bcf_dict['Title']
    input_dict['markup']['description'] = bcf_dict['Description']

    input_dict['viewpoint'] = dict()
    input_dict['viewpoint']['guid'] = input_dict['markup']['viewpoint_guid']

    input_dict['viewpoint']['visibility'] = bcf_dict['Visibility']
    input_dict['viewpoint']['Exceptions'] = bcf_dict['Exceptions']
    input_dict['viewpoint']['Selections'] = bcf_dict['Selections']

    main_guid = input_dict['markup']['guid']

    filepath_1 = os.path.dirname(args.input_file) + '/' + main_guid
    filepath_2 = os.path.dirname(args.input_file) + '/' + main_guid + '/' + main_guid

    filepath_version = filepath_1 + '/bcf.version'
    filepath_markup = filepath_2 + '/markup.bcf'
    filepath_viewpoint = filepath_2 + '/viewpoint.bcfv'

    os.mkdir(filepath_1)
    os.mkdir(filepath_2)

    create_bcf_version(filepath_version)
    create_bcf_markup(input_dict['markup'], filepath_markup)
    create_bcf_viewpoint(input_dict['viewpoint'], filepath_viewpoint)

    shutil.copyfile('snapshot.png', os.path.dirname(args.input_file) + '/' + main_guid + '/' + main_guid + '/snapshot.png')

    if zipped:
        zip_bcfs([main_guid], args, zipped)

    else:
        return main_guid


def zip_bcfs(list_guid, args, zipped):
    # Komprimierung der erstellten BCF-Dateien

    # Erstellung einer komprimierten BCF-Datei mit mehreren untergeordneten Dateien
    if not zipped:
        now = datetime.now()
        dt_string = now.strftime("%Y-%m-%dT%H-%M-%S")
        folder_name = str(uuid.uuid4())
        os.mkdir(os.path.dirname(args.input_file) + '/' + folder_name)
        for main_guid in list_guid:
            shutil.move(os.path.dirname(args.input_file) + '/' + main_guid + '/' + main_guid, os.path.dirname(args.input_file) + '/' + folder_name + '/' + main_guid)
            shutil.move(os.path.dirname(args.input_file) + '/' + main_guid + '/bcf.version', os.path.dirname(args.input_file) + '/' + folder_name + '/bcf.version')
            shutil.rmtree(os.path.dirname(args.input_file) + '/' + main_guid, ignore_errors=True)

        os.chdir(os.path.dirname(args.input_file) + '/' + folder_name)
        with ZipFile(folder_name + '.bcf', 'w') as zips:
            zips.write('bcf.version')
            for main_guid in list_guid:
                zips.write(main_guid)
                zips.write(main_guid + '/markup.bcf')
                zips.write(main_guid + '/viewpoint.bcfv')
                zips.write(main_guid + '/snapshot.png')

        os.chdir('..')
        os.chdir('..')
        shutil.move(os.path.dirname(args.input_file) + '/' + folder_name + '/' + folder_name + '.bcf', os.path.dirname(args.input_file) + '/' + folder_name + '.bcf')
        shutil.rmtree(os.path.dirname(args.input_file) + '/' + folder_name, ignore_errors=True)

    # Erstellung einer komprimierten BCF-Datei für jede untergeordnete Datei
    else:
        for main_guid in list_guid:
            os.chdir(os.path.dirname(args.input_file) + '/' + main_guid)
            with ZipFile(main_guid + '.bcf', 'w') as zips:
                zips.write('bcf.version')
                zips.write(main_guid)
                zips.write(main_guid + '/markup.bcf')
                zips.write(main_guid + '/viewpoint.bcfv')
                zips.write(main_guid + '/snapshot.png')

            os.chdir("..")
            shutil.move(main_guid + '/' + main_guid + '.bcf', main_guid + '.bcf')
            shutil.rmtree(main_guid, ignore_errors=True)
            os.chdir("..")


def create_bcf_viewpoint(input_dict, link):
    # Erstellung der viewpoint.bcfv als Teil einer BCF-Datei

    output = ET.ElementTree()
    visualizationinfo = ET.Element('VisualizationInfo', Guid=input_dict['guid'])

    # Anlegen der Komponenten
    components = ET.SubElement(visualizationinfo, 'Components')

    selection = ET.SubElement(components, 'Selection')
    for selection_globalid in input_dict['Selections']:
        ET.SubElement(selection, 'Component', IfcGuid=selection_globalid)

    visibility = ET.SubElement(components, 'Visibility', DefaultVisibility=str(input_dict['visibility']))
    exceptions = ET.SubElement(visibility, 'Exceptions')
    for exception_globalid in input_dict['Exceptions']:
        ET.SubElement(exceptions, 'Component', IfcGuid=exception_globalid)

    # Anlegen einer perspektivischen Kamera mit statsichen Werten
    perspectivecamera = ET.SubElement(visualizationinfo, 'PerspectiveCamera')
    cameraviewpoint = ET.SubElement(perspectivecamera, 'CameraViewPoint')
    ET.SubElement(cameraviewpoint, 'X').text = '-2.7754538059234619'
    ET.SubElement(cameraviewpoint, 'Y').text = '-6.5266432762145996'
    ET.SubElement(cameraviewpoint, 'Z').text = '10.918275833129883'
    cameradirection = ET.SubElement(perspectivecamera, 'CameraDirection')
    ET.SubElement(cameradirection, 'X').text = '0.71669578552246094'
    ET.SubElement(cameradirection, 'Y').text = '0.59156417846679688'
    ET.SubElement(cameradirection, 'Z').text = '-0.36938095092773438'
    cameraupvector = ET.SubElement(perspectivecamera, 'CameraUpVector')
    ET.SubElement(cameraupvector, 'X').text = '0.28487721085548401'
    ET.SubElement(cameraupvector, 'Y').text = '0.23512020707130432'
    ET.SubElement(cameraupvector, 'Z').text = '0.92928117513656616'
    ET.SubElement(perspectivecamera, 'FieldOfView').text = '60'

    output._setroot(visualizationinfo)
    output.write(link, encoding='utf-8', xml_declaration=True, pretty_print=True)

    return -1


def create_bcf_markup(input_dict, link):
    # Erstellung der markup.bcf als Teil einer BCF-Datei

    title_text = input_dict['title']
    description_text = input_dict['description']

    author_text = 'Nicolas Pauen'
    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%dT%H:%M:%S")
    viewpoint_text = 'viewpoint.bcfv'
    snapshot_text = 'snapshot.png'

    output = ET.ElementTree()
    markup = ET.Element('Markup')

    # Anlagen des Headers
    header = ET.SubElement(markup, 'Header')
    ET.SubElement(header, 'File').text = ''

    # Anlgen des Themas
    topic = ET.SubElement(markup, 'Topic', Guid=input_dict['guid'])
    ET.SubElement(topic, 'Title').text = title_text
    ET.SubElement(topic, 'CreationDate').text = dt_string
    ET.SubElement(topic, 'CreationAuthor').text = author_text
    ET.SubElement(topic, 'Description').text = description_text

    # Anlagen der Ansichtspunkte
    viewpoints = ET.SubElement(markup, 'Viewpoints',  Guid=input_dict['viewpoint_guid'])
    ET.SubElement(viewpoints, 'Viewpoint').text = viewpoint_text
    ET.SubElement(viewpoints, 'Snapshot').text = snapshot_text

    output._setroot(markup)
    output.write(link, encoding='utf-8', xml_declaration=True, pretty_print=True)

    return -1


def create_bcf_version(link):
    # Anlagen der Grundlagen einer BCF-Datei

    ns = 'http://www.w3.org/2001/XMLSchema-instance'
    location_attribute = '{%s}noNameSpaceSchemaLocation' % ns

    output = ET.ElementTree()
    version = ET.Element('Version', VersionId="2.1", attrib={location_attribute: 'Version.xsd'})
    ET.SubElement(version, 'DetailedVersion').text = "2.1"

    output._setroot(version)
    output.write(link, encoding='utf-8', xml_declaration=True, pretty_print=True)

    return -1


# Funktionen zum Anlegen und Arbeiten mit R-Bäumen
def calculate_absolute_position(entity_plc):
    # Berechnung der absoluten Position der Entität im dreidimensionalen Raum

    if not entity_plc:
        return np.eye(4)

    if not entity_plc.PlacementRelTo:
        parent = np.eye(4)

    else:
        parent = calculate_absolute_position(entity_plc.PlacementRelTo)

    try:
        x_direction = np.array(entity_plc.RelativePlacement.RefDirection.DirectionRatios)
        z_direction = np.array(entity_plc.RelativePlacement.Axis.DirectionRatios)
    except AttributeError:
        x_direction = np.array([1, 0, 0])
        z_direction = np.array([0, 0, 1])

    # Berechnung der y-Richtung als Kreuzprodukt
    y_direction = np.cross(z_direction, x_direction)

    # Festlegung der Transformationsmatrix
    r = np.eye(4)
    r[:-1, :-1] = x_direction, y_direction, z_direction
    r[-1, :-1] = entity_plc.RelativePlacement.Location.Coordinates

    return np.dot(parent, r.T)


def calculate_all_absolute_positions(model):
    # Berechnung der absoluten Position
    result_dict = dict()
    result_dict['Total'] = dict()
    result_dict['IfcSpatialElements'] = dict()
    result_dict['IfcElement'] = dict()
    result_dict['IfcDistributionPort'] = dict()

    # Berechnung der absoluten Position von Elementen der räumlichen Struktur
    spatial_elements = model.by_type('IfcSpatialElement')
    for spatial_elem in spatial_elements:
        spatial_elem_id = spatial_elem.GlobalId
        spatial_elem_pos = calculate_absolute_position(spatial_elem.ObjectPlacement)
        result_dict['IfcSpatialElements'][spatial_elem_id] = spatial_elem_pos.T[-1, :-1]
        result_dict['Total'][spatial_elem_id] = spatial_elem_pos.T[-1, :-1]

    # Berechnung der absoluten Position von Elementen technischer Systeme
    distribution_elements = model.by_type('IfcDistributionElement') + model.by_type('IfcBuildingElementProxy')
    for distribution_elem in distribution_elements:
        distribution_elem_id = distribution_elem.GlobalId
        distribution_elem_pos = calculate_absolute_position(distribution_elem.ObjectPlacement)
        result_dict['IfcElement'][distribution_elem_id] = distribution_elem_pos.T[-1, :-1]
        result_dict['Total'][distribution_elem_id] = distribution_elem_pos.T[-1, :-1]

    # Berechnung der absoluten Position von Ports
    port_elements = model.by_type('IfcDistributionPort')
    for port_elem in port_elements:
        port_elem_id = port_elem.GlobalId
        port_elem_pos = calculate_absolute_position(port_elem.ObjectPlacement)
        result_dict['IfcDistributionPort'][port_elem_id] = port_elem_pos.T[-1, :-1]
        result_dict['Total'][port_elem_id] = port_elem_pos.T[-1, :-1]

    return result_dict


def build_spatial_index(input_dict):
    # Anlegen des R-Baums mit den Positionen der Ports im dreidimensionalen Raum

    result_dict = dict()
    result_mapping = dict()
    p = index.Property()
    p.dimension = 3
    p.dat_extension = 'data'
    p.idx_extension = 'index'
    idx3d = index.Index('3d_index', properties=p)
    i = 1

    for guid, position in input_dict.items():
        idx3d.insert(i, (float(position[0]), float(position[1]), float(position[2])))

        result_mapping[guid] = i
        result_mapping[i] = guid
        i += 1

    result_dict['Spatialindex'] = idx3d
    result_dict['Mapping'] = result_mapping

    return result_dict


def k_nearest_neighbors(index_dict, position_dict, globalid, num_results):
    # Abfrage des R-Baums über eine kNN Abfrage
    result_dict = dict()
    try:
        position = position_dict['Total'][globalid]
    except KeyError:
        print('No position for port ' + globalid)
        result_dict['nearest_element_guid'] = []
        return result_dict

    coordinates = (float(position[0]), float(position[1]), float(position[2]))

    nearest_elements = index_dict['Spatialindex'].nearest(coordinates, num_results=num_results, objects=False)
    nearest_elements_idx = list(nearest_elements)[1:]

    result_dict['nearest_element_guid'] = []
    for nearest_elment_idx in nearest_elements_idx:
        nearest_element_guid = index_dict['Mapping'][nearest_elment_idx]
        result_dict['nearest_element_guid'].append(nearest_element_guid)

    return result_dict


def intersection_neighbors(index_dict, position_dict, globalid, spatial_boundary):
    # Abfrage der topologischen Nachbarn eines Ports mit einer gegebenen GUID
    result_dict = dict()
    try:
        position = position_dict['Total'][globalid]
    except KeyError:
        print('No position for port ' + globalid)
        result_dict['nearest_element_guid'] = []
        return result_dict

    coordinates = (float(position[0] - spatial_boundary), float(position[1] - spatial_boundary),
                   float(position[2] - spatial_boundary), float(position[0] + spatial_boundary),
                   float(position[1] + spatial_boundary), float(position[2] + spatial_boundary))

    nearest_element = index_dict['Spatialindex'].intersection(coordinates, objects=False)
    nearest_elements_idx = list(nearest_element)

    result_dict['nearest_element_guid'] = []
    for nearest_elment_idx in nearest_elements_idx:
        nearest_element_guid = index_dict['Mapping'][nearest_elment_idx]
        result_dict['nearest_element_guid'].append(nearest_element_guid)

    return result_dict


def check_ports(model, info_dict, index_dict, position_dict, spatial_boundary):
    # Anreicherung der topologischen Informationen durch Kontrolle von Elementen mit offenen Ports
    result_dict = dict()
    result_dict['Possible_connected_elements'] = []
    result_dict['No_free_port_nearby'] = []
    if 'IfcDistributionPort' in info_dict['Ports without assignment']:
        list_ports = info_dict['Ports without assignment']['IfcDistributionPort']
        set_ports = set(list_ports)
        for port in list_ports:
            source_port = model.by_guid(port)
            source_port_type = source_port.PredefinedType
            if not source_port_type:
                source_port_type = 'NOTDEFINED'
            if NESTS:
                source_element_idx = source_port.Nests[0].RelatingObject.GlobalId
            else:
                source_element_idx = source_port.ContainedIn[0].RelatedElement.GlobalId

            list_port_idx = intersection_neighbors(index_dict, position_dict, port, spatial_boundary)
            possible_connection = []
            port_idx = None
            for idx in list_port_idx['nearest_element_guid']:

                # Abfangen des abgefragten Ports in den Ergebnisse der Intersection Abfrage
                if idx == port:
                    continue

                # Kontrolle, dass das Ergebnis der Intersection Abfrage nicht zu selben Element gehört
                port_element = model.by_guid(idx)
                if NESTS:
                    element_idx = port_element.Nests[0].RelatingObject.GlobalId
                else:
                    element_idx = port_element.ContainedIn[0].RelatedElement.GlobalId

                if element_idx == source_element_idx:
                    continue

                # Kontrolle, dass der ausgegebene Port ebenfalls keinen topologischen Nachbarn hat
                if idx in set_ports:

                    # Kontrolle, dass die Typen der Ports zueinander passen
                    port_element_type = port_element.PredefinedType
                    if not port_element_type:
                        port_element_type = 'NOTDEFINED'

                    if port_element_type == 'NOTDEFINED' or port_element_type == source_port_type:
                        if element_idx not in possible_connection:
                            possible_connection.append(element_idx)
                            port_idx = idx

            if possible_connection:
                # Wenn mehrere Ports möglich sind, wähle den nächstliegenden
                if len(possible_connection) > 1:
                    list_port_idx = k_nearest_neighbors(index_dict, position_dict, port, 10)
                    list_elem_idx = []
                    nearest_connection = (None, None)
                    for i in list_port_idx['nearest_element_guid']:
                        port_element = model.by_guid(i)
                        if NESTS:
                            element_idx = port_element.Nests[0].RelatingObject.GlobalId
                        else:
                            element_idx = port_element.ContainedIn[0].RelatedElement.GlobalId

                        list_elem_idx.append(element_idx)
                        if element_idx in possible_connection:
                            nearest_connection = (i, element_idx)
                            break

                    if nearest_connection == (None, None):
                        continue
                    tmp_dict = {'source_elem_id': source_element_idx, 'source_port_id': port, 'sink_elem_id': nearest_connection[1], 'sink_port_id': nearest_connection[0]}
                    tmp_dict_reverse = {'source_elem_id': nearest_connection[1], 'source_port_id': nearest_connection[0], 'sink_elem_id': source_element_idx, 'sink_port_id': port}
                    if tmp_dict not in result_dict['Possible_connected_elements'] and tmp_dict_reverse not in result_dict['Possible_connected_elements']:
                        result_dict['Possible_connected_elements'].append(tmp_dict)

                else:
                    tmp_dict = {'source_elem_id': source_element_idx, 'source_port_id': port, 'sink_elem_id': possible_connection[0], 'sink_port_id': port_idx}
                    tmp_dict_reverse = {'source_elem_id': possible_connection[0], 'source_port_id': port_idx, 'sink_elem_id': source_element_idx, 'sink_port_id': port}
                    if tmp_dict not in result_dict['Possible_connected_elements'] and tmp_dict_reverse not in result_dict['Possible_connected_elements']:
                        result_dict['Possible_connected_elements'].append(tmp_dict)

            else:
                result_dict['No_free_port_nearby'].append(source_element_idx)

    return result_dict

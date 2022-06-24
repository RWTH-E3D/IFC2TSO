import os
import networkx as nx

from lxml import etree as ET
import shutil
from zipfile import ZipFile
from datetime import datetime
import uuid


def check_import_graph_syntax(graph_json):
    # Analyse der Syntax des Inputs
    # Überprüfe ob graph_json die Bezeichner 'nodes' und 'links' hat
    if 'nodes' not in graph_json or 'links' not in graph_json:
        return 'The given input does not have the correct syntax. No nodes or edges are given.'

    # Überprüfe die Struktur des Dictionary der 'links'
    if type(graph_json['links']) is not list:
        return 'The given input does not have the correct syntax. Edges are not given as a list of dict.'

    for edge in graph_json['links']:
        if type(edge) is not dict:
            return 'The given input does not have the correct syntax. Edges are not given as a list of dict.'
        if 'source' not in edge or 'target' not in edge:
            return 'The given input does not have the correct syntax. Edges are not given as {"source":str(GUID), "target":str(GUID)}.'

    # Überprüfe die Struktur des Dictionary der 'nodes'
    if type(graph_json['nodes']) is not list:
        return 'The given input does not have the correct syntax. Nodes are not given as a list of dict.'

    for node in graph_json['nodes']:
        if type(node) is not dict:
            return 'The given input does not have the correct syntax. Nodes are not given as a list of dict.'

        # Überprüfe das Vorhandensein der Attribute
        attr_dict = {'ifc_id': '', 'ifc_class': '', 'ifc_type': '', 'ifc_name': '', 'ifc_description': '', 'ifc_system': [], 'ifc_position': [], 'elem_rds': '', 'additional_data': dict()}
        for necessary_attr in attr_dict.keys():
            if necessary_attr not in node:
                return 'The given input does not have the correct syntax. Nodes do not have (a) necessary attribute(s).'

        # Überprüfe die Datentypen der Attribute
        for attr_name, attr_type in node.items():
            if attr_name not in attr_dict:
                continue
            if isinstance(attr_type, type(attr_dict[attr_name])) or isinstance(attr_type, type(None)):
                if attr_name == 'ifc_system' and isinstance(attr_name, list):
                    if len(attr_type) != 2:
                        return 'The given input does not have the correct syntax. Node attribute ifc_system does not have the length of 2.'
                if attr_name == 'ifc_position' and isinstance(attr_name, list):
                    if len(attr_type) != 3:
                        return 'The given input does not have the correct syntax. Node attribute ifc_position does not have the length of 3.'
            else:
                return 'The given input does not have the correct syntax. Node attribute(s) do(es) not have the necessary datatype.'

    return None


def check_import_graph_info(import_graph):
    # Analyse der Informationen des Inputs
    info_dict = dict()
    info_dict['Elements'] = dict()
    info_dict['IFC-Systems'] = dict()
    info_dict['Systems'] = dict()
    info_dict['Elements']['Total'] = 0
    info_dict['IFC-Systems']['Total'] = 0
    info_dict['Systems']['Total'] = 0
    for node in import_graph.nodes(data=True):
        # Anzahl der Knoten sowie deren Elementklassifizierungen (Class und Type)
        if node[1]['ifc_class'] not in info_dict['Elements']:
            info_dict['Elements'][node[1]['ifc_class']] = dict()
            info_dict['Elements'][node[1]['ifc_class']]['Total'] = 0
        if node[1]['ifc_type'] not in info_dict['Elements'][node[1]['ifc_class']]:
            info_dict['Elements'][node[1]['ifc_class']][node[1]['ifc_type']] = 1
            info_dict['Elements']['Total'] += 1
            info_dict['Elements'][node[1]['ifc_class']]['Total'] += 1
        else:
            info_dict['Elements'][node[1]['ifc_class']][node[1]['ifc_type']] += 1
            info_dict['Elements'][node[1]['ifc_class']]['Total'] += 1
            info_dict['Elements']['Total'] += 1

        # Verschiedene IFC-Systeme mit der Anzahl der dazugehörigen Knoten
        if node[1]['ifc_system']:
            system_tuple = tuple(node[1]['ifc_system'])
        else:
            system_tuple = None
        if system_tuple not in info_dict['IFC-Systems']:
            info_dict['IFC-Systems'][system_tuple] = dict()
            info_dict['IFC-Systems'][system_tuple]['Total'] = 1
            info_dict['IFC-Systems'][system_tuple]['Connected'] = []
            info_dict['IFC-Systems'][system_tuple]['Components'] = [node[0]]
            info_dict['IFC-Systems']['Total'] += 1
        else:
            info_dict['IFC-Systems'][system_tuple]['Total'] += 1
            info_dict['IFC-Systems'][system_tuple]['Components'].append(node[0])

        # Verbindungen zwischen den verschiedenen IFC-Systemen
        edge_list = []
        in_edges = import_graph.in_edges(node[0], data=True)
        out_edges = import_graph.out_edges(node[0])
        for i in in_edges:
            edge_list.append(i[0])
        for i in out_edges:
            edge_list.append(i[1])

        for j in edge_list:
            if import_graph.nodes[j]['ifc_system']:
                connected_system_tuple = tuple(import_graph.nodes[j]['ifc_system'])
                if connected_system_tuple != system_tuple:
                    if connected_system_tuple[0] not in info_dict['IFC-Systems'][system_tuple]['Connected']:
                        info_dict['IFC-Systems'][system_tuple]['Connected'].append(connected_system_tuple[0])
            else:
                connected_system_tuple = None

    # Anzahl der eigenständigen (schwach verbundenen (keine Betrachtung der Fließrichtung)) Systeme und deren enthaltenen definierten IFC-System
    system_list = sorted(nx.weakly_connected_components(import_graph), key=len, reverse=True)
    for system in system_list:
        info_dict['Systems']['Total'] += 1
        info_dict['Systems'][info_dict['Systems']['Total']] = dict()
        info_dict['Systems'][info_dict['Systems']['Total']]['Total'] = len(system)
        info_dict['Systems'][info_dict['Systems']['Total']]['IFC-Systems'] = []
        info_dict['Systems'][info_dict['Systems']['Total']]['Components'] = []
        for node in system:
            ifc_system = import_graph.nodes[node]['ifc_system']
            if ifc_system:
                ifc_system = ifc_system[0]
            else:
                ifc_system = None

            info_dict['Systems'][info_dict['Systems']['Total']]['Components'].append(node)
            if ifc_system not in info_dict['Systems'][info_dict['Systems']['Total']]['IFC-Systems']:
                info_dict['Systems'][info_dict['Systems']['Total']]['IFC-Systems'].append(ifc_system)

    return info_dict


def write_infos(input_dict, hierarchie_dict, args, name):
    # Konsolidierung und Ausgabe der Analyseergebnisse in einer Datei im TXT-Format
    f = open(os.path.dirname(args.input_file[0]) + '/INFO_' + name + ".txt", "w")
    for categorie, main_dict in input_dict.items():
        if categorie.upper() == 'IFC-SYSTEMS':
            f.write(categorie.upper().ljust(30))
            total = main_dict.pop('Total')
            f.write("\t\t\t{}".format(total) + '\n\n')
            for key, value in main_dict.items():
                if not key:
                    key = [None, None]
                total_classes = value.pop('Total')
                f.write("\t{}\t\t\t{}".format(str(key[0]).ljust(25), total_classes) + '\n')
                f.write("\t\t{}\t\t{}".format('Type'.ljust(25), str(key[1]).ljust(10)) + '\n')
                for key_class, total in value.items():
                    if key_class == 'Components':
                        continue
                    f.write("\t\t{}\t\t{}".format(key_class.ljust(25), total) + '\n')
                f.write('\n')

        elif categorie.upper() == 'ELEMENTS':
            f.write(categorie.upper().ljust(30))
            total_elements = main_dict.pop('Total')
            f.write("\t\t\t{}".format(total_elements) + '\n\n')
            for key, value in main_dict.items():
                f.write("\t{}".format(key.ljust(30)))
                total_classes = value.pop('Total')
                f.write("\t\t{}".format(total_classes) + '\n')
                for key_class, total in value.items():
                    f.write("\t\t{}\t\t\t\t{}".format(key_class.ljust(17), total) + '\n')
                f.write('\n')

    f.write('SYSTEMS \n \n')
    for categorie, main_dict in hierarchie_dict.items():
        if categorie == 'Schnittstellen':
            continue
        f.write(categorie.upper().ljust(30))
        f.write("\t\t\t{}".format(len(main_dict)) + '\n\n')
        for key, value in main_dict.items():
            f.write("\t{}".format(str(key).ljust(30)))
            f.write("\t\t{}".format(len(value['Components'])) + '\n')
            for key_class, total in value.items():
                f.write("\t\t{}\t\t\t\t{}".format(key_class.ljust(17), total) + '\n')
            f.write('\n')

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

    filepath_1 = os.path.dirname(args.input_file[0]) + '/' + main_guid
    filepath_2 = os.path.dirname(args.input_file[0]) + '/' + main_guid + '/' + main_guid

    filepath_version = filepath_1 + '/bcf.version'
    filepath_markup = filepath_2 + '/markup.bcf'
    filepath_viewpoint = filepath_2 + '/viewpoint.bcfv'

    os.mkdir(filepath_1)
    os.mkdir(filepath_2)

    create_bcf_version(filepath_version)
    create_bcf_markup(input_dict['markup'], filepath_markup)
    create_bcf_viewpoint(input_dict['viewpoint'], filepath_viewpoint)

    shutil.copyfile('snapshot.png', os.path.dirname(args.input_file[0]) + '/' + main_guid + '/' + main_guid + '/snapshot.png')

    if zipped:
        zip_bcfs([main_guid], args, zipped)

    else:
        return main_guid


def zip_bcfs(list_guid, args, zipped):
    # Komprimierung der erstellten BCF-Dateien

    # Erstellung einer komprimierten BCF-Datei mit mehreren untergeordneten Dateien
    if not zipped:
        now = datetime.now()
        folder_name = str(uuid.uuid4())
        os.mkdir(os.path.dirname(args.input_file[0]) + '/' + folder_name)
        for main_guid in list_guid:
            shutil.move(os.path.dirname(args.input_file[0]) + '/' + main_guid + '/' + main_guid, os.path.dirname(args.input_file[0]) + '/' + folder_name + '/' + main_guid)
            shutil.move(os.path.dirname(args.input_file[0]) + '/' + main_guid + '/bcf.version', os.path.dirname(args.input_file[0]) + '/' + folder_name + '/bcf.version')
            shutil.rmtree(os.path.dirname(args.input_file[0]) + '/' + main_guid, ignore_errors=True)

        os.chdir(os.path.dirname(args.input_file[0]) + '/' + folder_name)
        with ZipFile(folder_name + '.bcf', 'w') as zips:
            zips.write('bcf.version')
            for main_guid in list_guid:
                zips.write(main_guid)
                zips.write(main_guid + '/markup.bcf')
                zips.write(main_guid + '/viewpoint.bcfv')
                zips.write(main_guid + '/snapshot.png')

        os.chdir('..')
        os.chdir('..')
        shutil.move(os.path.dirname(args.input_file[0]) + '/' + folder_name + '/' + folder_name + '.bcf', os.path.dirname(args.input_file[0]) + '/' + folder_name + '.bcf')
        shutil.rmtree(os.path.dirname(args.input_file[0]) + '/' + folder_name, ignore_errors=True)

    # Erstellung einer komprimierten BCF-Datei für jede untergeordnete Datei
    else:
        for main_guid in list_guid:
            os.chdir(os.path.dirname(args.input_file[0]) + '/' + main_guid)
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

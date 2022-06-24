import ifcopenshell
import logging
import argparse
import json

from helper_graph import *
from helper_check import *


def check_ifc_file(model, file_name):
    # Analyse des IFC-Modells und der darin enthaltenen Informationen zu technischen Systemen
    # Aufsetzen eines Dictionaries zur Ablage der Ergebnisse der Analyse
    result_dict = dict()

    # Analyse der Informationen im Header
    result_dict['header_info'] = check_header(model, file_name)

    # Analyse der verwendeten Beziehung zur Zuordnung von Ports zu Elementen
    result_dict['port_relationship'], tmp = check_for_relationships(model)

    # Analyse der Elemente und deren Klassifizierungen
    result_dict['Investigated Classes'] = check_classes(model)

    # Analyse der Systemzuordnungen
    result_dict['Investigated Systems'] = check_systems(model)

    # Analyse der Portzuordnungen und topologischer Verbindungen
    tmp_dict = check_classes_for_ports(model)
    result_dict['Classes without ports'] = tmp_dict['Without_ports']
    result_dict['Elements without ports'] = tmp_dict['Elements_without_ports']
    result_dict['Classes with open ports'] = tmp_dict['With_unassigned_ports']
    result_dict['Ports without assignment'] = check_ports_for_unassigned(model)

    return result_dict


def convert_ifc_to_graph(model, args, pm_list, info_dict, position_dict):
    # Überführung der topologischen Informationen aus dem IFC-Modell in einen Graph
    # Vorbereitung der topologischen Informationen zur Überführung in den Graph
    logging.info('Topological information is being extracted')
    result_dict, additional_data_dict = get_topo_info(model, args, info_dict, position_dict)

    # Konzeption des Graphs und Integration der Daten
    logging.info('Graph is being built')
    directed_graph = create_directed_graph(result_dict, additional_data_dict, args)

    # Ergänzung von gerichteten Kanten basierend auf den Ergebnissen der Anreicherungsprozesse
    if args.ce:
        logging.info('Additional edges are being added to the graph')
        directed_graph = add_edges_based_on_spatial_tree(directed_graph, pm_list, model, args)

    return directed_graph


def main(args):
    # IFC2GRAPH Prozess
    # Konfiguration des Logs
    if args.l:
        logging.basicConfig(handlers=[logging.FileHandler(os.path.dirname(args.input_file) + '/LOG_' + os.path.basename(args.input_file)[:-4] + '.log'),
                                      logging.StreamHandler()],
                            level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

    logging.info('Process started with options %r', args)

    # Überprüfen ob es sich bei der zu importierenden Datei um ein IFC-Modell handelt
    if not args.input_file.lower().endswith('.ifc'):
        return logging.warning('The given Input is not in the *.ifc Format')

    # Parsen des Modells mit ifcopenshell
    logging.info('Model is getting imported')
    try:
        main_model = ifcopenshell.open(args.input_file)
        logging.info('Model was successfully imported')
    except OSError:
        return logging.warning('The given input could not be imported using ifcopenshell')

    # Kontrolle der Version der IFC
    if main_model.wrapped_data.schema != 'IFC4':
        return logging.warning('The given input is not in the necessary IFC4 format.')

    # Aufruf der Prozesse der Analyse der enthaltenen topologischen Informationen
    logging.info('Model is getting checked')
    info_dict = check_ifc_file(main_model, os.path.basename(args.input_file)[:-4])
    logging.info('Model was successfully checked')

    # Export einer BCF-Datei zu Elementen mit offenen Ports
    if args.bcf_p:
        logging.info('BCF about elements with unassigned ports is being created')
        selection = []
        for x in info_dict['Classes with open ports'].values():
            selection.extend(x)
        transfer_dict = {'Selections': selection,
                         'Title': 'Open Ports',
                         'Description': 'Elements with open ports',
                         'Visibility': 'True',
                         'Exceptions': []}
        create_bcf(transfer_dict, args)
        logging.info('BCF about elements with unassigned ports was successfully created')

    # Analyse der absoluten Position der Ports im dreidimensionalen Raum
    logging.info('Calculate absolute position of elements and corresponding ports')
    position_dict = calculate_all_absolute_positions(main_model)
    logging.info('Calculate absolute position of elements and corresponding ports was successful')

    # Konzeption eines R-Baum der Ports basierend auf der Position im dreidimensionalen Raum
    if args.ce or args.bcf_pm:
        logging.info('Spatial Tree is being created')

        # Konzeption eines R-Baums
        index_dict = build_spatial_index(position_dict['IfcDistributionPort'])
        logging.info('Spatial Tree was successfully created')

        # Abfrage des R-Baums um potentielle topologische Verbindungen zu identifizieren
        logging.info('Check for possible matches in spatial tree')
        if args.ce:
            spatial_bound = args.ce
        else:
            spatial_bound = 50

        result_check_port_dict = check_ports(main_model, info_dict, index_dict, position_dict, spatial_bound)
        info_dict['Possible Matches'] = result_check_port_dict['Possible_connected_elements']
        logging.info('Possible matches were successfully checked')

        # Export einer gezippten BCF-Datei zu Elementen mit offenen Ports und deren möglichen Verbindungen in untergeordneten BCF-Dateien
        if args.bcf_pm:
            logging.info('BCF about elements with unassigned ports and their possible matches is being created')
            bcf_guids = []
            if len(result_check_port_dict['Possible_connected_elements']) > 0:
                for x in result_check_port_dict['Possible_connected_elements']:
                    transfer_dict = {'Selections': [x['source_elem_id']],
                                     'Title': 'Open Ports and possible matches',
                                     'Description': 'Elements with open ports and their possible matches',
                                     'Visibility': 'False',
                                     'Exceptions': [x['sink_elem_id']]}
                    bcf_guids.append(create_bcf(transfer_dict, args, zipped=False))
                zip_bcfs(bcf_guids, args, zipped=False)
                logging.info('BCF about elements with unassigned ports and their possible matches was successfully created')
            else:
                logging.warning('BCF about elements with unassigned ports and their possible matches could not be created. There are no possible matches.')

    # Export der Analyseergebnisse als Datei im TXT-Format
    if args.i:
        logging.info('Information about the model is being saved')
        write_infos(info_dict, args)
        logging.info('Information about the model was successfully saved')

    # Überführung der topologischen Informationen aus dem IFC-Modell in einen Graph
    logging.info('Model is being converted into graph')
    pm_list = []
    if args.ce:
        pm_list = result_check_port_dict['Possible_connected_elements']

    output_graph = convert_ifc_to_graph(main_model, args, pm_list, info_dict, position_dict)
    logging.info('Model was successfully converted into graph')

    # Export des Graphs in Knoten-/Kantenliste Darstellung und Ablage als JSON-Datei
    data_drop = nx.node_link_data(output_graph)
    with open(os.path.dirname(args.input_file) + '/GRAPH_' + os.path.basename(args.input_file)[:-4] + '.json', 'w', encoding='utf8') as json_file:
        json.dump(data_drop, json_file, ensure_ascii=False)
    logging.info('Graph was successfully saved')

    # Entfernen der temporären Dateien
    logging.info('Temporary files are being removed')
    try:
        os.remove('3d_index.data')
        os.remove('3d_index.index')
    except FileNotFoundError:
        pass

    logging.info('Temporary files were successfully removed')


if __name__ == "__main__":
    # Konzeption des Command Line Interface
    parser = argparse.ArgumentParser(description="""
                                     Analyse the information regarding technical systems in the given ifc model, enrich topological connections and
                                     parse the results as a graph
                                     """
                                     )

    # Pfad zum IFC-Modell
    parser.add_argument("input_file", type=str, help="Input IFC file")

    # Erweiterung der Informationen an den Knoten des Graphs um ein Bezeichner-Wert Array, welche alle inversen Attribute des korrespondieren Elements im IFC-Modell enthält.
    parser.add_argument("-data", action='store_true', help="Store all alphanumerical data in the output graph")

    # Ablage der Analyseergebnisse der enthaltenen Informationen zu techni- schen Systemen als Datei im TXT-Format am Pfad des Modells.
    # Hierzu wird als Bezeichner der Name des IFC-Modells um den Präfix INFO_ erweitert.
    parser.add_argument("-i", action='store_true', help="Logging Information about the IFC files")

    # Ablage des Logs zum Prozessfortschritts als Datei im TXT-Format am Pfad des IFC-Modells. Hierzu wird als Bezeichner der Name des Modells um den Präfix LOG_ erweitert.
    parser.add_argument("-l", action='store_true', help="Save log to file at given output directory")

    # Automatisierte Erweiterung des Graphs um gerichtete Kanten basierend auf den Ergebnissen der Prozesse im Bereich der Anreicherung.
    parser.add_argument("-ce", type=int, default=None, help="Add an edge between open ports with the maximum distance of L in mm.")

    # Ablage der Analyseergebnisse zu Elementen mit offenen Ports als BCF- Datei am Pfad des Modells. Als Bezeichner wird eine GUID verwendet.
    parser.add_argument("-bcf_p", action="store_true", help='Create bcf-file of all elements with unassigned ports')

    # Ablage der Ergebnisse der Anreicherung zu Elementen mit offenen Ports und möglichen topologischen Nachbarn als BCF-Datei am Pfad des Modells. Als Bezeichner wird eine GUID verwendet.
    parser.add_argument("-bcf_pm", action="store_true", help='Create bcf-file of all elements with unassigned ports and possible matches')

    # Analyse des IFC-Modells anhand des angegebenen Attributsbezeichners und Zuordnung der Werte als standardisierte Eigenschaft elem_rds an die Konten des Graphs.
    parser.add_argument("-rds", type=str, default=None, help='Give property name of the reference designation key to store in graph')

    parse_args = parser.parse_args()

    # Aufruf des IFC2GRAPH Prozesses mit den notwendigen und optionalen Parametern zur Anpassung der Funktionalität
    main(parse_args)

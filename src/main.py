import ifcopenshell
import logging
import argparse
import json

from IFC2GRAPH.helper_graph import *
from IFC2GRAPH.helper_check import *

from GRAPH.helper_enrich import *

from GRAPH2TSO.helper_convert import *


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


def main_ifc2graph(args, import_ifc):
    # IFC2GRAPH Prozess
    # Überprüfen ob es sich bei der zu importierenden Datei um ein IFC-Modell handelt

    logging.info('Processstep IFC2GRAPH started')

    if not import_ifc.lower().endswith('.ifc'):
        return logging.warning('The given Input is not in the *.ifc Format')

    # Parsen des Modells mit ifcopenshell
    logging.info('Model is getting imported')
    try:
        main_model = ifcopenshell.open(import_ifc)
        logging.info('Model was successfully imported')
    except OSError:
        return logging.warning('The given input could not be imported using ifcopenshell')

    # Kontrolle der Version der IFC
    if main_model.wrapped_data.schema != 'IFC4':
        return logging.warning('The given input is not in the necessary IFC4 format.')

    # Aufruf der Prozesse der Analyse der enthaltenen topologischen Informationen
    logging.info('Model is getting checked')
    info_dict = check_ifc_file(main_model, os.path.basename(import_ifc)[:-4])
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

    # Überführung der topologischen Informationen aus dem IFC-Modell in einen Graph
    logging.info('Model is being converted into graph')
    pm_list = []
    if args.ce:
        pm_list = result_check_port_dict['Possible_connected_elements']

    output_graph = convert_ifc_to_graph(main_model, args, pm_list, info_dict, position_dict)
    logging.info('Model was successfully converted into graph')

    # Entfernen der temporären Dateien
    logging.info('Temporary files are being removed')
    try:
        os.remove('3d_index.data')
        os.remove('3d_index.index')
    except FileNotFoundError:
        pass

    logging.info('Temporary files were successfully removed')

    return output_graph, info_dict


def main_graph(args, graph_list):
    logging.info('Processstep GRAPH started')

    #                           #
    #                           #
    #                           #
    #    Bereich der ANALYSE    #
    #                           #
    #                           #
    #                           #
    import_graph = nx.DiGraph()
    for ifc2graph_graph_info in graph_list:

        # Überführung der Daten in einen gerichteten Graph
        logging.info('Graph is getting merged using networkx')
        try:
            import_graph = nx.compose(import_graph, ifc2graph_graph_info[0])
        except ValueError:
            return logging.warning('The graph could not be merged using networkx')

        logging.info('Graph was successfully imported')

    #                            #
    #                            #
    #                            #
    #  Bereich der ANREICHERUNG  #
    #                            #
    #                            #
    #                            #

    # Kanten anreichern
    if args.add_edges:
        # Überprüfen ob es sich bei der zu importierenden Datei um eine Datei im JSON-Format handelt
        if not args.add_edges.lower().endswith('.json'):
            return logging.warning('The given Input for adding edges is not in the *.json Format')

        logging.info('JSON is getting parsed')
        try:
            f = open(args.add_edges, "r")
            edge_json = json.load(f)
        except ValueError:
            return logging.warning('The given input could not be handle using json')

        try:
            for edge in edge_json['links']:
                if edge['source'] in import_graph.nodes and edge['target'] in import_graph.nodes:
                    import_graph.add_edge(edge['source'], edge['target'])
            logging.info('Additional edges were added successfully')
        except KeyError:
            return logging.warning('The given input does not have the correct syntax.')

    # Analyse der Informationen im Graph
    logging.info('Data is being analysed')
    info_dict = check_import_graph_info_graph(import_graph)
    logging.info('Data was successfully analysed')

    # Löschen von schwach verbundenen Systemem mit der Größe <= R
    if args.r:
        logging.info('Weakly connected systems with the size <= R are being deleted.')
        del_system_list = []
        for key, system in info_dict['Systems'].items():
            if isinstance(system, int):
                continue
            if system['Total'] <= args.r:
                for node in system['Components']:
                    import_graph.remove_node(node)
                del_system_list.append(key)

        for del_system in del_system_list:
            info_dict['Systems'].pop(del_system)
        info_dict['Systems']['Total'] = len(info_dict['Systems'].keys()) - 1
        logging.info('Weakly connected systems with the size <= R were successfully deleted.')

    # Anreicherung der Systemhierarchie
    logging.info('Hierarchical structure of the systems is being enriched.')
    hierarchie_dict = dict()
    hierarchie_dict['IS'] = dict()
    hierarchie_dict['FS'] = dict()
    hierarchie_dict['TS'] = dict()

    if args.add_sh:
        # Importieren der JSON-Datei und Anreicherung der hierarchischen Struktur
        logging.info('Hierarchical structure is being imported.')
        # Überprüfen ob es sich bei der zu importierenden Datei um eine Datei im JSON-Format handelt
        if not args.add_sh.lower().endswith('.json'):
            return logging.warning('The given Input for adding system hierarchy is not in the *.json Format')

        logging.info('JSON is getting parsed')
        try:
            f = open(args.add_sh, "r")
            system_json = json.load(f)
        except ValueError:
            return logging.warning('The given input could not be handle using json')

        hierarchie_dict, system_dict = get_system_hierarchy(system_json, info_dict, hierarchie_dict)
        logging.info('Hierarchical structure was successfully imported and enriched.')

    else:
        # Untegliederung der Systemverbände in funktionalen Systeme
        logging.info('Hierarchical structure of functional systems is being enriched.')
        hierarchie_dict, system_dict = check_for_functional_systems(info_dict, hierarchie_dict)
        logging.info('Hierarchical structure of functional systems was successfully enriched.')

        # Untegliederung der funktionalen Systeme in technische Systeme
        logging.info('Hierarchical structure of technical systems is being enriched.')
        hierarchie_dict, system_dict = check_for_technical_systems(hierarchie_dict, import_graph, system_dict)
        logging.info('Hierarchical structure of technical systems was successfully enriched.')
        logging.info('Hierarchical structure of the systems was successfully enriched')

    # Anlegen von Komponenten ohne Systemaggregation
    for node in import_graph.nodes(data=True):
        if node[0] not in system_dict:
            system_dict[node[0]] = dict()
            system_dict[node[0]]['IS'] = []
            system_dict[node[0]]['FS'] = []
            system_dict[node[0]]['TS'] = []

    # Export der Anreicherungsergebnisse im BCF-Format
    if args.bcf_sh:
        logging.info('Results of the enrichment are being exported as bcf files.')
        mapping = {'IS': 'FS', 'FS': 'TS', 'TS': 'TS'}
        bcf_guids = []
        for hier_level, system_dict_2 in hierarchie_dict.items():
            for system_guid, system_value in system_dict_2.items():
                transfer_dict = {'Selections': system_value['Components'],
                                 'Title': '%s - %s Children:(%s)' % (hier_level, system_value['Classification'], system_value[mapping[hier_level]]),
                                 'Description': 'Ifc-Systems %s of components' % (system_value['IFC-Systems']),
                                 'Visibility': 'True',
                                 'Exceptions': []}
                bcf_guids.append(create_bcf(transfer_dict, args, zipped=False))
        zip_bcfs(bcf_guids, args, zipped=False)
        logging.info('Results of the enrichment were successfully exported as bcf files.')

    hierarchie_dict = check_system_connections(import_graph, hierarchie_dict, system_dict)

    # Aufsetzen eines neuen Graphs mit den zusätzlichen Ergebnissen der Anreicherung
    logging.info('Resulting graph is converted and additional information is added.')
    export_graph = convert_import_graph_in_export_graph(import_graph, system_dict)
    logging.info('Resulting graph was successfully converted and additional information was added.')

    #                                       #
    #                                       #
    #                                       #
    #   Bereich der KOMPLEXITÄTSREDUKTION   #
    #                                       #
    #                                       #
    #                                       #

    # Komplexitätsreduktion des Graphs
    if args.cr:
        logging.info('Topological complexity of the graph is being reduced.')
        len_nodes_before = 1
        len_nodes_after = 0
        while len_nodes_before != len_nodes_after:
            len_nodes_before = len(export_graph.nodes)
            export_graph = aggregate_graph(export_graph)
            len_nodes_after = len(export_graph.nodes)
        logging.info('Topological complexity of the graph was successfully reduced.')

    return export_graph, info_dict, hierarchie_dict


def main_graph2tso(args, import_graph, hierarchie_dict):
    logging.info('Processstep GRAPH2TSO started')
    # Analyse der importierten Graphen auf birektionalen Austausch zwischen Komponenten
    result_set = set()
    for node in import_graph.nodes(data=True):
        suc_iter = import_graph.successors(node[0])
        for suc in suc_iter:
            node_2_iter = import_graph.successors(suc)
            if node[0] in node_2_iter:
                result_set.add(node[0])
                result_set.add(suc)

    # Export der Analyse der Fließrichtung als BCF
    if args.bcf_fd:
        logging.info('Results of the analyse regarding the flow direction are being exported as bcf file.')
        transfer_dict = {'Selections': list(result_set),
                         'Title': 'Bidirectional flow direction',
                         'Description': 'Components with a bidirectional flow direction',
                         'Visibility': 'True',
                         'Exceptions': []}
        create_bcf(transfer_dict, args)
        logging.info('Results of the analyse regarding the flow direction were successfully exported as bcf file.')

    #                            #
    #                            #
    #                            #
    #  Bereich der ANREICHERUNG  #
    #                            #
    #                            #
    #                            #

    # Konzeption eines neuen Graphs mit korrekten gerichteten Kanten
    directions_list = list()
    enriched_graph = create_enriched_directed_graph(directions_list, import_graph)

    # Anreicherung von inneren Verbindungen
    ic_json = dict()
    if args.add_ic:
        # Importieren der JSON-Datei und Anreicherung der inneren Verbindungen
        logging.info('Inner Connections are being imported.')
        # Überprüfen ob es sich bei der zu importierenden Datei um eine Datei im JSON-Format handelt
        if not args.add_ic.lower().endswith('.json'):
            return logging.warning('The given Input for adding inner connections is not in the *.json Format')

        logging.info('JSON is getting parsed')
        try:
            f = open(args.add_ic, "r")
            ic_json = json.load(f)
        except ValueError:
            return logging.warning('The given input could not be handle using json')

    # Anreicherung von funktionalen Konzepten
    fc_json = dict()
    if args.add_fc:
        # Importieren der JSON-Datei und Anreicherung der inneren Verbindungen
        logging.info('Functional Concepts are being imported.')
        # Überprüfen ob es sich bei der zu importierenden Datei um eine Datei im JSON-Format handelt
        if not args.add_fc.lower().endswith('.json'):
            return logging.warning('The given Input for adding functional concepts is not in the *.json Format')

        logging.info('JSON is getting parsed')
        try:
            f = open(args.add_fc, "r")
            fc_json = json.load(f)
        except ValueError:
            return logging.warning('The given input could not be handle using json')

    # Anreicherung von räumlichen Konzepten
    spatial_dict = dict()
    if args.add_spatial:
        # Importieren der IFC-Datei
        logging.info('Spatial Structure is being imported.')
        if not args.add_spatial.lower().endswith('.ifc'):
            return logging.warning('The given Input is not in the *.ifc Format')

        logging.info('Model is getting imported')
        try:
            main_model = ifcopenshell.open(args.add_spatial)
            logging.info('Model was successfully imported')
        except OSError:
            return logging.warning('The given input could not be imported using ifcopenshell')

        # Kontrolle der Version der IFC
        if main_model.wrapped_data.schema != 'IFC4':
            return logging.warning('The given input is not in the necessary IFC4 format.')

        logging.info('Model is getting analysed')
        rep_dict = calculate_spatial_representation(main_model)
        spatial_dict = analyse_spatial_structure(main_model, rep_dict)
        logging.info('Model was successfully analysed')

    #                            #
    #                            #
    #                            #
    #  Bereich der ÜBERFÜHRUNG   #
    #                            #
    #                            #
    #                            #
    logging.info('Graph is getting transfered in linked data representation')
    # Überführung vom Graph in eine Wissensrepräsentation
    # Aufsetzen des Graphs und der Namespaces
    g_ld = Graph()
    name = str(uuid.uuid4())

    if args.use_ns:
        INST = Namespace(args.use_ns)
    else:
        INST = Namespace('https://example.org/%s#' % (name))

    TSO = Namespace('https://w3id.org/tso#')
    RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
    IFC = Namespace('https://standards.buildingsmart.org/IFC/DEV/IFC4/FINAL/OWL#')
    BOT = Namespace('https://w3id.org/bot#')

    # Anlegen von Konzepten mit hierarchischen Aspekten
    logging.info('Hierarchical concepts are created')
    g_ld, state_dict = convert_hierarchicalconcepts_to_tso(g_ld, args, enriched_graph, hierarchie_dict, IFC, INST, TSO, RDF, RDFS)
    logging.info('Hierarchical concepts were created successfully')

    # Anlegen von Konzepten mit topologischen Aspekten
    logging.info('Topological concepts are created')
    g_ld, outer_edge_dict, inner_edge_dict = convert_topologicalconcepts_to_tso(g_ld, enriched_graph, hierarchie_dict, ic_json, INST, TSO, RDF)
    logging.info('Topological concepts were created successfully')

    # Anlegen von Konzepten mit Aspekten der räumlichen Strukturierung
    logging.info('Spatial concepts are created')
    g_ld, serves_dict = convert_spatialconcepts_to_tso(g_ld, args, enriched_graph, spatial_dict, INST, TSO, RDF, BOT)
    logging.info('Spatial concepts were created successfully')

    # Anlegen von Konzepten mit funktionalen Aspekten
    logging.info('Functional concepts are created')
    g_ld = convert_functionalconcepts_to_tso(g_ld, args, enriched_graph, fc_json, state_dict, outer_edge_dict, inner_edge_dict, hierarchie_dict, serves_dict, INST, TSO, RDF, RDFS)
    logging.info('Functional concepts were created successfully')

    logging.info('Graph was successfully transfered in linked data representation')

    # Binden der Namespaces
    g_ld.bind('tso', TSO)
    g_ld.bind('rdf', RDF)
    g_ld.bind('rdfs', RDFS)
    g_ld.bind('inst', INST)
    g_ld.bind('ifc4', IFC)
    g_ld.bind('bot', BOT)

    return g_ld, result_set, name


def main(args):
    # Konfiguration des Logs
    if args.l:
        logging.basicConfig(handlers=[logging.FileHandler(os.path.dirname(args.input_files[0]) + '/LOG_' + os.path.basename(args.input_files[0])[:-4] + '.log'),
                                      logging.StreamHandler()],
                            level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

    logging.info('Process IFC2TSO started with options %r', args)

    graph_list = list()
    for input_file in args.input_files:
        graph, ifc2graph_info_dict = main_ifc2graph(args, input_file)
        graph_list.append((graph, ifc2graph_info_dict))

    if args.ifc2graph:
        for idx, graph in enumerate(graph_list):
            # Export des Graphs in Knoten-/Kantenliste Darstellung und Ablage als JSON-Datei
            data_drop = nx.node_link_data(graph[0])
            with open(os.path.dirname(args.input_files[idx]) + '/GRAPH_' + os.path.basename(args.input_files[idx])[:-4] + '.json', 'w', encoding='utf8') as json_file:
                json.dump(data_drop, json_file, ensure_ascii=False)
            logging.info('Graph was successfully saved')

        return None

    merged_graph, graph_info_dict, hierarchie_dict = main_graph(args, graph_list)
    graph_name = str(uuid.uuid4())

    if args.graph:
        # Export des Graphs in Knoten-/Kantenliste Darstellung und Ablage als JSON-Datei
        data_drop = nx.node_link_data(merged_graph)
        data_drop['hierarchy'] = hierarchie_dict
        with open(os.path.dirname(args.input_files[0]) + '/ENRICHED_GRAPH_' + graph_name + '.json', 'w', encoding='utf8') as json_file:
            json.dump(data_drop, json_file, ensure_ascii=False)
        logging.info('Graph was successfully saved')

        return None

    g_ld, graph2tso_info_dict, name = main_graph2tso(args, merged_graph, hierarchie_dict)

    # Export der Analyseergebnisse als Datei im TXT-Format
    if args.i:
        logging.info('Information about the model is being saved')
        write_infos(graph_list, graph_info_dict, graph2tso_info_dict, hierarchie_dict, args, name)
        logging.info('Information about the model was successfully saved')

    # Ablage der Wissensrepräsentation am Pfad
    logging.info('Linked data representation is getting serialized')
    g_ld.serialize(destination=os.path.dirname(args.input_files[0]) + '/LD-REP_' + name + '.ttl', format='turtle')
    logging.info('Linked data representation was successfully serialized and saved')


if __name__ == "__main__":
    # Konzeption des Command Line Interface
    parser = argparse.ArgumentParser(description="""
                                     Analyse the information regarding technical systems in the given ifc model, enrich topological connections, hierarchical structure, functional
                                     and spatial concepts, reduce the topological complexity and parse the results as a turtle serialisation based on TSO.
                                     """
                                     )

    # Pfad zu den IFC-Modellen der technischen Systeme
    parser.add_argument("input_files", nargs='+', type=str, help="Input IFC file")

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

    # Löschen von Knoten in schwach verbundenen Graphen der Größe kleiner gleich R.
    parser.add_argument('-r', type=int, default=0, help='Delete nodes in weakly conncted graphs <= R')

    # Hinzufügen zusätzlicher gerichteter Kanten in den importierten Graph.
    parser.add_argument('-add_edges', type=str, default=None, help='Add edges based on the given json file')

    # Hinzufügen zusätzlicher Systemhierarchie in den importierten Graph.
    parser.add_argument('-add_sh', type=str, default=None, help='Add system hierarchy based on the given json file')

    # Ablage der Anreicherungsergebnisse zu [...] als BCF- Datei am Pfad des Graphs.
    parser.add_argument('-bcf_sh', action='store_true', help='Create bcf-files of the system hierarchy')

    # Durchführen der Prozesse im Bereich der Komplexitätsreduktion.
    parser.add_argument('-cr', action='store_true', help='Reduction of the complexity given the topological information in the graph')

    # Verwendung der IFCowl Ontologie zur Klassifikation von Komponenten.
    parser.add_argument('-ifcowl', action='store_true', help='Represent the component classification using the IFCowl Ontology.')

    # Hinzufügen der räumlichen Struktur basierend auf den Inhalten des angegebenen IFC-Modell.
    parser.add_argument('-add_spatial', type=str, default=None, help='Represent the building topology basend on the *.ifc model using BOT and link it with the technical systems.')

    # Hinzufügen zusätzlicher Informationen zur Anreicherung der inneren Verbindungen.
    parser.add_argument('-add_ic', type=str, default=None, help='Revise inner connections based on the given json file')

    # Hinzufügen zusätzlicher Informationen zur Anreicherung der funktionalen Konzepte.
    parser.add_argument('-add_fc', type=str, default=None, help='Enrich functional concepts based on the given json file')

    # Ablage der Anreicherungsergebnisse zu [...] als BCF- Datei am Pfad des Graphs.
    parser.add_argument('-bcf_fd', action='store_true', help='Create bcf-files of the functional information')

    # Nutzung des angegebenen Namespaces zur eindeutigen Identifizierung der Instanzen.
    parser.add_argument('-use_ns', type=str, default=None, help='Identify instances using the given namespace')

    # Unterbrechnung des Prozesses nach dem Prozessschritt IFC2GRAPH
    parser.add_argument("-ifc2graph", action='store_true', default=None, help="Break the process after IFC2GRAPH and export the resulting graphs")

    # Unterbrechnung des Prozesses nach dem Prozessschritt GRAPH
    parser.add_argument("-graph", action='store_true', default=None, help="Break the process after GRAPH and export the resulting graph")

    parse_args = parser.parse_args()

    # Aufruf des IFC2TSO Prozesses mit den notwendigen und optionalen Parametern zur Anpassung der Funktionalität
    main(parse_args)

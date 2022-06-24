import argparse
import logging
import json

from helper_analyse import *
from helper_enrich import *


def main(args):
    # GRAPH Prozess
    # Konfiguration des Logs
    if args.l:
        logging.basicConfig(handlers=[logging.FileHandler(os.path.dirname(args.input_file[1]) + '/LOG_' + os.path.basename(args.input_file[1])[:-5] + '.log'),
                                      logging.StreamHandler()],
                            level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

    logging.info('Process started with options %r', args)

    #                           #
    #                           #
    #                           #
    #    Bereich der ANALYSE    #
    #                           #
    #                           #
    #                           #
    import_graph = nx.DiGraph()
    for input_file in args.input_file:
        # Überprüfen ob es sich bei der zu importierenden Datei um eine Datei im JSON-Format handelt
        if not input_file.lower().endswith('.json'):
            return logging.warning('The given Input is not in the *.json Format')

        # Parsen des Modells
        logging.info('Graph is getting parsed')
        try:
            f = open(input_file, "r")
            graph_json = json.load(f)
        except ValueError:
            return logging.warning('The given input could not be handle using json')

        # Syntax des Graphs wird überprüft
        logging.info('Syntax of the graph is getting checked')
        error_message = check_import_graph_syntax(graph_json)
        if error_message:
            return logging.warning(str(error_message))
        logging.info('Syntax of the graph is correct')

        # Vorbeiten der Daten zur Überführung in den Graph
        parse_nodes_list = []
        for node in graph_json['nodes']:
            parse_nodes_list.append((node.pop('id'), node))

        parse_edges_list = []
        for edge in graph_json['links']:
            parse_edges_list.append((edge['source'], edge['target']))

        logging.info('Graph was parsed successfully')

        # Überführung der Daten in einen gerichteten Graph
        logging.info('Graph is getting imported using networkx')
        try:
            import_graph.add_nodes_from(parse_nodes_list)
            import_graph.add_edges_from(parse_edges_list)
        except ValueError:
            return logging.warning('The graph could not be imported using networkx')

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
    info_dict = check_import_graph_info(import_graph)
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

    # Export der Analyse- und Anreicherungsergebnisse im TXT-Format
    name = str(uuid.uuid4())
    if args.i:
        logging.info('Information about the model is being saved')
        write_infos(info_dict, hierarchie_dict, args, name)
        logging.info('Information about the model was successfully saved')

    # Export des Graphs in Knoten-/Kantenliste Darstellung und Ablage als JSON-Datei
    data_drop = nx.node_link_data(export_graph)
    data_drop['hierarchy'] = hierarchie_dict
    with open(os.path.dirname(args.input_file[0]) + '/ENRICHED_GRAPH_' + name + '.json', 'w', encoding='utf8') as json_file:
        json.dump(data_drop, json_file, ensure_ascii=False)
    logging.info('Graph was successfully saved')


if __name__ == "__main__":
    # Konzeption des Command Line Interface
    parser = argparse.ArgumentParser(description='Enrich the hierarchical information in the given graph, reduce the topological complexity and save to a directed graph')

    # Pfad zum Graph
    parser.add_argument('input_file', nargs='+', type=str, help='Path to the input graph as a JSON-file')

    # Ablage der Analyseergebnisse der enthaltenen Informationen zu technischen Systemen als Datei im TXT-Format am Pfad des Graphs.
    parser.add_argument('-i', action='store_true', help='Saving information about the graph in as *.txt at the give input directory')

    # Ablage des Logs zum Prozessfortschritts als Datei im TXT-Format am Pfad des Graphs.
    parser.add_argument('-l', action='store_true', help='Save log to file at the given input directory')

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

    parse_args = parser.parse_args()

    # Aufruf des GRAPH Prozesses mit den notwendigen und optionalen Parametern zur Anpassung der Funktionalität
    main(parse_args)

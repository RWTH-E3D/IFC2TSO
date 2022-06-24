import argparse
import logging
import json
import ifcopenshell

from helper_analyse import *
from helper_convert import *
from helper_enrich import *


def main(args):
    # Config logger
    if args.l:
        logging.basicConfig(handlers=[logging.FileHandler(os.path.dirname(args.input_file) + '/LOG_' + os.path.basename(args.input_file)[:-4] + '.log'),
                                      logging.StreamHandler()],
                            level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

    #                           #
    #                           #
    #                           #
    #    Bereich der ANALYSE    #
    #                           #
    #                           #
    #                           #

    import_graph = nx.DiGraph()
    hierarchie_dict = dict()
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

        hierarchie_dict = graph_json['hierarchy']
        logging.info('Graph was parsed successfully')

        # Überführung der Daten in einen gerichteten Graph
        logging.info('Graph is getting imported using networkx')
        try:
            import_graph.add_nodes_from(parse_nodes_list)
            import_graph.add_edges_from(parse_edges_list)
        except ValueError:
            return logging.warning('The graph could not be imported using networkx')

        logging.info('Graph was successfully imported')

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

    if args.use_ns:
        INST = Namespace(args.use_ns)
    else:

        INST = Namespace('https://example.org/%s#' % (uuid.uuid4()))

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

    # Export der Analyse- und Anreicherungsergebnisse im TXT-Format
    if args.i:
        logging.info('Information about the model is being saved')
        write_infos(result_set, args)
        logging.info('Information about the model was successfully saved')

    # Ablage der Wissensrepräsentation am Pfad
    logging.info('Linked data representation is getting serialized')
    g_ld.serialize(destination=os.path.dirname(args.input_file[0]) + '/LD-REP_' + os.path.basename(args.input_file[0])[:-5] + '.ttl', format='turtle')
    logging.info('Linked data representation was successfully serialized and saved')


if __name__ == "__main__":
    # Konzeption des Command Line Interface
    parser = argparse.ArgumentParser(description='Enrich the functional information in the given graph and save to a turtle serialisation of TSO')

    # Pfad zum Graph
    parser.add_argument('input_file', nargs='+', type=str, help='Path to the input graph as a JSON-file')

    # Ablage der Analyseergebnisse der enthaltenen Informationen zu technischen Systemen als Datei im TXT-Format am Pfad des Graphs.
    parser.add_argument('-i', action='store_true', help='Saving information about the graph in as *.txt at the give input directory')

    # Ablage des Logs zum Prozessfortschritts als Datei im TXT-Format am Pfad des Graphs.
    parser.add_argument('-l', action='store_true', help='Save log to file at the given input directory')

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

    parse_args = parser.parse_args()

    # Aufruf des GRAPH Prozesses mit den notwendigen und optionalen Parametern zur Anpassung der Funktionalität
    main(parse_args)
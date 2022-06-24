import networkx as nx
import re
import uuid


def init_regex():
    # Aufsetzen der regulären Ausdrücke für die Erkennung von technischen Systemen der TSO
    system_naming_conventions_import = dict()
    tsystem_naming_conections_import = dict()
    result_dict = dict()
    results_dict_ts = dict()

    # Funktionale Systeme
    system_naming_conventions_import['Automation System'] = []
    system_naming_conventions_import['Data System'] = []
    system_naming_conventions_import['Electrical System'] = []
    system_naming_conventions_import['Safety System'] = []
    system_naming_conventions_import['Fluid System'] = []
    system_naming_conventions_import['Drainage System'] = ['[\w\- ]*regenwasser[\w\- ]*', '[\w\- ]*brauchwasser[\w\- ]*']
    system_naming_conventions_import['Sanitary System'] = ['[\w\- ]*trinkwasser[\w\- ]*', '[\w\- ]*pwc[\w\- ]*', '[\w\- ]*pwh[\w\- ]*', '[\w\- ]*abwasser[\w\- ]*', '[\w\- ]*schmutzwasser[\w\- ]*']
    system_naming_conventions_import['Ventilation System'] = ['v_[\w\- ]*', '[\w\- ]*ods[\w\- ]*', '[\w\- ]*eta[\w\- ]*', '[\w\- ]*eoa[\w\- ]*', '[\w\- ]*sea[\w\- ]*', '[\w\- ]*eha[\w\- ]*',
                                                              '[\w\- ]*sup[\w\- ]*', '[\w\- ]*zuluft[\w\- ]*', '[\w\- ]*abluft[\w\- ]*', '[\w\- ]*fortluft[\w\- ]*',
                                                              '[\w\- ]*aussenluft[\w\- ]*', '[\w\- ]*außenluft[\w\- ]*']
    system_naming_conventions_import['Heating System'] = ['h_[\w\- ]*', 'hrl[\w\- ]*', 'hvl[\w\- ]*', '[\w\- ]*HRL[\w\- ]*', '[\w\- ]*HVL[\w\- ]*']
    system_naming_conventions_import['Cooling System'] = ['c_[\w\- ]*', 'k_[\w\- ]*']

    # Systemteile
    tsystem_naming_conections_import['Heating System'] = {"Supply System": ['[\w\- ]*vorlauf[\w\- ]*', '[\w\- ]*vl[\w\- ]*'], "Return System": ['[\w\- ]*rücklauf[\w\- ]*', '\w*rl\w*']}

    tsystem_naming_conections_import['Cooling System'] = {"Supply System": ['[\w\- ]*vorlauf[\w\- ]*', '[\w\- ]*vl[\w\- ]*'], "Return System": ['[\w\- ]*rücklauf[\w\- ]*', '\w*rl\w*']}

    tsystem_naming_conections_import['Ventilation System'] = {"Supply System_1": ['[\w\- ]*zuluft[\w\- ]*', '[\w\- ]*sup[\w\- ]*'],
                                                              "Return System_1": ['[\w\- ]*abluft[\w\- ]*','[\w\- ]*eth[\w\- ]*', '[\w\- ]*eta[\w\- ]*'],
                                                              "Return System_2": ['[\w\- ]*fortluft[\w\- ]*', '[\w\- ]*ehh[\w\- ]*', '[\w\- ]*eha[\w\- ]*'],
                                                              "Supply System_2": ['[\w\- ]*oda[\w\- ]*','[\w\- ]*aussenluft[\w\- ]*', '[\w\- ]*außenluft[\w\- ]*'],
                                                              "Distribution System": ['[\w\- ]*sea[\w\- ]*']}

    tsystem_naming_conections_import['Sanitary System'] = {"Return System": ['[\w\- ]*abwasser[\w\- ]*', '[\w\- ]*schmutzwasser[\w\- ]*'],
                                                           "Supply System": ['[\w\- ]*trinkwasser[\w\- ]*', '[\w\- ]*pwc[\w\- ]*', '[\w\- ]*pwh[\w\- ]*']}

    tsystem_naming_conections_import['Drainage System'] = {"Distribution System": ['[\w\- ]*regenwasser[\w\- ]*', '[\w\- ]*brauchwasser[\w\- ]*', '[\w\- ]*abwasser[\w\- ]*']}

    # Kompilieren der regulären Ausdrücke
    for key, values in system_naming_conventions_import.items():
        result_dict[key] = list()
        for value in values:
            value = re.compile(value)
            result_dict[key].append(value)

    for fs_key, values in tsystem_naming_conections_import.items():
        results_dict_ts[fs_key] = dict()
        for ts_key, value in values.items():
            tmp_list = list()
            for val in value:
                val = re.compile(val)
                tmp_list.append(val)
            results_dict_ts[fs_key][ts_key] = tmp_list

    return result_dict, results_dict_ts


def check_for_functional_systems(info_dict, hierarchie_dict):
    # Anreicherung von funktionalen Systemen basierend auf den schwachen Zusammenshangkomponenten und den gegebenen IFC-Systemen
    # Initialisierung der regulären Ausdrücke
    system_naming_conventions, tmp = init_regex()

    system_dict = dict()
    # Betrachtung aller schwach zusammenhängender Systeme
    for key, system in info_dict['Systems'].items():
        if isinstance(system, int):
            continue
        set_ifc_systems = set(system['IFC-Systems'])
        matches_dict = dict()
        # Kontrolle der IFC-Systeme auf Basis der regulären Ausdrücke
        for fs, fs_regex_list in system_naming_conventions.items():
            if not fs_regex_list:
                continue
            k = 0
            for fs_regex in fs_regex_list:
                if k == 1:
                    continue
                for s in set_ifc_systems:
                    if s:
                        # Übernahme der Informationen der IFC-Systeme in anzureichernde technische Systeme
                        if re.match(fs_regex, s.lower()):
                            if fs not in matches_dict:
                                matches_dict[fs] = dict()
                                matches_dict[fs]['Total'] = 1
                                matches_dict[fs]['Components'] = []
                                matches_dict[fs]['IFC-Systems'] = []

                                ifc_systems_list = list(info_dict['IFC-Systems'].keys())
                                for ifc_system in ifc_systems_list:
                                    if ifc_system:
                                        if s == ifc_system[0]:
                                            s = ifc_system
                                matches_dict[fs]['Components'].extend(info_dict['IFC-Systems'][s]['Components'])
                                matches_dict[fs]['IFC-Systems'].append(s[0])

                            else:
                                matches_dict[fs]['Total'] += 1
                                ifc_systems_list = list(info_dict['IFC-Systems'].keys())
                                for ifc_system in ifc_systems_list:
                                    if ifc_system:
                                        if s == ifc_system[0]:
                                            s = ifc_system
                                matches_dict[fs]['Components'].extend(info_dict['IFC-Systems'][s]['Components'])
                                matches_dict[fs]['IFC-Systems'].append(s[0])
                            k = 1

        # Überführung der Informationen in die festgelegte Ausgabestruktur
        # Anlegen eines Systemverbundes und untergeordneter funktionaler Systeme
        if len(matches_dict) > 1:
            system_id = str(uuid.uuid4())
            hierarchie_dict['IS'][system_id] = dict()
            hierarchie_dict['IS'][system_id]['Classification'] = None
            hierarchie_dict['IS'][system_id]['Components'] = system['Components']
            hierarchie_dict['IS'][system_id]['IFC-Systems'] = system['IFC-Systems']
            hierarchie_dict['IS'][system_id]['FS'] = []
            for comp in system['Components']:
                if comp not in system_dict:
                    system_dict[comp] = dict()
                    system_dict[comp]['IS'] = []
                    system_dict[comp]['FS'] = []
                    system_dict[comp]['TS'] = []
                system_dict[comp]['IS'].append(system_id)

            for system_classification, system_value in matches_dict.items():
                fs_system_id = str(uuid.uuid4())
                hierarchie_dict['FS'][fs_system_id] = dict()
                hierarchie_dict['FS'][fs_system_id]['Classification'] = system_classification
                hierarchie_dict['FS'][fs_system_id]['Components'] = system_value['Components']
                hierarchie_dict['FS'][fs_system_id]['IFC-Systems'] = system_value['IFC-Systems']
                hierarchie_dict['FS'][fs_system_id]['TS'] = []
                hierarchie_dict['IS'][system_id]['FS'].append(fs_system_id)

                for comp in system_value['Components']:
                    if comp not in system_dict:
                        system_dict[comp] = dict()
                        system_dict[comp]['IS'] = []
                        system_dict[comp]['FS'] = []
                        system_dict[comp]['TS'] = []
                    system_dict[comp]['FS'].append(fs_system_id)

        # Anlegen eines funktionalen Systems
        elif len(matches_dict) == 1:
            system_id = str(uuid.uuid4())
            hierarchie_dict['FS'][system_id] = dict()
            hierarchie_dict['FS'][system_id]['Classification'] = list(matches_dict.keys())[0]
            hierarchie_dict['FS'][system_id]['Components'] = system['Components']
            hierarchie_dict['FS'][system_id]['IFC-Systems'] = system['IFC-Systems']
            hierarchie_dict['FS'][system_id]['TS'] = []

            for comp in system['Components']:
                if comp not in system_dict:
                    system_dict[comp] = dict()
                    system_dict[comp]['IS'] = []
                    system_dict[comp]['FS'] = []
                    system_dict[comp]['TS'] = []
                system_dict[comp]['FS'].append(system_id)

    return hierarchie_dict, system_dict


def check_for_technical_systems(hierarchie_dict, import_graph, system_dict):
    # Anreicherung von technischen Systemen basierend auf den schwachen Zusammenshangkomponenten und den gegebenen IFC-Systemen
    # Initialisierung der regulären Ausdrücke
    tmp, technicalsystem_naming_conventions = init_regex()

    # Vorbereitung der Anreicherung
    lookup_dict_technical_sytems = import_graph.nodes.data('ifc_system')

    lookup_dict_components = dict()
    for node in import_graph.nodes(data=True):
        if not node[1]['ifc_system']:
            continue
        if node[1]['ifc_system'][0] not in lookup_dict_components:
            lookup_dict_components[node[1]['ifc_system'][0]] = list()
            lookup_dict_components[node[1]['ifc_system'][0]].append(node[0])
        else:
            lookup_dict_components[node[1]['ifc_system'][0]].append(node[0])

    # Anreicherung von Systemteilen für jedes vorhandene funktionale System
    for fs_id, fs_value in hierarchie_dict['FS'].items():
        matches_dict = dict()

        # Analyse der IFC-Systeme auf potentielle Matches
        for ifc_system in fs_value['IFC-Systems']:
            k = 0
            if not ifc_system:
                continue
            for ts, ts_regex_list in technicalsystem_naming_conventions[fs_value['Classification']].items():
                if not ts_regex_list:
                    continue
                if k == 1:
                    break
                for ts_regex in ts_regex_list:
                    if re.match(ts_regex, ifc_system.lower()):
                        if ts in matches_dict:
                            matches_dict[ts].append(ifc_system)
                        else:
                            matches_dict[ts] = list()
                            matches_dict[ts].append(ifc_system)
                        k = 1
                        break

        # Auswertung der Matches basierend auf dem Zusammenhang
        for match_key, match_systems in matches_dict.items():
            # Anlegen eines Systemteils
            if len(match_systems) == 1:
                ts_id = str(uuid.uuid4())
                hierarchie_dict['FS'][fs_id]['TS'].append(ts_id)
                hierarchie_dict['TS'][ts_id] = dict()

                if '_' in match_key:
                    system_classification = match_key.split('_')[0]
                else:
                    system_classification = match_key
                hierarchie_dict['TS'][ts_id]['Classification'] = system_classification
                hierarchie_dict['TS'][ts_id]['Components'] = lookup_dict_components[match_systems[0]]
                hierarchie_dict['TS'][ts_id]['IFC-Systems'] = match_systems
                hierarchie_dict['TS'][ts_id]['TS'] = []

                for comp in hierarchie_dict['TS'][ts_id]['Components']:
                    if comp not in system_dict:
                        system_dict[comp] = dict()
                        system_dict[comp]['IS'] = []
                        system_dict[comp]['FS'] = []
                        system_dict[comp]['TS'] = []
                    system_dict[comp]['TS'].append(ts_id)

            # Anlegen mehrerer Systemteile basierend auf dem Zusammenhang
            else:
                tmp_nodes = list()
                for match_system in match_systems:
                    tmp_nodes.extend(lookup_dict_components[match_system])
                tmp_subgraph = import_graph.subgraph(tmp_nodes)
                tmp_subgraph_weaklyconnsystems_list = sorted(nx.weakly_connected_components(tmp_subgraph), key=len, reverse=True)

                if len(tmp_subgraph_weaklyconnsystems_list) == 1:
                    ts_id = str(uuid.uuid4())
                    hierarchie_dict['FS'][fs_id]['TS'].append(ts_id)
                    hierarchie_dict['TS'][ts_id] = dict()

                    if '_' in match_key:
                        system_classification = match_key.split('_')[0]
                    else:
                        system_classification = match_key
                    hierarchie_dict['TS'][ts_id]['Classification'] = system_classification
                    hierarchie_dict['TS'][ts_id]['Components'] = tmp_nodes
                    hierarchie_dict['TS'][ts_id]['IFC-Systems'] = match_systems
                    hierarchie_dict['TS'][ts_id]['TS'] = []

                    for comp in tmp_nodes:
                        if comp not in system_dict:
                            system_dict[comp] = dict()
                            system_dict[comp]['IS'] = []
                            system_dict[comp]['FS'] = []
                            system_dict[comp]['TS'] = []
                        system_dict[comp]['TS'].append(ts_id)

                else:
                    for technical_system in tmp_subgraph_weaklyconnsystems_list:

                        ts_id = str(uuid.uuid4())
                        hierarchie_dict['FS'][fs_id]['TS'].append(ts_id)
                        hierarchie_dict['TS'][ts_id] = dict()

                        ifc_systems_list = list()
                        for comp in technical_system:
                            comp_ts = lookup_dict_technical_sytems[comp][0]
                            if comp_ts not in ifc_systems_list:
                                ifc_systems_list.append(comp_ts)

                        if '_' in match_key:
                            system_classification = match_key.split('_')[0]
                        else:
                            system_classification = match_key
                        hierarchie_dict['TS'][ts_id]['Classification'] = system_classification
                        hierarchie_dict['TS'][ts_id]['Components'] = list(technical_system)
                        hierarchie_dict['TS'][ts_id]['IFC-Systems'] = ifc_systems_list
                        hierarchie_dict['TS'][ts_id]['TS'] = []

                        for comp in tmp_nodes:
                            if comp not in system_dict:
                                system_dict[comp] = dict()
                                system_dict[comp]['IS'] = []
                                system_dict[comp]['FS'] = []
                                system_dict[comp]['TS'] = []
                            system_dict[comp]['TS'].append(ts_id)

    return hierarchie_dict, system_dict


def get_comp_by_ifc_system(system_list, info_dict):
    # Abfragen der Komponenten basierend auf dem übergebenen IFC-System
    result_set = set()
    ifc_system_list = list(info_dict['IFC-Systems'].keys())
    for system in system_list:
        for ifc_system in ifc_system_list:
            if not ifc_system:
                continue
            if system == ifc_system[0]:
                result_set.update(set(info_dict['IFC-Systems'][ifc_system]['Components']))
                break

    return list(result_set)


def get_system_hierarchy(system_json, info_dict, hierarchie_dict):
    # Anreicherung der Systemhierarchie basierend auf dem expliziten Input des Nutzers
    system_dict = dict()

    for key, value in system_json.items():
        # Anreicherung von Systemverbunden
        if key == 'IS':
            for system_key, system_value in value.items():
                system_id = system_key
                hierarchie_dict['IS'][system_id] = dict()
                hierarchie_dict['IS'][system_id]['Classification'] = None
                comp_list = get_comp_by_ifc_system(system_value['IFC-Systems'], info_dict)
                for comp in comp_list:
                    if comp not in system_dict:
                        system_dict[comp] = dict()
                        system_dict[comp]['IS'] = []
                        system_dict[comp]['FS'] = []
                        system_dict[comp]['TS'] = []
                    system_dict[comp]['IS'].append(system_id)
                hierarchie_dict['IS'][system_id]['Components'] = comp_list
                hierarchie_dict['IS'][system_id]['IFC-Systems'] = system_value['IFC-Systems']

        # Anreicherung von funktionalen Systemen
        elif key == 'FS':
            for system_key, system_value in value.items():
                system_id = system_key
                hierarchie_dict['FS'][system_id] = dict()
                hierarchie_dict['FS'][system_id]['Classification'] = system_value['Classification']
                comp_set = set(get_comp_by_ifc_system(system_value['IFC-Systems'], info_dict))
                comp_set.update(set(system_value['Components']['Add']))
                comp_set -= set(system_value['Components']['Delete'])
                comp_list = list(comp_set)
                for comp in comp_list:
                    if comp not in system_dict:
                        system_dict[comp] = dict()
                        system_dict[comp]['IS'] = []
                        system_dict[comp]['FS'] = []
                        system_dict[comp]['TS'] = []
                    system_dict[comp]['FS'].append(system_id)
                hierarchie_dict['FS'][system_id]['Components'] = comp_list
                hierarchie_dict['FS'][system_id]['IFC-Systems'] = system_value['IFC-Systems']

        # Anreicherung von Systemteilen
        elif key == 'TS':
            for system_key, system_value in value.items():
                system_id = system_key
                hierarchie_dict['TS'][system_id] = dict()
                hierarchie_dict['TS'][system_id]['Classification'] = system_value['Classification']
                comp_set = set(get_comp_by_ifc_system(system_value['IFC-Systems'], info_dict))
                comp_set.update(set(system_value['Components']['Add']))
                comp_set -= set(system_value['Components']['Delete'])
                comp_list = list(comp_set)
                for comp in comp_list:
                    if comp not in system_dict:
                        system_dict[comp] = dict()
                        system_dict[comp]['IS'] = []
                        system_dict[comp]['FS'] = []
                        system_dict[comp]['TS'] = []
                    system_dict[comp]['TS'].append(system_id)
                hierarchie_dict['TS'][system_id]['Components'] = comp_list
                hierarchie_dict['TS'][system_id]['IFC-Systems'] = system_value['IFC-Systems']

    # Übernahme der hierarchischen Untergliederung der technischen Systeme
    for key, value in hierarchie_dict.items():
        if key == 'IS':
            for system_id, system_value in value.items():
                system_value['FS'] = system_json[key][system_id]['FS']
        if key == 'FS':
            for system_id, system_value in value.items():
                system_value['TS'] = system_json[key][system_id]['TS']
        if key == 'TS':
            for system_id, system_value in value.items():
                system_value['TS'] = system_json[key][system_id]['TS']

    return hierarchie_dict, system_dict


def convert_import_graph_in_export_graph(import_graph, system_dict):
    # Parsen des Graphs und Übergabe der hierarchischen Informationen
    export_graph = nx.DiGraph()

    # Parsen der Knoten
    for node in import_graph.nodes(data=True):

        # Übergabe der hierarchischen Informationen
        if node[0] in system_dict:
            integrated_systems = system_dict[node[0]]['IS']
            functional_systems = system_dict[node[0]]['FS']
            technical_systems = system_dict[node[0]]['TS']
        else:
            integrated_systems = []
            functional_systems = []
            technical_systems = []

        export_graph.add_node(node[0], ifc_id=node[1]['ifc_id'], ifc_class=node[1]['ifc_class'], ifc_type=node[1]['ifc_type'], ifc_name=node[1]['ifc_name'], ifc_description=node[1]['ifc_description'],
                              ifc_system=node[1]['ifc_system'], ifc_position=node[1]['ifc_position'], elem_rds=node[1]['elem_rds'], additional_data=node[1]['additional_data'], integrated_systems=integrated_systems,
                              functional_systems=functional_systems, technical_systems=technical_systems)

    # Parsen der Kanten
    for edge in import_graph.edges:
        export_graph.add_edge(edge[0], edge[1], aggregated_nodes=[])

    return export_graph


def check_system_connections(import_graph, hierarchie_dict, system_dict):
    # Analyse der Schnittstellen der technischen Systeme
    tmp_list = list()
    for sys_hier, systems in hierarchie_dict.items():
        if len(systems) <= 1:
            for sys_key, sys_value in systems.items():
                sys_value['Schnittstellen'] = []
        else:
            comp_dict = dict()
            for sys_key, sys_value in systems.items():
                comp_dict[sys_key] = set(sys_value['Components'])
                sys_value['Schnittstellen'] = []

            connected_edges = set()
            for edge in import_graph.edges():
                systems_0 = set(system_dict[edge[0]][sys_hier])
                systems_1 = set(system_dict[edge[1]][sys_hier])

                if systems_0 == systems_1:
                    continue

                for sys_key, sys_comp in comp_dict.items():
                    if edge[0] in sys_comp:
                        for sys_key_2, sys_comp_2 in comp_dict.items():
                            if sys_key == sys_key_2:
                                continue
                            if edge[1] in sys_comp_2:
                                if edge not in connected_edges and (edge[1], edge[0]) not in connected_edges:
                                    systems[sys_key]['Schnittstellen'].append(sys_key_2)
                                    systems[sys_key_2]['Schnittstellen'].append(sys_key)
                                    connected_edges.add(edge)

                                    tmp_dict = {
                                        'Source_System': sys_key,
                                        'Target_System': sys_key_2,
                                        'Source_Component': edge[0],
                                        'Target_Component': edge[1]
                                    }
                                    tmp_list.append(tmp_dict)
                    if edge[1] in sys_comp:
                        for sys_key_2, sys_comp_2 in comp_dict.items():
                            if sys_key == sys_key_2:
                                continue
                            if edge[0] in sys_comp_2:
                                if edge not in connected_edges and (edge[1], edge[0]) not in connected_edges:
                                    systems[sys_key]['Schnittstellen'].append(sys_key_2)
                                    systems[sys_key_2]['Schnittstellen'].append(sys_key)
                                    connected_edges.add(edge)

                                    tmp_dict = {
                                        'Source_System': sys_key,
                                        'Target_System': sys_key_2,
                                        'Source_Component': edge[0],
                                        'Target_Component': edge[1]
                                    }
                                    tmp_list.append(tmp_dict)

    hierarchie_dict['Schnittstellen'] = tmp_list
    return hierarchie_dict


def aggregate_graph(directed_graph):
    # Aggregation des gerichteten Graphs
    # Vorbereitung der Aggregation
    aggregated_directed_graph = directed_graph.copy()
    aggregated_directed_graph_nodes = list(aggregated_directed_graph.nodes(data=True))

    # Festlegung von Elementklassifizierungen die aggregiert werden dürfen
    segment_set = {'IfcPipeSegment', 'IfcDuctSegment'}
    fitting_set = {'IfcPipeFitting', 'IfcDuctFitting'}
    complete_set = segment_set.union(fitting_set)

    # Startpunkt der Aggragation
    for node in aggregated_directed_graph_nodes:
        # Abrufen der Nachbarn des Knotens
        pre_edges = list(aggregated_directed_graph.predecessors(node[0]))
        suc_edges = list(aggregated_directed_graph.successors(node[0]))
        complete_edges = list(set(pre_edges) | set(suc_edges))

        # Aggregation
        if node[1]['ifc_class'] in complete_set:
            if len(complete_edges) == 0:
                aggregated_directed_graph.remove_node(node[0])
            elif len(complete_edges) == 1:
                aggregated_directed_graph.remove_node(node[0])
            elif len(pre_edges) == 1 and len(suc_edges) == 1:
                removed_nodes_set = set()
                try:
                    removed_nodes_set.update(aggregated_directed_graph.edges[pre_edges[0], node[0]]['aggregated_nodes'])
                except KeyError:
                    pass

                try:
                    removed_nodes_set.update(aggregated_directed_graph.edges[node[0], suc_edges[0]]['aggregated_nodes'])
                except KeyError:
                    pass

                removed_nodes_set.add(node[0])
                aggregated_directed_graph.remove_node(node[0])
                aggregated_directed_graph.add_edge(pre_edges[0], suc_edges[0], aggregated_nodes=list(removed_nodes_set))

            elif len(complete_edges) == 2:
                removed_nodes_set = set()
                try:
                    removed_nodes_set.update(aggregated_directed_graph.edges[node[0], complete_edges[0]]['aggregated_nodes'])
                except KeyError:
                    pass

                try:
                    removed_nodes_set.update(aggregated_directed_graph.edges[complete_edges[0], node[0]]['aggregated_nodes'])
                except KeyError:
                    pass

                try:
                    removed_nodes_set.update(aggregated_directed_graph.edges[node[0], complete_edges[1]]['aggregated_nodes'])
                except KeyError:
                    pass

                try:
                    removed_nodes_set.update(aggregated_directed_graph.edges[complete_edges[1], node[0]]['aggregated_nodes'])
                except KeyError:
                    pass

                removed_nodes_set.add(node[0])
                aggregated_directed_graph.remove_node(node[0])
                aggregated_directed_graph.add_edge(complete_edges[0], complete_edges[1], aggregated_nodes=list(removed_nodes_set))
        else:
            if len(complete_edges) == 0:
                aggregated_directed_graph.remove_node(node[0])

    return aggregated_directed_graph

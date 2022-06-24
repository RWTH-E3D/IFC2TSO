from rdflib import Literal, RDF, Graph, Namespace, RDFS
import uuid
from urllib.parse import quote

from helper_enrich import *


def convert_hierarchicalconcepts_to_tso(g_ld, args, enriched_graph, hierarchie_dict, IFC, INST, TSO, RDF, RDFS):
    # Anlegen der hierarchischen Konzepten (kein Input benötigt)
    # TSO-Klassen: IntegratedSystem, FunctionalSystem (und Subklassen zur Klassifizierung), TechnicalSystem (und Subklassen zur Klassifizierung), Component, State
    # TSO-OP: hasState, stateOf, subSystemOf, hasSubSystem, integratedSystemOf, hasIntegratedSystem, functionalSystemOf, hasFunctionalSystem,
    # TSO-OP: technicalSystemOf, hasTechnicalSystem, componentOf, hasComponent, subStateOf, hasSubState
    # IFC-Klassen: IfcDistributionElement (und Subklassen zur Klassifizierung)
    # IFC-OP: PredefinedType

    # Anlegen von Komponenten
    state_dict = dict()
    if args.ifcowl:
        for node in enriched_graph.nodes(data=True):
            # Anlegen des Komponentenknotens und Zuweisung des Labels
            g_ld.add((INST[quote(node[0])], RDF.type, TSO.Component))
            g_ld.add((INST[quote(node[0])], RDFS.label, Literal(node[1]['ifc_name'])))

            # Anlegen eines Zustand und Zuweisung von diesem
            state_uuid = str(uuid.uuid4())
            state_dict[node[0]] = state_uuid
            g_ld.add((INST[state_uuid], RDF.type, TSO.State))
            g_ld.add((INST[quote(node[0])], TSO.hasState, INST[state_uuid]))
            g_ld.add((INST[state_uuid], TSO.stateOf, INST[quote(node[0])]))

            # Anlegen einer Komponentenklassifizierung
            g_ld = add_component_classification(g_ld, node, INST, IFC)
            g_ld = add_component_classification_type(g_ld, node, INST, IFC)

    else:
        for node in enriched_graph.nodes(data=True):
            # Anlegen des Komponentenknotens und Zuweisung des Labels
            g_ld.add((INST[quote(node[0])], RDF.type, TSO.Component))
            g_ld.add((INST[quote(node[0])], RDFS.label, Literal(node[1]['ifc_name'])))

            # Anlegen eines Zustand und Zuweisung von diesem
            state_uuid = str(uuid.uuid4())
            state_dict[node[0]] = state_uuid
            g_ld.add((INST[state_uuid], RDF.type, TSO.State))
            g_ld.add((INST[quote(node[0])], TSO.hasState, INST[state_uuid]))
            g_ld.add((INST[state_uuid], TSO.stateOf, INST[quote(node[0])]))

    # Anlegen von integralen Systemen und der hierrarchischen Untergliederung dieser zu untergeordneten Systemen
    for i_s_id, i_s in hierarchie_dict['IS'].items():
        # Anlegen des Systemknotens
        g_ld.add((INST[i_s_id], RDF.type, TSO.IntegratedSystem))

        # Anlegen eines Zustand und Zuweisung von diesem
        state_uuid = str(uuid.uuid4())
        state_dict[i_s_id] = state_uuid
        g_ld.add((INST[state_uuid], RDF.type, TSO.State))
        g_ld.add((INST[i_s_id], TSO.hasState, INST[state_uuid]))
        g_ld.add((INST[state_uuid], TSO.stateOf, INST[i_s_id]))

        # Anlegen einer hierarchischen Untergliederung
        for f_s_id in i_s['FS']:
            g_ld.add((INST[i_s_id], TSO.hasSubSystem, INST[f_s_id]))
            g_ld.add((INST[f_s_id], TSO.subSystemOf, INST[i_s_id]))

            g_ld.add((INST[i_s_id], TSO.hasFunctionalSystem, INST[f_s_id]))
            g_ld.add((INST[f_s_id], TSO.functionalSystemOf, INST[i_s_id]))

        if not i_s['FS']:
            for comp_id in i_s['Components']:
                g_ld.add((INST[i_s_id], TSO.hasSubSystem, INST[comp_id]))
                g_ld.add((INST[comp_id], TSO.subSystemOf, INST[i_s_id]))

                g_ld.add((INST[i_s_id], TSO.hasComponent, INST[comp_id]))
                g_ld.add((INST[comp_id], TSO.componentOf, INST[i_s_id]))

    # Anlegen von funktionalen Systemen und der hierrarchischen Untergliederung dieser zu untergeordneten Systemen
    for f_s_id, f_s in hierarchie_dict['FS'].items():

        # Anlegen des Systemknotens und der Klassifizierung von diesem
        g_ld.add((INST[f_s_id], RDF.type, TSO.FunctionalSystem))

        for classification in f_s['Classification']:
            if classification == 'Heating System':
                g_ld.add((INST[f_s_id], RDF.type, TSO.HeatingSystem))
            elif classification == 'Cooling System':
                g_ld.add((INST[f_s_id], RDF.type, TSO.CoolingSystem))
            elif classification == 'Automation System':
                g_ld.add((INST[f_s_id], RDF.type, TSO.AutomationSystem))
            elif classification == 'Data System':
                g_ld.add((INST[f_s_id], RDF.type, TSO.DataSystem))
            elif classification == 'Drainage System':
                g_ld.add((INST[f_s_id], RDF.type, TSO.DrainageSystem))
            elif classification == 'Electrical System':
                g_ld.add((INST[f_s_id], RDF.type, TSO.ElextricalSystem))
            elif classification == 'Fluid System':
                g_ld.add((INST[f_s_id], RDF.type, TSO.FluidSystem))
            elif classification == 'Safety System':
                g_ld.add((INST[f_s_id], RDF.type, TSO.SafetySystem))
            elif classification == 'Sanitary System':
                g_ld.add((INST[f_s_id], RDF.type, TSO.SanitarySystem))
            elif classification == 'Ventilation System':
                g_ld.add((INST[f_s_id], RDF.type, TSO.VentilationSystem))

        # Anlegen eines Zustand und Zuweisung von diesem
        state_uuid = str(uuid.uuid4())
        state_dict[f_s_id] = state_uuid
        g_ld.add((INST[state_uuid], RDF.type, TSO.State))
        g_ld.add((INST[f_s_id], TSO.hasState, INST[state_uuid]))
        g_ld.add((INST[state_uuid], TSO.stateOf, INST[f_s_id]))

        # Anlegen einer hierarchischen Untergliederung
        for t_s_id in f_s['TS']:
            g_ld.add((INST[f_s_id], TSO.hasSubSystem, INST[t_s_id]))
            g_ld.add((INST[t_s_id], TSO.subSystemOf, INST[f_s_id]))

            g_ld.add((INST[f_s_id], TSO.hasTechnicalSystem, INST[t_s_id]))
            g_ld.add((INST[t_s_id], TSO.techncialSystemOf, INST[t_s_id]))

        if not f_s['TS']:
            for comp_id in f_s['Components']:
                g_ld.add((INST[f_s_id], TSO.hasSubSystem, INST[quote(comp_id)]))
                g_ld.add((INST[quote(comp_id)], TSO.subSystemOf, INST[f_s_id]))

                g_ld.add((INST[f_s_id], TSO.hasComponent, INST[quote(comp_id)]))
                g_ld.add((INST[quote(comp_id)], TSO.componentOf, INST[f_s_id]))

    # Anlegen von technischen Systemen und der hierrarchischen Untergliederung dieser zu untergeordneten Systemen
    for t_s_id, t_s in hierarchie_dict['TS'].items():

        # Anlegen des Systemknotens und der Klassifizierung von diesem
        g_ld.add((INST[t_s_id], RDF.type, TSO.TechnicalSystem))

        if t_s['Classification'] == 'Conversion System':
            g_ld.add((INST[t_s_id], RDF.type, TSO.ConversionSystem))
        elif t_s['Classification'] == 'Storage System':
            g_ld.add((INST[t_s_id], RDF.type, TSO.StorageSystem))
        elif t_s['Classification'] == 'Distribution System':
            g_ld.add((INST[t_s_id], RDF.type, TSO.DistributionSystem))
        elif t_s['Classification'] == 'Supply System':
            g_ld.add((INST[t_s_id], RDF.type, TSO.SupplySystem))
        elif t_s['Classification'] == 'Return System':
            g_ld.add((INST[t_s_id], RDF.type, TSO.ReturnSystem))
        elif t_s['Classification'] == 'Energy Conversion System':
            g_ld.add((INST[t_s_id], RDF.type, TSO.EnergyConversionSystem))
        elif t_s['Classification'] == 'Matter Conversion System':
            g_ld.add((INST[t_s_id], RDF.type, TSO.MatterConversionSystem))
        elif t_s['Classification'] == 'Data Conversion System':
            g_ld.add((INST[t_s_id], RDF.type, TSO.DataConversionSystem))

        # Anlegen eines Zustand und Zuweisung von diesem
        state_uuid = str(uuid.uuid4())
        state_dict[t_s_id] = state_uuid
        g_ld.add((INST[state_uuid], RDF.type, TSO.State))
        g_ld.add((INST[t_s_id], TSO.hasState, INST[state_uuid]))
        g_ld.add((INST[state_uuid], TSO.stateOf, INST[t_s_id]))

        # Anlegen einer hierarchischen Untergliederung
        for t_s_id_ss in t_s['TS']:
            g_ld.add((INST[t_s_id], TSO.hasSubSystem, INST[t_s_id_ss]))
            g_ld.add((INST[t_s_id_ss], TSO.subSystemOf, INST[t_s_id]))

            g_ld.add((INST[t_s_id], TSO.hasTechnicalSystem, INST[t_s_id_ss]))
            g_ld.add((INST[t_s_id_ss], TSO.techncialSystemOf, INST[t_s_id]))

        if not t_s['TS']:
            for comp_id in t_s['Components']:
                g_ld.add((INST[t_s_id], TSO.hasSubSystem, INST[quote(comp_id)]))
                g_ld.add((INST[quote(comp_id)], TSO.subSystemOf, INST[t_s_id]))

                g_ld.add((INST[t_s_id], TSO.hasComponent, INST[quote(comp_id)]))
                g_ld.add((INST[quote(comp_id)], TSO.componentOf, INST[t_s_id]))

    # Anlegen der hierarchischen Untergliederung von Zuständen über alle Hierarchielevel von Systemen
    for i_s_id, i_s in hierarchie_dict['IS'].items():
        for f_s_id in i_s['FS']:
            g_ld.add((INST[state_dict[i_s_id]], TSO.hasSubState, INST[state_dict[f_s_id]]))
            g_ld.add((INST[state_dict[f_s_id]], TSO.subStateOf, INST[state_dict[i_s_id]]))

    for f_s_id, f_s in hierarchie_dict['FS'].items():
        for t_s_id in f_s['TS']:
            g_ld.add((INST[state_dict[f_s_id]], TSO.hasSubState, INST[state_dict[t_s_id]]))
            g_ld.add((INST[state_dict[t_s_id]], TSO.subStateOf, INST[state_dict[f_s_id]]))

    for t_s_id, t_s in hierarchie_dict['TS'].items():
        for t_s_id_ss in t_s['TS']:
            g_ld.add((INST[state_dict[t_s_id]], TSO.hasSubState, INST[state_dict[t_s_id_ss]]))
            g_ld.add((INST[state_dict[t_s_id_ss]], TSO.subStateOf, INST[state_dict[t_s_id]]))

    return g_ld, state_dict


def convert_topologicalconcepts_to_tso(g_ld, enriched_graph, hierarchie_dict, ic_json, INST, TSO, RDF):
    # Anlegen der topologischen Konzepte (Input benötigt für angereicherte innere Verbindungen)
    # TSO-Klassen: ConnectionPoint, InnerConnection, OuterConnection
    # TSO-OP: connects, connectsAt, connectionPointOf, connectsSystem, connectedThrough, connectsSystemAt, connectsSystemThrough, subConnectionPointOf, hasSubConnectionPoint

    # Anlegen der topologischen Konzepte für Komponenten
    edge_set = set()
    outer_edge_dict = dict()
    inner_edge_dict = dict()
    for node in enriched_graph.nodes(data=True):
        pre = enriched_graph.predecessors(node[0])
        suc = enriched_graph.successors(node[0])
        neighbors = list(pre) + list(suc)
        for neighbor in set(neighbors):
            if (node[0], neighbor) not in edge_set:
                # Anlegen des Verbindungspunkt der Komponente
                node_cp = str(uuid.uuid4())
                g_ld.add((INST[node_cp], RDF.type, TSO.ConnectionPoint))
                g_ld.add((INST[quote(node[0])], TSO.connectsAt, INST[node_cp]))
                g_ld.add((INST[node_cp], TSO.connectionPointOf, INST[quote(node[0])]))

                # Anlegen des Verbindungspunkt des Nachbarns
                neigbhor_cp = str(uuid.uuid4())
                g_ld.add((INST[neigbhor_cp], RDF.type, TSO.ConnectionPoint))
                g_ld.add((INST[quote(neighbor)], TSO.connectsAt, INST[neigbhor_cp]))
                g_ld.add((INST[neigbhor_cp], TSO.connectionPointOf, INST[quote(neighbor)]))

                # Anlegen der äußeren Verbindung
                outer_connection = str(uuid.uuid4())
                g_ld.add((INST[outer_connection], RDF.type, TSO.OuterConnection))
                g_ld.add((INST[outer_connection], TSO.connectsSystemThrough, INST[neigbhor_cp]))
                g_ld.add((INST[neigbhor_cp], TSO.connectsSystemAt, INST[outer_connection]))
                g_ld.add((INST[outer_connection], TSO.connectsSystemThrough, INST[node_cp]))
                g_ld.add((INST[node_cp], TSO.connectsSystemAt, INST[outer_connection]))

                g_ld.add((INST[outer_connection], TSO.connectsSystem, INST[quote(node[0])]))
                g_ld.add((INST[quote(node[0])], TSO.connectedThrough, INST[outer_connection]))
                g_ld.add((INST[outer_connection], TSO.connectsSystem, INST[quote(neighbor)]))
                g_ld.add((INST[quote(neighbor)], TSO.connectedThrough, INST[outer_connection]))

                # Direkte Verbindung der Komponenten über connects
                g_ld.add((INST[quote(node[0])], TSO.connects, INST[quote(neighbor)]))
                g_ld.add((INST[quote(neighbor)], TSO.connects, INST[quote(node[0])]))

                # Hinzufügen der Kante in eine ungerichtete Sammlung der Kanten
                edge_set.add((node[0], neighbor))
                edge_set.add((neighbor, node[0]))

                # Hinzufügen der Verbindung in ein Dictionary der äußeren Verbindungen mit der GUID der Verbindungspunkte und der Verbindung
                outer_edge_dict[(node[0], neighbor)] = [node_cp, neigbhor_cp, outer_connection]

        # Anlegen von inneren Verbindungen und die Verbindung zur den Verbindungspunkten
        if len(neighbors) <= 1:
            continue
        else:
            # Falls der Knoten im importierten Dictionary vorhanden ist werden die entsprechenden Informationen übernommen
            if node[0] in ic_json:
                inner_edge_dict[node[0]] = list()
                for inner_connection in ic_json[node[0]]:
                    # Anlegen einer inneren Verbindung
                    g_ld.add((INST[inner_connection['InnerConnection']], RDF.type, TSO.InnerConnection))

                    # Zuordnung der inneren Verbindung zu den Verbindungspunkten
                    tmp_list = list()
                    for connected_elem in inner_connection['neighbor_ids']:
                        try:
                            node_cp = outer_edge_dict[(node[0], connected_elem)][0]
                            g_ld.add((INST[inner_connection['InnerConnection']], TSO.connectsSystemThrough, INST[quote(node_cp)]))
                            g_ld.add((INST[quote(node_cp)], TSO.connectsSystemAt, INST[inner_connection['InnerConnection']]))
                        except KeyError:
                            node_cp = outer_edge_dict[(connected_elem, node[0])][1]
                            g_ld.add((INST[inner_connection['InnerConnection']], TSO.connectsSystemThrough, INST[quote(node_cp)]))
                            g_ld.add((INST[quote(node_cp)], TSO.connectsSystemAt, INST[inner_connection['InnerConnection']]))

                        tmp_list.append(node_cp)

                    # Hinzufügen der Verbindung in ein Dictionary der inneren Verbindungen mit der GUID der Verbindungspunkte und der Verbindung
                    inner_edge_dict[node[0]].append([tmp_list, inner_connection['InnerConnection']])
            # Falls der Knoten im importierten Dictionary nicht vorhanden ist werden die vorhandenen Verbindungspunkte verbunden
            else:
                # Anlegen einer inneren Verbindung
                inner_connection = str(uuid.uuid4())
                g_ld.add((INST[inner_connection], RDF.type, TSO.InnerConnection))
                inner_edge_dict[node[0]] = list()

                # Zuordnung der inneren Verbindung zu den Verbindungspunkten
                tmp_list = list()
                for connected_elem in neighbors:
                    try:
                        node_cp = outer_edge_dict[(node[0], connected_elem)][0]
                        g_ld.add((INST[inner_connection], TSO.connectsSystemThrough, INST[quote(node_cp)]))
                        g_ld.add((INST[quote(node_cp)], TSO.connectsSystemAt, INST[inner_connection]))
                    except KeyError:
                        node_cp = outer_edge_dict[(connected_elem, node[0])][1]
                        g_ld.add((INST[inner_connection], TSO.connectsSystemThrough, INST[quote(node_cp)]))
                        g_ld.add((INST[quote(node_cp)], TSO.connectsSystemAt, INST[inner_connection]))
                    tmp_list.append(node_cp)

                # Hinzufügen der Verbindung in ein Dictionary der inneren Verbindungen mit der GUID der Verbindungspunkte und der Verbindung
                inner_edge_dict[node[0]].append([tmp_list, inner_connection])

    # Anlegen der topologischen Konzepte für integrale-, funktional- und technische Systeme sowie die hierarchische Untergliederung von Verbindungspunkten
    edge_set_systems = set()
    ic_dict = dict()
    for connection_dict in hierarchie_dict['Schnittstellen']:

        # Analyse der Komponenten der verbundenen Systeme um mehrere Verbindungen über Komponenten, die in beiden Systemen sind, auszuschließen
        source_system_comp = get_system_comp_by_key(hierarchie_dict, connection_dict['Source_System'])
        target_system_comp = get_system_comp_by_key(hierarchie_dict, connection_dict['Target_System'])

        if connection_dict['Source_Component'] in source_system_comp and connection_dict['Source_Component'] in target_system_comp:
            edge = (connection_dict['Source_System'], connection_dict['Target_System'], connection_dict['Source_Component'], connection_dict['Source_Component'])
        elif connection_dict['Target_Component'] in source_system_comp and connection_dict['Target_Component'] in target_system_comp:
            edge = (connection_dict['Source_System'], connection_dict['Target_System'], connection_dict['Target_Component'], connection_dict['Target_Component'])
        else:
            edge = (connection_dict['Source_System'], connection_dict['Target_System'], connection_dict['Source_Component'], connection_dict['Target_Component'])

        if edge not in edge_set_systems:
            # Anlegen des Verbindungspunkt des Source Systems
            system_source_cp = str(uuid.uuid4())
            g_ld.add((INST[system_source_cp], RDF.type, TSO.ConnectionPoint))
            g_ld.add((INST[connection_dict['Source_System']], TSO.connectsAt, INST[system_source_cp]))
            g_ld.add((INST[system_source_cp], TSO.connectionPointOf, INST[connection_dict['Source_System']]))

            # Anlegen des Verbindungspunkt des Target Systems
            system_target_cp = str(uuid.uuid4())
            g_ld.add((INST[system_target_cp], RDF.type, TSO.ConnectionPoint))
            g_ld.add((INST[connection_dict['Target_System']], TSO.connectsAt, INST[system_target_cp]))
            g_ld.add((INST[system_target_cp], TSO.connectionPointOf, INST[connection_dict['Target_System']]))

            # Anlegen der äußeren Verbindung
            outer_connection = str(uuid.uuid4())
            g_ld.add((INST[outer_connection], RDF.type, TSO.OuterConnection))
            g_ld.add((INST[outer_connection], TSO.connectsSystemThrough, INST[system_source_cp]))
            g_ld.add((INST[system_source_cp], TSO.connectsSystemAt, INST[outer_connection]))
            g_ld.add((INST[outer_connection], TSO.connectsSystemThrough, INST[system_target_cp]))
            g_ld.add((INST[system_target_cp], TSO.connectsSystemAt, INST[outer_connection]))

            g_ld.add((INST[outer_connection], TSO.connectsSystem, INST[connection_dict['Source_System']]))
            g_ld.add((INST[connection_dict['Source_System']], TSO.connectedThrough, INST[outer_connection]))
            g_ld.add((INST[outer_connection], TSO.connectsSystem, INST[connection_dict['Target_System']]))
            g_ld.add((INST[connection_dict['Target_System']], TSO.connectedThrough, INST[outer_connection]))

            # Direkte Verbindung der Systeme über connects
            if (connection_dict['Source_System'], connection_dict['Target_System']) not in edge_set_systems:
                g_ld.add((INST[connection_dict['Source_System']], TSO.connects, INST[connection_dict['Target_System']]))
                g_ld.add((INST[connection_dict['Target_System']], TSO.connects, INST[connection_dict['Source_System']]))

            # Hinzufügen der Verbindung in eine Sammlung von Kanten
            edge_set_systems.add((connection_dict['Source_System'], connection_dict['Target_System'], edge[2], edge[3]))
            edge_set_systems.add((connection_dict['Target_System'], connection_dict['Source_System'], edge[2], edge[3]))
            edge_set_systems.add((connection_dict['Source_System'], connection_dict['Target_System'], edge[3], edge[2]))
            edge_set_systems.add((connection_dict['Target_System'], connection_dict['Source_System'], edge[3], edge[2]))

            # Hinzufügen der Verbindung in ein Dictionary der äußeren Verbindungen mit der GUID der Verbindungspunkte und der Verbindung
            outer_edge_dict[(connection_dict['Source_System'], connection_dict['Target_System'])] = [system_source_cp, system_target_cp, outer_connection]

            # Zuordnung der Verbindungspunkte zu den Systemen
            if connection_dict['Source_System'] not in ic_dict:
                ic_dict[connection_dict['Source_System']] = []
                ic_dict[connection_dict['Source_System']].append(system_source_cp)
            else:
                ic_dict[connection_dict['Source_System']].append(system_source_cp)

            if connection_dict['Target_System'] not in ic_dict:
                ic_dict[connection_dict['Target_System']] = []
                ic_dict[connection_dict['Target_System']].append(system_target_cp)
            else:
                ic_dict[connection_dict['Target_System']].append(system_target_cp)

            # Anlegen von hierarchischen Untergliederungen von Verbindungspunkten
            if (connection_dict['Source_Component'], connection_dict['Target_Component']) in outer_edge_dict:
                sub_cp = outer_edge_dict[(connection_dict['Source_Component'], connection_dict['Target_Component'])]

                g_ld.add((INST[system_source_cp], TSO.hasSubConnectionPoint, INST[sub_cp[0]]))
                g_ld.add((INST[sub_cp[0]], TSO.subConnectionPointOf, INST[system_source_cp]))

                g_ld.add((INST[system_target_cp], TSO.hasSubConnectionPoint, INST[sub_cp[1]]))
                g_ld.add((INST[sub_cp[1]], TSO.subConnectionPointOf, INST[system_target_cp]))

    # Anlegen von inneren Verbindungen für integrale-, funktionale- und technische Systeme
    for key, value in ic_dict.items():
        if len(value) <= 1:
            continue
        else:
            # Falls der Knoten im importierten Dictionary vorhanden ist werden die entsprechenden Informationen übernommen
            if key in ic_json:
                for inner_connection in ic_json[key]:
                    g_ld.add((INST[inner_connection['InnerConnection']], RDF.type, TSO.InnerConnection))

                    tmp_list = list()
                    for connected_elem in inner_connection['neighbor_ids']:
                        try:
                            node_cp = outer_edge_dict[(key, connected_elem)][0]
                            g_ld.add((INST[inner_connection], TSO.connectsSystemThrough, INST[node_cp]))
                            g_ld.add((INST[node_cp], TSO.connectsSystemAt, INST[inner_connection]))
                        except KeyError:
                            node_cp = outer_edge_dict[(connected_elem, key)][1]
                            g_ld.add((INST[inner_connection], TSO.connectsSystemThrough, INST[node_cp]))
                            g_ld.add((INST[node_cp], TSO.connectsSystemAt, INST[inner_connection]))

                        tmp_list.append(node_cp)

                    inner_edge_dict[key] = [tmp_list, inner_connection]

            else:
                inner_connection = str(uuid.uuid4())
                g_ld.add((INST[inner_connection], RDF.type, TSO.InnerConnection))

                for node_cp in value:
                    g_ld.add((INST[inner_connection], TSO.connectsSystemThrough, INST[node_cp]))
                    g_ld.add((INST[node_cp], TSO.connectsSystemAt, INST[inner_connection]))

                inner_edge_dict[key] = [value, inner_connection]

    return g_ld, outer_edge_dict, inner_edge_dict


def convert_functionalconcepts_to_tso(g_ld, args, enriched_graph, fc_json, state_dict, outer_edge_dict, inner_edge_dict, hierarchie_dict, serves_dict, INST, TSO, RDF, RDFS):
    # Anlegen der funktionalen Konzepte (Input benötigt)
    # TSO-Klassen: Matter (und Subklassen), Energy (und Subklassen), Data (und Subklassen)
    # TSO-OP: hasOutput, outputOf, hasInput, inputOf, hasInnerExchange, innerExchangeOf, supplies (und Subbeziehungen), suppliedBy (und Subbeziehungen), exchange (und Subbeziehungen)
    # TSO-OP: transmitsFrom, hasTransmissionFrom, transmitsThrough, hasTransmissionThrough, transmitsTo, hasTransmissionTo

    terminal_set = ('IfcSpaceHeater', 'IfcSanitaryTerminal', 'IfcWasteTerminal', 'IfcAirTerminal', 'IfcAudioVisualAppliance', 'IfcCommunicationsAppliance',
                    'IfcElectricAppliance', 'IfcFireSuppressionTerminal', 'IfcLamp', 'IfcLightFixture', 'IfcMedialDevice', 'IfcOutlet', 'IfcStackTerminal')
    medium_dict = dict()
    for categorie, value in fc_json.items():
        # Anlegen von Materie, Energie und Daten
        if categorie == 'MED':
            for med in value:
                # Anlegen von Materie, Energie und Daten
                if len(med['ID']) > 0:
                    flow_uuid = med['ID']
                else:
                    flow_uuid = str(uuid.uuid4())

                if med['Classification'] == 'Matter':
                    g_ld.add((INST[flow_uuid], RDF.type, TSO.Matter))
                elif med['Classification'] == 'Fluid':
                    g_ld.add((INST[flow_uuid], RDF.type, TSO.Fluid))
                elif med['Classification'] == 'Liquid':
                    g_ld.add((INST[flow_uuid], RDF.type, TSO.Liquid))
                elif med['Classification'] == 'Gas':
                    g_ld.add((INST[flow_uuid], RDF.type, TSO.Gas))
                elif med['Classification'] == 'Solid':
                    g_ld.add((INST[flow_uuid], RDF.type, TSO.Solid))
                elif med['Classification'] == 'Energy':
                    g_ld.add((INST[flow_uuid], RDF.type, TSO.Energy))
                elif med['Classification'] == 'ThermalEnergy':
                    g_ld.add((INST[flow_uuid], RDF.type, TSO.ThermalEnergy))
                elif med['Classification'] == 'ElectricalEnergy':
                    g_ld.add((INST[flow_uuid], RDF.type, TSO.ElectricalEnergy))
                elif med['Classification'] == 'MechanicalEnergy':
                    g_ld.add((INST[flow_uuid], RDF.type, TSO.MechanicalEnergy))
                elif med['Classification'] == 'Data':
                    g_ld.add((INST[flow_uuid], RDF.type, TSO.Data))

                g_ld.add((INST[flow_uuid], RDFS.label, Literal(med['Label'])))
                medium_dict[flow_uuid] = med['Classification']

        elif categorie == 'GivenState':
            edge_set = set()
            undirected_graph = enriched_graph.to_undirected()
            total_nodes = set()
            conn_point_to_set = set()
            conn_point_from_set = set()
            for flow in value['Flow']:
                search_nodes = set()
                search_edges = dfs_undirected(flow, undirected_graph)
                edge_set.update(search_edges)

                flow_uuid = flow['ID']
                flow_medium = medium_dict[flow_uuid]

                for edge in search_edges:
                    # Knoten in Liste sortieren
                    if edge[0] not in search_nodes:
                        search_nodes.add(edge[0])
                        total_nodes.add(edge[0])

                    if edge[1] not in search_nodes:
                        search_nodes.add(edge[1])
                        total_nodes.add(edge[1])

                    # Output
                    g_ld.add((INST[state_dict[edge[0]]], TSO.hasOutput, INST[flow_uuid]))
                    g_ld.add((INST[flow_uuid], TSO.outputOf, INST[state_dict[edge[0]]]))

                    # Input
                    g_ld.add((INST[state_dict[edge[1]]], TSO.hasInput, INST[flow_uuid]))
                    g_ld.add((INST[flow_uuid], TSO.inputOf, INST[state_dict[edge[1]]]))

                    # Inner Exchange
                    g_ld.add((INST[state_dict[edge[0]]], TSO.hasInnerExchange, INST[flow_uuid]))
                    g_ld.add((INST[flow_uuid], TSO.innerExchangeOf, INST[state_dict[edge[0]]]))

                    g_ld.add((INST[state_dict[edge[1]]], TSO.hasInnerExchange, INST[flow_uuid]))
                    g_ld.add((INST[flow_uuid], TSO.innerExchangeOf, INST[state_dict[edge[1]]]))

                    # Verknüpfung von Zuständen über supplies/suppliedBy
                    if flow_medium == 'Matter':
                        g_ld.add((INST[state_dict[edge[0]]], TSO.suppliesMatter, INST[state_dict[edge[1]]]))
                        g_ld.add((INST[state_dict[edge[1]]], TSO.matterSuppliedBy, INST[state_dict[edge[0]]]))
                    elif flow_medium == 'Fluid':
                        g_ld.add((INST[state_dict[edge[0]]], TSO.suppliesFluid, INST[state_dict[edge[1]]]))
                        g_ld.add((INST[state_dict[edge[1]]], TSO.fluidSuppliedBy, INST[state_dict[edge[0]]]))
                    elif flow_medium == 'Liquid':
                        g_ld.add((INST[state_dict[edge[0]]], TSO.suppliesLiquid, INST[state_dict[edge[1]]]))
                        g_ld.add((INST[state_dict[edge[1]]], TSO.liquidSuppliedBy, INST[state_dict[edge[0]]]))
                    elif flow_medium == 'Gas':
                        g_ld.add((INST[state_dict[edge[0]]], TSO.suppliesGas, INST[state_dict[edge[1]]]))
                        g_ld.add((INST[state_dict[edge[1]]], TSO.gasSuppliedBy, INST[state_dict[edge[0]]]))
                    elif flow_medium == 'Solid':
                        g_ld.add((INST[state_dict[edge[0]]], TSO.suppliesSolid, INST[state_dict[edge[1]]]))
                        g_ld.add((INST[state_dict[edge[1]]], TSO.solidSuppliedBy, INST[state_dict[edge[0]]]))
                    elif flow_medium == 'Energy':
                        g_ld.add((INST[state_dict[edge[0]]], TSO.suppliesEnergy, INST[state_dict[edge[1]]]))
                        g_ld.add((INST[state_dict[edge[1]]], TSO.energySuppliedBy, INST[state_dict[edge[0]]]))
                    elif flow_medium == 'ThermalEnergy':
                        g_ld.add((INST[state_dict[edge[0]]], TSO.suppliesThermalEnergy, INST[state_dict[edge[1]]]))
                        g_ld.add((INST[state_dict[edge[1]]], TSO.thermalEnergySuppliedBy, INST[state_dict[edge[0]]]))
                    elif flow_medium == 'ElectricalEnergy':
                        g_ld.add((INST[state_dict[edge[0]]], TSO.suppliesElectricalEnergy, INST[state_dict[edge[1]]]))
                        g_ld.add((INST[state_dict[edge[1]]], TSO.electricalEnergySuppliedBy, INST[state_dict[edge[0]]]))
                    elif flow_medium == 'MechanicalEnergy':
                        g_ld.add((INST[state_dict[edge[0]]], TSO.suppliesMechanicalEnergy, INST[state_dict[edge[1]]]))
                        g_ld.add((INST[state_dict[edge[1]]], TSO.mechanicalEnergySuppliedBy, INST[state_dict[edge[0]]]))
                    elif flow_medium == 'Data':
                        g_ld.add((INST[state_dict[edge[0]]], TSO.suppliesData, INST[state_dict[edge[1]]]))
                        g_ld.add((INST[state_dict[edge[1]]], TSO.dataSuppliedBy, INST[state_dict[edge[0]]]))

                    # Verknüpfung mit Verbindungspunkten und äußeren Verbindungen
                    try:
                        conn_point_from = outer_edge_dict[(edge[0], edge[1])][0]
                        conn_point_to = outer_edge_dict[(edge[0], edge[1])][1]
                        connection = outer_edge_dict[(edge[0], edge[1])][2]
                    except KeyError:
                        conn_point_from = outer_edge_dict[(edge[1], edge[0])][1]
                        conn_point_to = outer_edge_dict[(edge[1], edge[0])][0]
                        connection = outer_edge_dict[(edge[1], edge[0])][2]

                    g_ld.add((INST[flow_uuid], TSO.transmitsFrom, INST[quote(conn_point_from)]))
                    g_ld.add((INST[quote(conn_point_from)], TSO.hasTransmissionFrom, INST[flow_uuid]))
                    conn_point_from_set.add(conn_point_from)

                    g_ld.add((INST[flow_uuid], TSO.transmitsTo, INST[quote(conn_point_to)]))
                    g_ld.add((INST[quote(conn_point_to)], TSO.hasTransmissionTo, INST[flow_uuid]))
                    conn_point_to_set.add(conn_point_to)

                    g_ld.add((INST[flow_uuid], TSO.transmitsThrough, INST[connection]))
                    g_ld.add((INST[connection], TSO.hasTransmissionThrough, INST[flow_uuid]))

                # Hierarchische Untergliederung von Zuständen
                for state_hierarchy_node in search_nodes:
                    for uppersystem in flow['UpperState']:
                        g_ld.add((INST[state_dict[uppersystem]], TSO.hasSubState, INST[state_dict[state_hierarchy_node]]))
                        g_ld.add((INST[state_dict[state_hierarchy_node]], TSO.subStateOf, INST[state_dict[uppersystem]]))

                # Verknüpfung mit Verbindungspunkten und inneren Verbindungen
                for node in enriched_graph.nodes(data=True):
                    if node[0] in search_nodes:
                        if node[0] in value['IC']:
                            for ic_value in value['IC'][node[0]]:
                                flow_uuid = ic_value['MED']
                                g_ld.add((INST[flow_uuid], TSO.transmitsThrough, INST[ic_value['InnerConnection']]))
                                g_ld.add((INST[ic_value['InnerConnection']], TSO.hasTransmissionThrough, INST[flow_uuid]))

                                for conn_point_from in ic_value['From']:
                                    g_ld.add((INST[flow_uuid], TSO.transmitsFrom, INST[quote(conn_point_from)]))
                                    g_ld.add((INST[quote(conn_point_from)], TSO.hasTransmissionFrom, INST[flow_uuid]))

                                for conn_point_to in ic_value['To']:
                                    g_ld.add((INST[flow_uuid], TSO.transmitsTo, INST[quote(conn_point_to)]))
                                    g_ld.add((INST[quote(conn_point_to)], TSO.hasTransmissionTo, INST[flow_uuid]))

                        else:
                            if node[0] not in inner_edge_dict:
                                continue
                            for inner_conn in inner_edge_dict[node[0]]:
                                conn_points = inner_conn[0]
                                connection = inner_conn[1]

                                g_ld.add((INST[flow_uuid], TSO.transmitsThrough, INST[connection]))
                                g_ld.add((INST[connection], TSO.hasTransmissionThrough, INST[flow_uuid]))

                                for conn_point in conn_points:
                                    if conn_point in conn_point_to_set:
                                        g_ld.add((INST[flow_uuid], TSO.transmitsFrom, INST[quote(conn_point)]))
                                        g_ld.add((INST[quote(conn_point)], TSO.hasTransmissionFrom, INST[flow_uuid]))
                                    elif conn_point in conn_point_from_set:
                                        g_ld.add((INST[flow_uuid], TSO.transmitsTo, INST[quote(conn_point)]))
                                        g_ld.add((INST[quote(conn_point)], TSO.hasTransmissionTo, INST[flow_uuid]))

            for node in enriched_graph.nodes(data=True):
                # Add source and sink relationships
                if node[0] in value['SourceAndSink']:
                    for rel in value['SourceAndSink'][node[0]]:
                        if rel[0] == 'Sink':
                            for sink_system in rel[1]:
                                g_ld.add((INST[state_dict[node[0]]], TSO.sinkOf, INST[state_dict[sink_system]]))
                                g_ld.add((INST[state_dict[sink_system]], TSO.hasSink, INST[state_dict[node[0]]]))
                        elif rel[0] == 'Source':
                            for source_system in rel[1]:
                                g_ld.add((INST[state_dict[node[0]]], TSO.sourceOf, INST[state_dict[source_system]]))
                                g_ld.add((INST[state_dict[source_system]], TSO.hasSource, INST[state_dict[node[0]]]))
                else:
                    if node[1]['ifc_class'] in terminal_set:
                        nodes_fs_list = node[1]['functional_systems']
                        nodes_ts_list = node[1]['technical_systems']
                        ts_supersystem = None
                        fs_supersystem = None

                        for fs in nodes_fs_list:
                            if len(hierarchie_dict['FS'][fs]['TS']) == 0:
                                fs_supersystem = fs

                        for ts in nodes_ts_list:
                            if len(hierarchie_dict['TS'][ts]['TS']) == 0:
                                ts_supersystem = ts

                        if ts_supersystem:
                            if node[1]['ifc_class'] == 'IfcSpaceHeater':
                                g_ld.add((INST[state_dict[node[0]]], TSO.sinkOf, INST[state_dict[ts_supersystem]]))
                                g_ld.add((INST[state_dict[ts_supersystem]], TSO.hasSink, INST[state_dict[node[0]]]))
                            elif node[1]['ifc_class'] == 'IfcSanitaryTerminal':
                                if hierarchie_dict['TS'][ts_supersystem]['Classification'] == 'Supply System':
                                    g_ld.add((INST[state_dict[node[0]]], TSO.sinkOf, INST[state_dict[ts_supersystem]]))
                                    g_ld.add((INST[state_dict[ts_supersystem]], TSO.hasSink, INST[state_dict[node[0]]]))
                                elif hierarchie_dict['TS'][ts_supersystem]['Classification'] == 'Return System':
                                    g_ld.add((INST[state_dict[node[0]]], TSO.sourceOf, INST[state_dict[ts_supersystem]]))
                                    g_ld.add((INST[state_dict[ts_supersystem]], TSO.hasSource, INST[state_dict[node[0]]]))
                            elif node[1]['ifc_class'] == 'IfcWasteTerminal':
                                g_ld.add((INST[state_dict[node[0]]], TSO.sourceOf, INST[state_dict[ts_supersystem]]))
                                g_ld.add((INST[state_dict[ts_supersystem]], TSO.hasSource, INST[state_dict[node[0]]]))
                            elif node[1]['ifc_class'] == 'IfcAirTerminal':
                                if hierarchie_dict['TS'][ts_supersystem]['Classification'] == 'Supply System':
                                    g_ld.add((INST[state_dict[node[0]]], TSO.sinkOf, INST[state_dict[ts_supersystem]]))
                                    g_ld.add((INST[state_dict[ts_supersystem]], TSO.hasSink, INST[state_dict[node[0]]]))

                                elif hierarchie_dict['TS'][ts_supersystem]['Classification'] == 'Return System':
                                    g_ld.add((INST[state_dict[node[0]]], TSO.sourceOf, INST[state_dict[ts_supersystem]]))
                                    g_ld.add((INST[state_dict[ts_supersystem]], TSO.hasSource, INST[state_dict[node[0]]]))

                        if fs_supersystem:
                            if node[1]['ifc_class'] == 'IfcSpaceHeater':
                                g_ld.add((INST[state_dict[node[0]]], TSO.sinkOf, INST[state_dict[fs_supersystem]]))
                                g_ld.add((INST[state_dict[fs_supersystem]], TSO.hasSink, INST[state_dict[node[0]]]))
                            elif node[1]['ifc_class'] == 'IfcSanitaryTerminal':
                                if hierarchie_dict['TS'][ts_supersystem]['Classification'] == 'Supply System':
                                    g_ld.add((INST[state_dict[node[0]]], TSO.sinkOf, INST[state_dict[fs_supersystem]]))
                                    g_ld.add((INST[state_dict[fs_supersystem]], TSO.hasSink, INST[state_dict[node[0]]]))
                            elif node[1]['ifc_class'] == 'IfcAirTerminal':
                                if hierarchie_dict['TS'][ts_supersystem]['Classification'] == 'Supply System':
                                    g_ld.add((INST[state_dict[node[0]]], TSO.sinkOf, INST[state_dict[fs_supersystem]]))
                                    g_ld.add((INST[state_dict[fs_supersystem]], TSO.hasSink, INST[state_dict[node[0]]]))

                # Add serves relationships
                if node[0] in value['Serves']:
                    for serves_value in value['Serves'][node[0]]:
                        if len(serves_value[2]) > 1:
                            space_key = quote(serves_value[2])
                        else:
                            if node[0] in serves_dict:
                                space_key = quote(serves_dict[node[0]])
                            else:
                                continue
                        if serves_value[0] == 'Serves':
                            if serves_value[1] == 'Matter':
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesMatterToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'Solid':
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesSolidToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'Fluid':
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesFluidToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'Liquid':
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesLiquidToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'Gas':
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesGasToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'Energy':
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesEnergyToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'ThermalEnergy':
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesThermalEnergyToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'ElectricalEnergy':
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesElectricalEnergyToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'MechanicalEnergy':
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesMechanicalEnergyToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'LightEnergy':
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesLightEnergyToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'SoundEnergy':
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesSoundEnergyToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'Data':
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesDataToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                        elif serves_value[0] == 'ServedBy':
                            if serves_value[1] == 'Matter':
                                g_ld.add((INST[space_key], TSO.servesMatterToSystem, INST[state_dict[node[0]]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node[0]]]))
                            elif serves_value[1] == 'Solid':
                                g_ld.add((INST[space_key], TSO.servesSolidToSystem, INST[state_dict[node[0]]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node[0]]]))
                            elif serves_value[1] == 'Fluid':
                                g_ld.add((INST[space_key], TSO.servesFluidToSystem, INST[state_dict[node[0]]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node[0]]]))
                            elif serves_value[1] == 'Liquid':
                                g_ld.add((INST[space_key], TSO.servesLiquidToSystem, INST[state_dict[node[0]]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node[0]]]))
                            elif serves_value[1] == 'Gas':
                                g_ld.add((INST[space_key], TSO.servesGasToSystem, INST[state_dict[node[0]]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node[0]]]))
                            elif serves_value[1] == 'Energy':
                                g_ld.add((INST[space_key], TSO.servesEnergyToSystem, INST[state_dict[node[0]]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node[0]]]))
                            elif serves_value[1] == 'ThermalEnergy':
                                g_ld.add((INST[space_key], TSO.servesThermalEnergyToSystem, INST[state_dict[node[0]]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node[0]]]))
                            elif serves_value[1] == 'ElectricalEnergy':
                                g_ld.add((INST[space_key], TSO.servesElectricalEnergyToSystem, INST[state_dict[node[0]]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node[0]]]))
                            elif serves_value[1] == 'MechanicalEnergy':
                                g_ld.add((INST[space_key], TSO.servesMechanicalEnergyToSystem, INST[state_dict[node[0]]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node[0]]]))
                            elif serves_value[1] == 'LightEnergy':
                                g_ld.add((INST[space_key], TSO.servesLightEnergyToSystem, INST[state_dict[node[0]]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node[0]]]))
                            elif serves_value[1] == 'SoundEnergy':
                                g_ld.add((INST[space_key], TSO.servesSoundEnergyToSystem, INST[state_dict[node[0]]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node[0]]]))
                            elif serves_value[1] == 'Data':
                                g_ld.add((INST[space_key], TSO.servesDataToSystem, INST[state_dict[node[0]]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node[0]]]))
                else:
                    if node[0] in serves_dict:
                        for space_key in serves_dict[node[0]]:
                            space_key = quote(space_key)
                            if node[1]['ifc_class'] in terminal_set:
                                if node[1]['ifc_class'] == 'IfcSpaceHeater':
                                    g_ld.add((INST[state_dict[node[0]]], TSO.servesThermalEnergyToZone, INST[space_key]))
                                    g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                                elif node[1]['ifc_class'] == 'IfcWasteTerminal':
                                    g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node[0]]]))
                                    g_ld.add((INST[space_key], TSO.servesLiquidToSystem, INST[state_dict[node[0]]]))
                                elif node[1]['ifc_class'] == 'IfcSanitaryTerminal':
                                    g_ld.add((INST[state_dict[node[0]]], TSO.servesLiquidToZone, INST[space_key]))
                                    g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                                elif node[1]['ifc_class'] == 'IfcAirTerminal':
                                    nodes_ts_list = enriched_graph.nodes[node[0]]['technical_systems']
                                    for ts in nodes_ts_list:
                                        if hierarchie_dict['TS'][ts]['Classification'] == 'Supply System':
                                            g_ld.add((INST[state_dict[node[0]]], TSO.servesGasToZone, INST[space_key]))
                                            g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                                            break

                                    for ts in nodes_ts_list:
                                        if hierarchie_dict['TS'][ts]['Classification'] == 'Return System':
                                            g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node[0]]]))
                                            g_ld.add((INST[space_key], TSO.servesGasToSystem, INST[state_dict[node[0]]]))
                                            break

                                elif node[1]['ifc_class'] == 'IfcFireSuppressionTerminal':
                                    g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                                    g_ld.add((INST[state_dict[node[0]]], TSO.servesLiquid, INST[space_key]))

                                elif node[1]['ifc_class'] == 'IfcOutlet':
                                    g_ld.add((INST[state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                                    g_ld.add((INST[state_dict[node[0]]], TSO.servesElectricalEnergyToZone, INST[space_key]))

                for node_idx, serves_value in value['Serves'].items():
                        space_key = quote(serves_value[2])
                        if node_idx not in state_dict:
                            continue

                        if serves_value[0] == 'Serves':
                            if serves_value[1] == 'Matter':
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesMatterToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'Solid':
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesSolidToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'Fluid':
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesFluidToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'Liquid':
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesLiquidToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'Gas':
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesGasToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'Energy':
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesEnergyToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'ThermalEnergy':
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesThermalEnergyToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'ElectricalEnergy':
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesElectricalEnergyToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'MechanicalEnergy':
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesMechanicalEnergyToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'LightEnergy':
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesLightEnergyToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'SoundEnergy':
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesSoundEnergyToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesZone, INST[space_key]))
                            elif serves_value[1] == 'Data':
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesDataToZone, INST[space_key]))
                                g_ld.add((INST[state_dict[node_idx]], TSO.servesZone, INST[space_key]))
                        elif serves_value[0] == 'ServedBy':
                            if serves_value[1] == 'Matter':
                                g_ld.add((INST[space_key], TSO.servesMatterToSystem, INST[state_dict[node_idx]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node_idx]]))
                            elif serves_value[1] == 'Solid':
                                g_ld.add((INST[space_key], TSO.servesSolidToSystem, INST[state_dict[node_idx]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node_idx]]))
                            elif serves_value[1] == 'Fluid':
                                g_ld.add((INST[space_key], TSO.servesFluidToSystem, INST[state_dict[node_idx]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node_idx]]))
                            elif serves_value[1] == 'Liquid':
                                g_ld.add((INST[space_key], TSO.servesLiquidToSystem, INST[state_dict[node_idx]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node_idx]]))
                            elif serves_value[1] == 'Gas':
                                g_ld.add((INST[space_key], TSO.servesGasToSystem, INST[state_dict[node_idx]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node_idx]]))
                            elif serves_value[1] == 'Energy':
                                g_ld.add((INST[space_key], TSO.servesEnergyToSystem, INST[state_dict[node_idx]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node_idx]]))
                            elif serves_value[1] == 'ThermalEnergy':
                                g_ld.add((INST[space_key], TSO.servesThermalEnergyToSystem, INST[state_dict[node_idx]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node_idx]]))
                            elif serves_value[1] == 'ElectricalEnergy':
                                g_ld.add((INST[space_key], TSO.servesElectricalEnergyToSystem, INST[state_dict[node_idx]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node_idx]]))
                            elif serves_value[1] == 'MechanicalEnergy':
                                g_ld.add((INST[space_key], TSO.servesMechanicalEnergyToSystem, INST[state_dict[node_idx]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node_idx]]))
                            elif serves_value[1] == 'LightEnergy':
                                g_ld.add((INST[space_key], TSO.servesLightEnergyToSystem, INST[state_dict[node_idx]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node_idx]]))
                            elif serves_value[1] == 'SoundEnergy':
                                g_ld.add((INST[space_key], TSO.servesSoundEnergyToSystem, INST[state_dict[node_idx]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node_idx]]))
                            elif serves_value[1] == 'Data':
                                g_ld.add((INST[space_key], TSO.servesDataToSystem, INST[state_dict[node_idx]]))
                                g_ld.add((INST[space_key], TSO.servesSystem, INST[state_dict[node_idx]]))

        elif categorie == 'NewStates':
            for new_state_value in value:
                new_state_dict = dict()
                edge_set = set()
                undirected_graph = enriched_graph.to_undirected()
                total_nodes = set()
                conn_point_to_set = set()
                conn_point_from_set = set()
                for system in new_state_value['Systems']:
                    state_uuid = str(uuid.uuid4())
                    new_state_dict[system] = state_uuid
                    g_ld.add((INST[state_uuid], RDF.type, TSO.State))
                    g_ld.add((INST[system], TSO.hasState, INST[state_uuid]))
                    g_ld.add((INST[state_uuid], TSO.stateOf, INST[system]))

                for system_hierarchy in new_state_value['Systemhierarchy']:
                    g_ld.add((INST[new_state_dict[system_hierarchy[0]]], TSO.hasSubState, INST[new_state_dict[system_hierarchy[1]]]))
                    g_ld.add((INST[new_state_dict[system_hierarchy[1]]], TSO.subStateOf, INST[new_state_dict[system_hierarchy[0]]]))

                for flow in new_state_value['Flow']:
                    search_nodes = set()
                    search_edges = dfs_undirected(flow, undirected_graph)
                    edge_set.update(search_edges)

                    flow_uuid = flow['ID']
                    flow_medium = medium_dict[flow_uuid]

                    for edge in search_edges:
                        # Knoten in Liste sortieren
                        if edge[0] not in search_nodes:
                            search_nodes.add(edge[0])
                            total_nodes.add(edge[0])

                            if edge[0] not in new_state_dict:
                                state_uuid = str(uuid.uuid4())
                                new_state_dict[edge[0]] = state_uuid
                            else:
                                state_uuid = new_state_dict[edge[0]]
                            g_ld.add((INST[state_uuid], RDF.type, TSO.State))
                            g_ld.add((INST[quote(edge[0])], TSO.hasState, INST[state_uuid]))
                            g_ld.add((INST[state_uuid], TSO.stateOf, INST[quote(edge[0])]))

                        if edge[1] not in search_nodes:
                            search_nodes.add(edge[1])
                            total_nodes.add(edge[1])

                            if edge[1] not in new_state_dict:
                                state_uuid = str(uuid.uuid4())
                                new_state_dict[edge[1]] = state_uuid
                            else:
                                state_uuid = new_state_dict[edge[1]]
                            g_ld.add((INST[state_uuid], RDF.type, TSO.State))
                            g_ld.add((INST[quote(edge[1])], TSO.hasState, INST[state_uuid]))
                            g_ld.add((INST[state_uuid], TSO.stateOf, INST[quote(edge[1])]))

                        # Output
                        g_ld.add((INST[new_state_dict[edge[0]]], TSO.hasOutput, INST[flow_uuid]))
                        g_ld.add((INST[flow_uuid], TSO.outputOf, INST[new_state_dict[edge[0]]]))

                        # Input
                        g_ld.add((INST[new_state_dict[edge[1]]], TSO.hasInput, INST[flow_uuid]))
                        g_ld.add((INST[flow_uuid], TSO.inputOf, INST[new_state_dict[edge[1]]]))

                        # Inner Exchange
                        g_ld.add((INST[new_state_dict[edge[0]]], TSO.hasInnerExchange, INST[flow_uuid]))
                        g_ld.add((INST[flow_uuid], TSO.innerExchangeOf, INST[new_state_dict[edge[0]]]))

                        g_ld.add((INST[new_state_dict[edge[1]]], TSO.hasInnerExchange, INST[flow_uuid]))
                        g_ld.add((INST[flow_uuid], TSO.innerExchangeOf, INST[new_state_dict[edge[1]]]))

                        # Verknüpfung von Zuständen über supplies/suppliedBy
                        if flow_medium == 'Matter':
                            g_ld.add((INST[new_state_dict[edge[0]]], TSO.suppliesMatter, INST[new_state_dict[edge[1]]]))
                            g_ld.add((INST[new_state_dict[edge[1]]], TSO.matterSuppliedBy, INST[new_state_dict[edge[0]]]))
                        elif flow_medium == 'Fluid':
                            g_ld.add((INST[new_state_dict[edge[0]]], TSO.suppliesFluid, INST[new_state_dict[edge[1]]]))
                            g_ld.add((INST[new_state_dict[edge[1]]], TSO.fluidSuppliedBy, INST[new_state_dict[edge[0]]]))
                        elif flow_medium == 'Liquid':
                            g_ld.add((INST[new_state_dict[edge[0]]], TSO.suppliesLiquid, INST[new_state_dict[edge[1]]]))
                            g_ld.add((INST[new_state_dict[edge[1]]], TSO.liquidSuppliedBy, INST[new_state_dict[edge[0]]]))
                        elif flow_medium == 'Gas':
                            g_ld.add((INST[new_state_dict[edge[0]]], TSO.suppliesGas, INST[new_state_dict[edge[1]]]))
                            g_ld.add((INST[new_state_dict[edge[1]]], TSO.gasSuppliedBy, INST[new_state_dict[edge[0]]]))
                        elif flow_medium == 'Solid':
                            g_ld.add((INST[new_state_dict[edge[0]]], TSO.suppliesSolid, INST[new_state_dict[edge[1]]]))
                            g_ld.add((INST[new_state_dict[edge[1]]], TSO.solidSuppliedBy, INST[new_state_dict[edge[0]]]))
                        elif flow_medium == 'Energy':
                            g_ld.add((INST[new_state_dict[edge[0]]], TSO.suppliesEnergy, INST[new_state_dict[edge[1]]]))
                            g_ld.add((INST[new_state_dict[edge[1]]], TSO.energySuppliedBy, INST[new_state_dict[edge[0]]]))
                        elif flow_medium == 'ThermalEnergy':
                            g_ld.add((INST[new_state_dict[edge[0]]], TSO.suppliesThermalEnergy, INST[new_state_dict[edge[1]]]))
                            g_ld.add((INST[new_state_dict[edge[1]]], TSO.thermalEnergySuppliedBy, INST[new_state_dict[edge[0]]]))
                        elif flow_medium == 'ElectricalEnergy':
                            g_ld.add((INST[new_state_dict[edge[0]]], TSO.suppliesElectricalEnergy, INST[new_state_dict[edge[1]]]))
                            g_ld.add((INST[new_state_dict[edge[1]]], TSO.electricalEnergySuppliedBy, INST[new_state_dict[edge[0]]]))
                        elif flow_medium == 'MechanicalEnergy':
                            g_ld.add((INST[new_state_dict[edge[0]]], TSO.suppliesMechanicalEnergy, INST[new_state_dict[edge[1]]]))
                            g_ld.add((INST[new_state_dict[edge[1]]], TSO.mechanicalEnergySuppliedBy, INST[new_state_dict[edge[0]]]))
                        elif flow_medium == 'Data':
                            g_ld.add((INST[new_state_dict[edge[0]]], TSO.suppliesData, INST[new_state_dict[edge[1]]]))
                            g_ld.add((INST[new_state_dict[edge[1]]], TSO.dataSuppliedBy, INST[new_state_dict[edge[0]]]))

                        # Verknüpfung mit Verbindungspunkten und äußeren Verbindungen
                        try:
                            conn_point_from = outer_edge_dict[(edge[0], edge[1])][0]
                            conn_point_to = outer_edge_dict[(edge[0], edge[1])][1]
                            connection = outer_edge_dict[(edge[0], edge[1])][2]
                        except KeyError:
                            conn_point_from = outer_edge_dict[(edge[1], edge[0])][1]
                            conn_point_to = outer_edge_dict[(edge[1], edge[0])][0]
                            connection = outer_edge_dict[(edge[1], edge[0])][2]

                        g_ld.add((INST[flow_uuid], TSO.transmitsFrom, INST[quote(conn_point_from)]))
                        g_ld.add((INST[quote(conn_point_from)], TSO.hasTransmissionFrom, INST[flow_uuid]))
                        conn_point_from_set.add(conn_point_from)

                        g_ld.add((INST[flow_uuid], TSO.transmitsTo, INST[quote(conn_point_to)]))
                        g_ld.add((INST[quote(conn_point_to)], TSO.hasTransmissionTo, INST[flow_uuid]))
                        conn_point_to_set.add(conn_point_to)

                        g_ld.add((INST[flow_uuid], TSO.transmitsThrough, INST[connection]))
                        g_ld.add((INST[connection], TSO.hasTransmissionThrough, INST[flow_uuid]))

                    # Hierarchische Untergliederung von Zuständen
                    for state_hierarchy_node in search_nodes:
                        for uppersystem in flow['UpperState']:
                            g_ld.add((INST[new_state_dict[uppersystem]], TSO.hasSubState, INST[new_state_dict[state_hierarchy_node]]))
                            g_ld.add((INST[new_state_dict[state_hierarchy_node]], TSO.subStateOf, INST[new_state_dict[uppersystem]]))

                    # Verknüpfung mit Verbindungspunkten und inneren Verbindungen
                    for node in enriched_graph.nodes(data=True):
                        if node[0] in search_nodes:
                            if node[0] in new_state_value['IC']:
                                for ic_value in new_state_value['IC'][node[0]]:
                                    flow_uuid = ic_value['MED']
                                    g_ld.add((INST[flow_uuid], TSO.transmitsThrough, INST[ic_value['InnerConnection']]))
                                    g_ld.add((INST[ic_value['InnerConnection']], TSO.hasTransmissionThrough, INST[flow_uuid]))

                                    for conn_point_from in ic_value['From']:
                                        g_ld.add((INST[flow_uuid], TSO.transmitsFrom, INST[quote(conn_point_from)]))
                                        g_ld.add((INST[quote(conn_point_from)], TSO.hasTransmissionFrom, INST[flow_uuid]))

                                    for conn_point_to in ic_value['To']:
                                        g_ld.add((INST[flow_uuid], TSO.transmitsTo, INST[quote(conn_point_to)]))
                                        g_ld.add((INST[quote(conn_point_to)], TSO.hasTransmissionTo, INST[flow_uuid]))

                            else:
                                if node[0] not in inner_edge_dict:
                                    continue
                                for inner_conn in inner_edge_dict[node[0]]:
                                    conn_points = inner_conn[0]
                                    connection = inner_conn[1]

                                    g_ld.add((INST[flow_uuid], TSO.transmitsThrough, INST[connection]))
                                    g_ld.add((INST[connection], TSO.hasTransmissionThrough, INST[flow_uuid]))

                                    for conn_point in conn_points:
                                        if conn_point in conn_point_to_set:
                                            g_ld.add((INST[flow_uuid], TSO.transmitsFrom, INST[quote(conn_point)]))
                                            g_ld.add((INST[quote(conn_point)], TSO.hasTransmissionFrom, INST[flow_uuid]))
                                        elif conn_point in conn_point_from_set:
                                            g_ld.add((INST[flow_uuid], TSO.transmitsTo, INST[quote(conn_point)]))
                                            g_ld.add((INST[quote(conn_point)], TSO.hasTransmissionTo, INST[flow_uuid]))

                for node in enriched_graph.nodes(data=True):
                    # Add source and sink relationships
                    if node[0] in new_state_value['SourceAndSink']:
                        for rel in new_state_value['SourceAndSink'][node[0]]:
                            if rel[0] == 'Sink':
                                for sink_system in rel[1]:
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.sinkOf, INST[new_state_dict[sink_system]]))
                                    g_ld.add((INST[new_state_dict[sink_system]], TSO.hasSink, INST[new_state_dict[node[0]]]))
                            elif rel[0] == 'Source':
                                for source_system in rel[1]:
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.sourceOf, INST[new_state_dict[source_system]]))
                                    g_ld.add((INST[new_state_dict[source_system]], TSO.hasSource, INST[new_state_dict[node[0]]]))
                    else:
                        if node[0] not in new_state_dict.keys():
                            continue
                        if node[1]['ifc_class'] in terminal_set:
                            nodes_fs_list = node[1]['functional_systems']
                            nodes_ts_list = node[1]['technical_systems']
                            ts_supersystem = None
                            fs_supersystem = None

                            for fs in nodes_fs_list:
                                if len(hierarchie_dict['FS'][fs]['TS']) == 0:
                                    fs_supersystem = fs

                            for ts in nodes_ts_list:
                                if len(hierarchie_dict['TS'][ts]['TS']) == 0:
                                    ts_supersystem = ts

                            if ts_supersystem:
                                if ts_supersystem not in new_state_dict.keys():
                                    continue
                                if node[1]['ifc_class'] == 'IfcSpaceHeater':
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.sinkOf, INST[new_state_dict[ts_supersystem]]))
                                    g_ld.add((INST[new_state_dict[ts_supersystem]], TSO.hasSink, INST[new_state_dict[node[0]]]))
                                elif node[1]['ifc_class'] == 'IfcSanitaryTerminal':
                                    if hierarchie_dict['TS'][ts_supersystem]['Classification'] == 'Supply System':
                                        g_ld.add((INST[new_state_dict[node[0]]], TSO.sinkOf, INST[new_state_dict[ts_supersystem]]))
                                        g_ld.add((INST[new_state_dict[ts_supersystem]], TSO.hasSink, INST[new_state_dict[node[0]]]))
                                    elif hierarchie_dict['TS'][ts_supersystem]['Classification'] == 'Return System':
                                        g_ld.add((INST[new_state_dict[node[0]]], TSO.sourceOf, INST[new_state_dict[ts_supersystem]]))
                                        g_ld.add((INST[new_state_dict[ts_supersystem]], TSO.hasSource, INST[new_state_dict[node[0]]]))
                                elif node[1]['ifc_class'] == 'IfcWasteTerminal':
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.sourceOf, INST[new_state_dict[ts_supersystem]]))
                                    g_ld.add((INST[new_state_dict[ts_supersystem]], TSO.hasSource, INST[new_state_dict[node[0]]]))
                                elif node[1]['ifc_class'] == 'IfcAirTerminal':
                                    if hierarchie_dict['TS'][ts_supersystem]['Classification'] == 'Supply System':
                                        g_ld.add((INST[new_state_dict[node[0]]], TSO.sinkOf, INST[new_state_dict[ts_supersystem]]))
                                        g_ld.add((INST[new_state_dict[ts_supersystem]], TSO.hasSink, INST[new_state_dict[node[0]]]))

                                    elif hierarchie_dict['TS'][ts_supersystem]['Classification'] == 'Return System':
                                        g_ld.add((INST[new_state_dict[node[0]]], TSO.sourceOf, INST[new_state_dict[ts_supersystem]]))
                                        g_ld.add((INST[new_state_dict[ts_supersystem]], TSO.hasSource, INST[new_state_dict[node[0]]]))

                            if fs_supersystem:
                                if fs_supersystem not in new_state_dict.keys():
                                    continue
                                if node[1]['ifc_class'] == 'IfcSpaceHeater':
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.sinkOf, INST[new_state_dict[fs_supersystem]]))
                                    g_ld.add((INST[new_state_dict[fs_supersystem]], TSO.hasSink, INST[new_state_dict[node[0]]]))
                                elif node[1]['ifc_class'] == 'IfcSanitaryTerminal':
                                    if hierarchie_dict['TS'][ts_supersystem]['Classification'] == 'Supply System':
                                        g_ld.add((INST[new_state_dict[node[0]]], TSO.sinkOf, INST[new_state_dict[fs_supersystem]]))
                                        g_ld.add((INST[new_state_dict[fs_supersystem]], TSO.hasSink, INST[new_state_dict[node[0]]]))
                                elif node[1]['ifc_class'] == 'IfcAirTerminal':
                                    if hierarchie_dict['TS'][ts_supersystem]['Classification'] == 'Supply System':
                                        g_ld.add((INST[new_state_dict[node[0]]], TSO.sinkOf, INST[new_state_dict[fs_supersystem]]))
                                        g_ld.add((INST[new_state_dict[fs_supersystem]], TSO.hasSink, INST[new_state_dict[node[0]]]))

                    # Add serves relationships
                    if node[0] in new_state_value['Serves']:
                        for serves_value in new_state_value['Serves'][node[0]]:
                            if len(serves_value[2]) > 1:
                                space_key = quote(serves_value[2])
                            else:
                                if node[0] in serves_dict:
                                    space_key = quote(serves_dict[node[0]])
                                else:
                                    continue
                            if serves_value[0] == 'Serves':
                                if serves_value[1] == 'Matter':
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesMatterToZone, INST[space_key]))
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                                elif serves_value[1] == 'Solid':
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesSolidToZone, INST[space_key]))
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                                elif serves_value[1] == 'Fluid':
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesFluidToZone, INST[space_key]))
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                                elif serves_value[1] == 'Liquid':
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesLiquidToZone, INST[space_key]))
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                                elif serves_value[1] == 'Gas':
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesGasToZone, INST[space_key]))
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                                elif serves_value[1] == 'Energy':
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesEnergyToZone, INST[space_key]))
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                                elif serves_value[1] == 'ThermalEnergy':
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesThermalEnergyToZone, INST[space_key]))
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                                elif serves_value[1] == 'ElectricalEnergy':
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesElectricalEnergyToZone, INST[space_key]))
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                                elif serves_value[1] == 'MechanicalEnergy':
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesMechanicalEnergyToZone, INST[space_key]))
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                                elif serves_value[1] == 'LightEnergy':
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesLightEnergyToZone, INST[space_key]))
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                                elif serves_value[1] == 'SoundEnergy':
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesSoundEnergyToZone, INST[space_key]))
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                                elif serves_value[1] == 'Data':
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesDataToZone, INST[space_key]))
                                    g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[space_key]))
                            elif serves_value[0] == 'ServedBy':
                                if serves_value[1] == 'Matter':
                                    g_ld.add((INST[space_key], TSO.servesMatterToSystem, INST[new_state_dict[node[0]]]))
                                    g_ld.add((INST[space_key], TSO.servesSystem, INST[new_state_dict[node[0]]]))
                                elif serves_value[1] == 'Solid':
                                    g_ld.add((INST[space_key], TSO.servesSolidToSystem, INST[new_state_dict[node[0]]]))
                                    g_ld.add((INST[space_key], TSO.servesSystem, INST[new_state_dict[node[0]]]))
                                elif serves_value[1] == 'Fluid':
                                    g_ld.add((INST[space_key], TSO.servesFluidToSystem, INST[new_state_dict[node[0]]]))
                                    g_ld.add((INST[space_key], TSO.servesSystem, INST[new_state_dict[node[0]]]))
                                elif serves_value[1] == 'Liquid':
                                    g_ld.add((INST[space_key], TSO.servesLiquidToSystem, INST[new_state_dict[node[0]]]))
                                    g_ld.add((INST[space_key], TSO.servesSystem, INST[new_state_dict[node[0]]]))
                                elif serves_value[1] == 'Gas':
                                    g_ld.add((INST[space_key], TSO.servesGasToSystem, INST[new_state_dict[node[0]]]))
                                    g_ld.add((INST[space_key], TSO.servesSystem, INST[new_state_dict[node[0]]]))
                                elif serves_value[1] == 'Energy':
                                    g_ld.add((INST[space_key], TSO.servesEnergyToSystem, INST[new_state_dict[node[0]]]))
                                    g_ld.add((INST[space_key], TSO.servesSystem, INST[new_state_dict[node[0]]]))
                                elif serves_value[1] == 'ThermalEnergy':
                                    g_ld.add((INST[space_key], TSO.servesThermalEnergyToSystem, INST[new_state_dict[node[0]]]))
                                    g_ld.add((INST[space_key], TSO.servesSystem, INST[new_state_dict[node[0]]]))
                                elif serves_value[1] == 'ElectricalEnergy':
                                    g_ld.add((INST[space_key], TSO.servesElectricalEnergyToSystem, INST[new_state_dict[node[0]]]))
                                    g_ld.add((INST[space_key], TSO.servesSystem, INST[new_state_dict[node[0]]]))
                                elif serves_value[1] == 'MechanicalEnergy':
                                    g_ld.add((INST[space_key], TSO.servesMechanicalEnergyToSystem, INST[new_state_dict[node[0]]]))
                                    g_ld.add((INST[space_key], TSO.servesSystem, INST[new_state_dict[node[0]]]))
                                elif serves_value[1] == 'LightEnergy':
                                    g_ld.add((INST[space_key], TSO.servesLightEnergyToSystem, INST[new_state_dict[node[0]]]))
                                    g_ld.add((INST[space_key], TSO.servesSystem, INST[new_state_dict[node[0]]]))
                                elif serves_value[1] == 'SoundEnergy':
                                    g_ld.add((INST[space_key], TSO.servesSoundEnergyToSystem, INST[new_state_dict[node[0]]]))
                                    g_ld.add((INST[space_key], TSO.servesSystem, INST[new_state_dict[node[0]]]))
                                elif serves_value[1] == 'Data':
                                    g_ld.add((INST[space_key], TSO.servesDataToSystem, INST[new_state_dict[node[0]]]))
                                    g_ld.add((INST[space_key], TSO.servesSystem, INST[new_state_dict[node[0]]]))
                    else:
                        if node[0] not in new_state_dict.keys():
                            continue
                        if node[0] in serves_dict:
                            for space_key in serves_dict[node[0]]:
                                if node[1]['ifc_class'] in terminal_set:
                                    if node[1]['ifc_class'] == 'IfcSpaceHeater':
                                        g_ld.add((INST[new_state_dict[node[0]]], TSO.servesThermalEnergyToZone, INST[quote(space_key)]))
                                        g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[quote(space_key)]))
                                    elif node[1]['ifc_class'] == 'IfcWasteTerminal':
                                        g_ld.add((INST[quote(space_key)], TSO.servesSystem, INST[new_state_dict[node[0]]]))
                                        g_ld.add((INST[quote(space_key)], TSO.servesLiquidToSystem, INST[new_state_dict[node[0]]]))
                                    elif node[1]['ifc_class'] == 'IfcSanitaryTerminal':
                                        g_ld.add((INST[new_state_dict[node[0]]], TSO.servesLiquidToZone, INST[quote(space_key)]))
                                        g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[quote(space_key)]))
                                    elif node[1]['ifc_class'] == 'IfcAirTerminal':
                                        nodes_ts_list = enriched_graph.nodes[node[0]]['technical_systems']
                                        for ts in nodes_ts_list:
                                            if hierarchie_dict['TS'][ts]['Classification'] == 'Supply System':
                                                g_ld.add((INST[new_state_dict[node[0]]], TSO.servesGasToZone, INST[quote(space_key)]))
                                                g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[quote(space_key)]))
                                                break

                                        for ts in nodes_ts_list:
                                            if hierarchie_dict['TS'][ts]['Classification'] == 'Return System':
                                                g_ld.add((INST[quote(space_key)], TSO.servesSystem, INST[new_state_dict[node[0]]]))
                                                g_ld.add((INST[quote(space_key)], TSO.servesGasToSystem, INST[new_state_dict[node[0]]]))
                                                break

                                    elif node[1]['ifc_class'] == 'IfcFireSuppressionTerminal':
                                        g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[quote(space_key)]))
                                        g_ld.add((INST[new_state_dict[node[0]]], TSO.servesLiquid, INST[quote(space_key)]))

                                    elif node[1]['ifc_class'] == 'IfcOutlet':
                                        g_ld.add((INST[new_state_dict[node[0]]], TSO.servesZone, INST[quote(space_key)]))
                                        g_ld.add((INST[new_state_dict[node[0]]], TSO.servesElectricalEnergyToZone, INST[quote(space_key)]))

    return g_ld


def convert_spatialconcepts_to_tso(g_ld, args, enriched_graph, spatial_dict, INST, TSO, RDF, BOT):
    # Anlegen von räumlichen Konzepten und den Beziehungen zu Systemen
    # TSO-Klassen: Zone
    # TSO-OP: contains, locatedIn, servesZone (und Subbeziehungen), servesSystem (und Subbeziehungen)
    # BOT-Klassen: Site, Building, Storey, Space
    # BOT-OP: hasZone (und Subbeziehungen)
    terminal_set = ('IfcSpaceHeater', 'IfcSanitaryTerminal', 'IfcWasteTerminal', 'IfcAirTerminal', 'IfcAudioVisualAppliance', 'IfcCommunicationsAppliance',
                    'IfcElectricAppliance', 'IfcFireSuppressionTerminal', 'IfcLamp', 'IfcLightFixture', 'IfcMedialDevice', 'IfcOutlet', 'IfcStackTerminal')

    serves_dict = dict()
    if args.add_spatial:
        for site_key, site_value in spatial_dict['IfcSite'].items():
            g_ld.add((INST[quote(site_key)], RDF.type, TSO.Zone))
            g_ld.add((INST[quote(site_key)], RDF.type, BOT.Site))
            try:
                for bld in spatial_dict['Structure'][site_key]:
                    g_ld.add((INST[quote(site_key)], BOT.hasBuilding, INST[quote(bld)]))
                    g_ld.add((INST[quote(site_key)], BOT.containsZone, INST[quote(bld)]))
            except KeyError:
                continue

        for bld_key, bld_value in spatial_dict['IfcBuilding'].items():
            g_ld.add((INST[quote(bld_key)], RDF.type, TSO.Zone))
            g_ld.add((INST[quote(bld_key)], RDF.type, BOT.Building))
            try:
                for storey in spatial_dict['Structure'][bld_key]:
                    g_ld.add((INST[quote(bld_key)], BOT.hasStorey, INST[quote(storey)]))
                    g_ld.add((INST[quote(bld_key)], BOT.containsZone, INST[quote(storey)]))
            except KeyError:
                continue

        for storey_key, storey_value in spatial_dict['IfcBuildingStorey'].items():
            g_ld.add((INST[quote(storey_key)], RDF.type, TSO.Zone))
            g_ld.add((INST[quote(storey_key)], RDF.type, BOT.Storey))
            try:
                for space in spatial_dict['Structure'][storey_key]:
                    g_ld.add((INST[quote(storey_key)], BOT.hasSpace, INST[quote(space)]))
                    g_ld.add((INST[quote(storey_key)], BOT.containsZone, INST[quote(space)]))
            except KeyError:
                continue

        for space_key, space_value in spatial_dict['IfcSpace'].items():
            g_ld.add((INST[quote(space_key)], RDF.type, TSO.Zone))
            g_ld.add((INST[quote(space_key)], RDF.type, BOT.Space))

        lookup_dict = dict()
        points_list = list()
        for i, node in enumerate(enriched_graph.nodes(data=True)):
            converted_point_position = [float(node[1]["ifc_position"][0])/1000, float(node[1]["ifc_position"][1])/1000, float(node[1]["ifc_position"][2])/1000]
            points_list.append(converted_point_position)
            lookup_dict[i] = (node[0], node[1]['ifc_class'])

        for space_key, space_value in spatial_dict['IfcSpace'].items():
            distance_list = list(proximity.ProximityQuery(space_value['Mesh']).signed_distance(points_list))

            for idx, distance in enumerate(distance_list):
                if distance >= 0:
                    g_ld.add((INST[quote(lookup_dict[idx][0])], TSO.locatedIn, INST[quote(space_key)]))
                    g_ld.add((INST[quote(space_key)], TSO.contains, INST[quote(lookup_dict[idx][0])]))

                    if lookup_dict[idx][0] in serves_dict:
                        serves_dict[lookup_dict[idx][0]].append(space_key)
                    else:
                        serves_dict[lookup_dict[idx][0]] = [space_key]

    return g_ld, serves_dict


def add_component_classification(g_ld, node, INST, IFC):
    # Klassifikation von Komponenten anhand der zugeordneten IFC Klasse
    # Distribution Flow Element
    # Flow Segment
    if node[1]['ifc_class'] == 'IfcPipeSegment':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcPipeSegment))
    elif node[1]['ifc_class'] == 'IfcDuctSegment':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcDuctSegment))
    elif node[1]['ifc_class'] == 'IfcCableSegment':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcCableSegment))
    elif node[1]['ifc_class'] == 'IfcCableCarrierSegment':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcCableCarrierSegment))
    # Flow Fitting
    elif node[1]['ifc_class'] == 'IfcPipeFitting':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcPipeFitting))
    elif node[1]['ifc_class'] == 'IfcDuctFitting':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcDuctFitting))
    elif node[1]['ifc_class'] == 'IfcCableFitting':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcCableFitting))
    elif node[1]['ifc_class'] == 'IfcCableCarrierFitting':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcCableCarrierFitting))
    elif node[1]['ifc_class'] == 'IfcJunctionBox':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcJunctionBox))
    # Flow Moving Device
    elif node[1]['ifc_class'] == 'IfcPump':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcPump))
    elif node[1]['ifc_class'] == 'IfcFan':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcFan))
    elif node[1]['ifc_class'] == 'IfcCompressor':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcCompressor))
    # Flow Controller
    elif node[1]['ifc_class'] == 'IfcAirTerminalBox':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcAirTerminalBox))
    elif node[1]['ifc_class'] == 'IfcDamper':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcDamper))
    elif node[1]['ifc_class'] == 'IfcElectricDistributionBoard':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcElectricDistributionBoard))
    elif node[1]['ifc_class'] == 'IfcElectricTimeControl':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcElectricTimeControl))
    elif node[1]['ifc_class'] == 'IfcFlowMeter':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcFlowMeter))
    elif node[1]['ifc_class'] == 'IfcProtectiveDevice':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcProtectiveDevice))
    elif node[1]['ifc_class'] == 'IfcSwitchingDevice':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcSwitchingDevice))
    elif node[1]['ifc_class'] == 'IfcValve':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcValve))
    # Flow Storage Device
    elif node[1]['ifc_class'] == 'IfcTank':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcTank))
    elif node[1]['ifc_class'] == 'IfcElectricFlowStorageDevice':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcElectricFlowStorageDevice))
    # Flow Treatment Device
    elif node[1]['ifc_class'] == 'IfcDuctSilencer':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcDuctSilencer))
    elif node[1]['ifc_class'] == 'IfcFilter':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcFilter))
    elif node[1]['ifc_class'] == 'IfcInterceptor':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcInterceptor))
    # Flow Terminal
    elif node[1]['ifc_class'] == 'IfcSanitaryTerminal':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcSanitaryTerminal))
    elif node[1]['ifc_class'] == 'IfcSpaceHeater':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.SpaceHeater))
    elif node[1]['ifc_class'] == 'IfcWasteTerminal':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcWasteTerminal))
    elif node[1]['ifc_class'] == 'IfcAirTerminal':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcAirTerminal))
    elif node[1]['ifc_class'] == 'IfcAudioVisualAppliance':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcAudioVisualAppliance))
    elif node[1]['ifc_class'] == 'IfcCommunicationsAppliance':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcCommunicationsAppliance))
    elif node[1]['ifc_class'] == 'IfcElectricAppliance':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcElectricAppliance))
    elif node[1]['ifc_class'] == 'IfcLamp':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcLamp))
    elif node[1]['ifc_class'] == 'IfcLightFixture':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcLightFixture))
    elif node[1]['ifc_class'] == 'IfcMedicalDevice':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcMedicalDevice))
    elif node[1]['ifc_class'] == 'IfcOutlet':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcOutlet))
    elif node[1]['ifc_class'] == 'IfcStackTerminal':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcStackTerminal))
    elif node[1]['ifc_class'] == 'IfcFireSuppressionTerminal':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcFireSuppressionTerminal))
    # Distribution Chamber Element
    elif node[1]['ifc_class'] == 'IfcDistributionChamberElement':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcDistributionChamberElement))
    # Energy Conversion Device
    elif node[1]['ifc_class'] == 'IfcAirToAirHeatRecovery':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcAirToAirHeatRecovery))
    elif node[1]['ifc_class'] == 'IfcBoiler':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcBoiler))
    elif node[1]['ifc_class'] == 'IfcBurner':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcBurner))
    elif node[1]['ifc_class'] == 'IfcChiller':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcChiller))
    elif node[1]['ifc_class'] == 'IfcCoil':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcCoil))
    elif node[1]['ifc_class'] == 'IfcCondenser':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcCondenser))
    elif node[1]['ifc_class'] == 'IfcCooledBeam':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcCooledBeam))
    elif node[1]['ifc_class'] == 'IfcElectricGenerator':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcElectricGenerator))
    elif node[1]['ifc_class'] == 'IfcElectricMotor':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcElectricMotor))
    elif node[1]['ifc_class'] == 'IfcEngine':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcEngine))
    elif node[1]['ifc_class'] == 'IfcEvaporativeCooler':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcEvaporativeCooler))
    elif node[1]['ifc_class'] == 'IfcEvaporator':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcEvaporator))
    elif node[1]['ifc_class'] == 'IfcHeatExchanger':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcHeatExchanger))
    elif node[1]['ifc_class'] == 'IfcHumidifier':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcHumidifier))
    elif node[1]['ifc_class'] == 'IfcMotorConnection':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcMotorConnection))
    elif node[1]['ifc_class'] == 'IfcSolarDevice':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcSolarDevice))
    elif node[1]['ifc_class'] == 'IfcTransformer':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcTransformer))
    elif node[1]['ifc_class'] == 'IfcTubeBundle':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcTubeBundle))
    elif node[1]['ifc_class'] == 'IfcUnitaryEquipment':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcUnitaryEquipment))
    # Distribution Control Element
    elif node[1]['ifc_class'] == 'IfcActuator':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcActuator))
    elif node[1]['ifc_class'] == 'IfcAlarm':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcAlarm))
    elif node[1]['ifc_class'] == 'IfcController':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcController))
    elif node[1]['ifc_class'] == 'IfcFlowInstrument':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcFlowInstrument))
    elif node[1]['ifc_class'] == 'IfcProtectiveDeviceTrippingUnit':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcProtectiveDeviceTrippingUnit))
    elif node[1]['ifc_class'] == 'IfcSensor':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcSensor))
    elif node[1]['ifc_class'] == 'IfcUnitaryControlElement':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcUnitaryControlElement))

    # UpperLevel
    elif node[1]['ifc_class'] == 'IfcFlowSegment':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcFlowSegment))
    elif node[1]['ifc_class'] == 'IfcFlowFitting':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcFlowFitting))
    elif node[1]['ifc_class'] == 'IfcFlowTerminal':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcFlowTerminal))
    elif node[1]['ifc_class'] == 'IfcFlowController':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcFlowController))
    elif node[1]['ifc_class'] == 'IfcFlowStorageDevice':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcFlowStorageDevice))
    elif node[1]['ifc_class'] == 'IfcFlowTreatmentDevice':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcFlowTreatmentDevice))
    elif node[1]['ifc_class'] == 'IfcFlowMovingDevice':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcFlowMovingDevice))
    elif node[1]['ifc_class'] == 'IfcEnergyConversionDevice':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcEnergyConversionDevice))

    elif node[1]['ifc_class'] == 'IfcBuildingElementProxy':
        g_ld.add((INST[quote(node[0])], RDF.type, IFC.IfcBuildingElementProxy))

    return g_ld


def add_component_classification_type(g_ld, node, INST, IFC):
    # Klassifikation von Komponenten anhang des zugeordneten Typs der IFC Klasse

    # Distribution Flow Element
    # Flow Segment
    if node[1]['ifc_class'] in {'IfcPipeSegment', 'IfcDuctSegment', 'IfcCableSegment', 'IfcCableCarrierSegment'}:
        if node[1]['ifc_type'] == 'RIGIDSEGMENT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.RIGIDSEGMENT))
        elif node[1]['ifc_type'] == 'NOTDEFINED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.NOTDEFINED))
        elif node[1]['ifc_type'] == 'FLEXIBLESEGMENT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FLEXIBLESEGMENT))
        elif node[1]['ifc_type'] == 'CULVERT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CULVERT))
        elif node[1]['ifc_type'] == 'GUTTER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.GUTTER))
        elif node[1]['ifc_type'] == 'SPOOL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SPOOL))

    # Flow Fitting
    elif node[1]['ifc_class'] in {'IfcPipeFitting', 'IfcDuctFitting', 'IfcCableFitting', 'IfcCableCarrierFitting', 'IfcJunctionBox'}:
        if node[1]['ifc_type'] == 'BEND':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.BEND))
        elif node[1]['ifc_type'] == 'NOTDEFINED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.NOTDEFINED))
        elif node[1]['ifc_type'] == 'CONNECTOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CONNECTOR))
        elif node[1]['ifc_type'] == 'ENTRY':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ENTRY))
        elif node[1]['ifc_type'] == 'EXIT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.EXIT))
        elif node[1]['ifc_type'] == 'JUNCTION':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.JUNCTION))
        elif node[1]['ifc_type'] == 'OBSTRUCTION':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.OBSTRUCTION))
        elif node[1]['ifc_type'] == 'TRANSITION':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.TRANSITION))
        elif node[1]['ifc_type'] == 'DATA':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DATA))
        elif node[1]['ifc_type'] == 'POWER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.POWER))
        elif node[1]['ifc_type'] == 'DATA':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DATA))
        elif node[1]['ifc_type'] == 'CROSS':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CROSS))
        elif node[1]['ifc_type'] == 'REDUCER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.REDUCER))
        elif node[1]['ifc_type'] == 'TEE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.TEE))

    # Flow Controller
    elif node[1]['ifc_class'] in {'IfcAirTerminalBox', 'IfcDamper', 'IfcElectricDistributionBoard', 'IfcElectricTimeControl', 'IfcFlowMeter', 'IfcProtectiveDevice', 'IfcSwitchingDevice', 'IfcValve'}:
        if node[1]['ifc_type'] == 'CONSTANTFLOW':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CONSTANTFLOW))
        elif node[1]['ifc_type'] == 'NOTDEFINED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.NOTDEFINED))
        elif node[1]['ifc_type'] == 'VARIABLEFLOWPRESSUREDEPENDANT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.VARIABLEFLOWPRESSUREDEPENDANT))
        elif node[1]['ifc_type'] == 'VARIABLEFLOWPRESSUREINDEPENDANT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.VARIABLEFLOWPRESSUREINDEPENDANT))
        elif node[1]['ifc_type'] == 'BACKDRAFTDAMPER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.BACKDRAFTDAMPER))
        elif node[1]['ifc_type'] == 'BALANCINGDAMPER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.BALANCINGDAMPER))
        elif node[1]['ifc_type'] == 'BLASTDAMPER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.BLASTDAMPER))
        elif node[1]['ifc_type'] == 'CONTROLDAMPER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CONTROLDAMPER))
        elif node[1]['ifc_type'] == 'FIREDAMPER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FIREDAMPER))
        elif node[1]['ifc_type'] == 'FIRESMOKEDAMPER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FIRESMOKEDAMPER))
        elif node[1]['ifc_type'] == 'FUMEHOODEXHAUST':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FUMEHOODEXHAUST))
        elif node[1]['ifc_type'] == 'GRAVITYDAMPER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.GRAVITYDAMPER))
        elif node[1]['ifc_type'] == 'GRAVITYRELIEFDAMPER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.GRAVITYRELIEFDAMPER))
        elif node[1]['ifc_type'] == 'RELIEFDAMPER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.RELIEFDAMPER))
        elif node[1]['ifc_type'] == 'SMOKEDAMPER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SMOKEDAMPER))
        elif node[1]['ifc_type'] == 'CONSUMERUNIT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CONSUMERUNIT))
        elif node[1]['ifc_type'] == 'DISTRIBUTIONBOARD':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DISTRIBUTIONBOARD))
        elif node[1]['ifc_type'] == 'MOTORCONTROLCENTRE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.MOTORCONTROLCENTRE))
        elif node[1]['ifc_type'] == 'SWITCHBOARD':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SWITCHBOARD))
        elif node[1]['ifc_type'] == 'ENERGYMETER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ENERGYMETER))
        elif node[1]['ifc_type'] == 'GASMETER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.GASMETER))
        elif node[1]['ifc_type'] == 'OILMETER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.OILMETER))
        elif node[1]['ifc_type'] == 'WATERMETER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WATERMETER))
        elif node[1]['ifc_type'] == 'AIRRELEASE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.AIRRELEASE))
        elif node[1]['ifc_type'] == 'ANTIVACUUM':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ANTIVACUUM))
        elif node[1]['ifc_type'] == 'CHANGEOVER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CHANGEOVER))
        elif node[1]['ifc_type'] == 'CHECK':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CHECK))
        elif node[1]['ifc_type'] == 'COMMISSIONING':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.COMMISSIONING))
        elif node[1]['ifc_type'] == 'DIVERTING':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DIVERTING))
        elif node[1]['ifc_type'] == 'DRAWOFFCOCK':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DRAWOFFCOCK))
        elif node[1]['ifc_type'] == 'DOUBLECHECK':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DOUBLECHECK))
        elif node[1]['ifc_type'] == 'DOUBLEREGULATING':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DOUBLEREGULATING))
        elif node[1]['ifc_type'] == 'FAUCET':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FAUCET))
        elif node[1]['ifc_type'] == 'FLUSHING':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FLUSHING))
        elif node[1]['ifc_type'] == 'GASCOCK':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.GASCOCK))
        elif node[1]['ifc_type'] == 'GASTAP':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.GASTAP))
        elif node[1]['ifc_type'] == 'ISOLATING':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ISOLATING))
        elif node[1]['ifc_type'] == 'MIXING':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.MIXING))
        elif node[1]['ifc_type'] == 'PRESSUREREDUCING':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.PRESSUREREDUCING))
        elif node[1]['ifc_type'] == 'PRESSURERELIEF':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.PRESSURERELIEF))
        elif node[1]['ifc_type'] == 'REGULATING':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.REGULATING))
        elif node[1]['ifc_type'] == 'SAFETYCUTOFF':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SAFETYCUTOFF))
        elif node[1]['ifc_type'] == 'STEAMTRAP':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.STEAMTRAP))
        elif node[1]['ifc_type'] == 'STOPCOCK':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.STOPCOCK))

    # Flow Moving Device
    elif node[1]['ifc_class'] in {'IfcPump', 'IfcFan', 'IfcCompressor'}:
        if node[1]['ifc_type'] == 'CIRCULATOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CIRCULATOR))
        elif node[1]['ifc_type'] == 'NOTDEFINED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.NOTDEFINED))
        elif node[1]['ifc_type'] == 'ENDSUCTION':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ENDSUCTION))
        elif node[1]['ifc_type'] == 'SPLITCASE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SPLITCASE))
        elif node[1]['ifc_type'] == 'SUBMERSIBLEPUMP':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SUBMERSIBLEPUMP))
        elif node[1]['ifc_type'] == 'SUMPPUMP':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SUMPPUMP))
        elif node[1]['ifc_type'] == 'VERTICALINLINE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.VERTICALINLINE))
        elif node[1]['ifc_type'] == 'VERTICALTURBINE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.VERTICALTURBINE))
        elif node[1]['ifc_type'] == 'CENTRIFUGALFORWARDCURVED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CENTRIFUGALFORWARDCURVED))
        elif node[1]['ifc_type'] == 'CENTRIFUGALRADIAL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CENTRIFUGALRADIAL))
        elif node[1]['ifc_type'] == 'CENTRIFUGALBACKWARDINCLINEDCURVED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CENTRIFUGALBACKWARDINCLINEDCURVED))
        elif node[1]['ifc_type'] == 'CENTRIFUGALAIRFOIL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CENTRIFUGALAIRFOIL))
        elif node[1]['ifc_type'] == 'TUBEAXIAL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.TUBEAXIAL))
        elif node[1]['ifc_type'] == 'VANEAXIAL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.VANEAXIAL))
        elif node[1]['ifc_type'] == 'PROPELLORAXIAL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.PROPELLORAXIAL))
        elif node[1]['ifc_type'] == 'DYNAMIC':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DYNAMIC))
        elif node[1]['ifc_type'] == 'RECIPROCATING':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.RECIPROCATING))
        elif node[1]['ifc_type'] == 'ROTARY':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ROTARY))
        elif node[1]['ifc_type'] == 'SCROLL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SCROLL))
        elif node[1]['ifc_type'] == 'TROCHOIDAL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.TROCHOIDAL))
        elif node[1]['ifc_type'] == 'SINGLESTAGE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SINGLESTAGE))
        elif node[1]['ifc_type'] == 'BOOSTER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.BOOSTER))
        elif node[1]['ifc_type'] == 'OPENTYPE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.OPENTYPE))
        elif node[1]['ifc_type'] == 'HERMETIC':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.HERMETIC))
        elif node[1]['ifc_type'] == 'SEMIHERMETIC':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SEMIHERMETIC))
        elif node[1]['ifc_type'] == 'WELDEDSHELLHERMETIC':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WELDEDSHELLHERMETIC))
        elif node[1]['ifc_type'] == 'ROLLINGPISTON':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ROLLINGPISTON))
        elif node[1]['ifc_type'] == 'ROTARYVANE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ROTARYVANE))
        elif node[1]['ifc_type'] == 'SINGLESCREW':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SINGLESCREW))
        elif node[1]['ifc_type'] == 'TWINSCREW':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.TWINSCREW))

    # Flow Storage Device
    elif node[1]['ifc_class'] in {'IfcTank', 'IfcElectricFlowStorageDevice'}:
        if node[1]['ifc_type'] == 'BASIN':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.BASIN))
        elif node[1]['ifc_type'] == 'NOTDEFINED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.NOTDEFINED))
        elif node[1]['ifc_type'] == 'BREAKPRESSURE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.BREAKPRESSURE))
        elif node[1]['ifc_type'] == 'EXPANSION':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.EXPANSION))
        elif node[1]['ifc_type'] == 'FEEDANDEXPANSION':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FEEDANDEXPANSION))
        elif node[1]['ifc_type'] == 'PRESSUREVESSEL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.PRESSUREVESSEL))
        elif node[1]['ifc_type'] == 'STORAGE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.STORAGE))
        elif node[1]['ifc_type'] == 'VESSEL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.VESSEL))
        elif node[1]['ifc_type'] == 'BATTERY':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.BATTERY))
        elif node[1]['ifc_type'] == 'CAPACITORBANK':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CAPACITORBANK))
        elif node[1]['ifc_type'] == 'HARMONICFILTER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.HARMONICFILTER))
        elif node[1]['ifc_type'] == 'INDUCTORBANK':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.INDUCTORBANK))
        elif node[1]['ifc_type'] == 'UPS':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.UPS))

    # Flow Storage Device
    elif node[1]['ifc_class'] in {'IfcDuctSilencer', 'IfcFilter', 'IfcInterceptor'}:
        if node[1]['ifc_type'] == 'FLATOVAL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FLATOVAL))
        elif node[1]['ifc_type'] == 'NOTDEFINED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.NOTDEFINED))
        elif node[1]['ifc_type'] == 'RECTANGULAR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.RECTANGULAR))
        elif node[1]['ifc_type'] == 'ROUND':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ROUND))
        elif node[1]['ifc_type'] == 'AIRPARTICLEFILTER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.AIRPARTICLEFILTER))
        elif node[1]['ifc_type'] == 'COMPRESSEDAIRFILTER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.COMPRESSEDAIRFILTER))
        elif node[1]['ifc_type'] == 'ODORFILTER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ODORFILTER))
        elif node[1]['ifc_type'] == 'OILFILTER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.OILFILTER))
        elif node[1]['ifc_type'] == 'STRAINER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.STRAINER))
        elif node[1]['ifc_type'] == 'WATERFILTER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WATERFILTER))
        elif node[1]['ifc_type'] == 'HARMONICFILTER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.HARMONICFILTER))
        elif node[1]['ifc_type'] == 'CYCLONIC':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CYCLONIC))
        elif node[1]['ifc_type'] == 'GREASE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.GREASE))
        elif node[1]['ifc_type'] == 'OIL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.OIL))
        elif node[1]['ifc_type'] == 'PETROL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.PETROL))

    # Distribution Chamber Element
    elif node[1]['ifc_class'] in {'IfcDistributionChamberElement'}:
        if node[1]['ifc_type'] == 'FORMEDDUCT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FORMEDDUCT))
        elif node[1]['ifc_type'] == 'NOTDEFINED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.NOTDEFINED))
        elif node[1]['ifc_type'] == 'INSPECTIONCHAMBER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.INSPECTIONCHAMBER))
        elif node[1]['ifc_type'] == 'INSPECTIONPIT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.INSPECTIONPIT))
        elif node[1]['ifc_type'] == 'MANHOLE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.MANHOLE))
        elif node[1]['ifc_type'] == 'METERCHAMBER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.METERCHAMBER))
        elif node[1]['ifc_type'] == 'SUMP':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SUMP))
        elif node[1]['ifc_type'] == 'TRENCH':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.TRENCH))
        elif node[1]['ifc_type'] == 'VALVECHAMBER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.VALVECHAMBER))

    # Flow Terminal
    elif node[1]['ifc_class'] in {'IfcAirTerminal', 'IfcAudioVisualAppliance', 'IfcCommunicationsAppliance', 'IfcElectricAppliance', 'IfcFireSuppressionTerminal', 'IfcLamp', 'IfcLightFixture',
                                  'IfcMedicalDevice', 'IfcOutlet', 'IfcSanitaryTerminal', 'IfcSpaceHeater', 'IfcStackTerminal', 'IfcWasteTerminal'}:
        if node[1]['ifc_type'] == 'DIFFUSER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DIFFUSER))
        elif node[1]['ifc_type'] == 'NOTDEFINED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.NOTDEFINED))
        elif node[1]['ifc_type'] == 'GRILLE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.GRILLE))
        elif node[1]['ifc_type'] == 'LOUVRE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.LOUVRE))
        elif node[1]['ifc_type'] == 'REGISTER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.REGISTER))
        elif node[1]['ifc_type'] == 'BREECHINGINLET':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.BREECHINGINLET))
        elif node[1]['ifc_type'] == 'FIREHYDRANT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FIREHYDRANT))
        elif node[1]['ifc_type'] == 'HOSEREEL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.HOSEREEL))
        elif node[1]['ifc_type'] == 'SPRINKLER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SPRINKLER))
        elif node[1]['ifc_type'] == 'SPRINKLERDEFLECTOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SPRINKLERDEFLECTOR))
        elif node[1]['ifc_type'] == 'AUDIOVISUALOUTLET':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.AUDIOVISUALOUTLET))
        elif node[1]['ifc_type'] == 'COMMUNICATIONSOUTLET':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.COMMUNICATIONSOUTLET))
        elif node[1]['ifc_type'] == 'POWEROUTLET':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.POWEROUTLET))
        elif node[1]['ifc_type'] == 'DATAOUTLET':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DATAOUTLET))
        elif node[1]['ifc_type'] == 'TELEPHONEOUTLET':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.TELEPHONEOUTLET))
        elif node[1]['ifc_type'] == 'BATH':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.BATH))
        elif node[1]['ifc_type'] == 'BIDET':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.BIDET))
        elif node[1]['ifc_type'] == 'CISTERN':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CISTERN))
        elif node[1]['ifc_type'] == 'SHOWER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SHOWER))
        elif node[1]['ifc_type'] == 'SINK':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SINK))
        elif node[1]['ifc_type'] == 'SANITARYFOUNTAIN':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SANITARYFOUNTAIN))
        elif node[1]['ifc_type'] == 'TOILETPAN':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.TOILETPAN))
        elif node[1]['ifc_type'] == 'URINAL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.URINAL))
        elif node[1]['ifc_type'] == 'WASHHANDBASIN':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WASHHANDBASIN))
        elif node[1]['ifc_type'] == 'CONVECTOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CONVECTOR))
        elif node[1]['ifc_type'] == 'RADIATOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.RADIATOR))
        elif node[1]['ifc_type'] == 'BIRDCAGE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.BIRDCAGE))
        elif node[1]['ifc_type'] == 'COWL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.COWL))
        elif node[1]['ifc_type'] == 'RAINWATERHOPPER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.RAINWATERHOPPER))
        elif node[1]['ifc_type'] == 'FLOORTRAP':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FLOORTRAP))
        elif node[1]['ifc_type'] == 'FLOORWASTE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FLOORWASTE))
        elif node[1]['ifc_type'] == 'GULLYSUMP':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.GULLYSUMP))
        elif node[1]['ifc_type'] == 'GULLYTRAP':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.GULLYTRAP))
        elif node[1]['ifc_type'] == 'ROOFDRAIN':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ROOFDRAIN))
        elif node[1]['ifc_type'] == 'WASTEDISPOSALUNIT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WASTEDISPOSALUNIT))
        elif node[1]['ifc_type'] == 'WASTETRAP':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WASTETRAP))

    # Energy Conversion Device
    elif node[1]['ifc_class'] in {'IfcAirToAirHeatRecovery', 'IfcBoiler', 'IfcBurner', 'IfcChiller', 'IfcCoil', 'IfcCondenser'}:
        if node[1]['ifc_type'] == 'FIXEDPLATECOUNTERFLOWEXCHANGER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FIXEDPLATECOUNTERFLOWEXCHANGER))
        elif node[1]['ifc_type'] == 'NOTDEFINED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.NOTDEFINED))
        elif node[1]['ifc_type'] == 'FIXEDPLATECROSSFLOWEXCHANGER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FIXEDPLATECROSSFLOWEXCHANGER))
        elif node[1]['ifc_type'] == 'FIXEDPLATEPARALLELFLOWEXCHANGER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FIXEDPLATEPARALLELFLOWEXCHANGER))
        elif node[1]['ifc_type'] == 'ROTARYWHEEL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ROTARYWHEEL))
        elif node[1]['ifc_type'] == 'RUNAROUNDCOILLOOP':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.RUNAROUNDCOILLOOP))
        elif node[1]['ifc_type'] == 'HEATPIPE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.HEATPIPE))
        elif node[1]['ifc_type'] == 'TWINTOWERENTHALPYRECOVERYLOOPS':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.TWINTOWERENTHALPYRECOVERYLOOPS))
        elif node[1]['ifc_type'] == 'THERMOSIPHONSEALEDTUBEHEATEXCHANGERS':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.THERMOSIPHONSEALEDTUBEHEATEXCHANGERS))
        elif node[1]['ifc_type'] == 'THERMOSIPHONCOILTYPEHEATEXCHANGERS':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.THERMOSIPHONCOILTYPEHEATEXCHANGERS))
        elif node[1]['ifc_type'] == 'WATER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WATER))
        elif node[1]['ifc_type'] == 'STEAM':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.STEAM))
        elif node[1]['ifc_type'] == 'AIRCOOLED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.AIRCOOLED))
        elif node[1]['ifc_type'] == 'WATERCOOLED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WATERCOOLED))
        elif node[1]['ifc_type'] == 'HEATRECOVERY':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.HEATRECOVERY))
        elif node[1]['ifc_type'] == 'DXCOOLINGCOIL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DXCOOLINGCOIL))
        elif node[1]['ifc_type'] == 'ELECTRICHEATINGCOIL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ELECTRICHEATINGCOIL))
        elif node[1]['ifc_type'] == 'GASHEATINGCOIL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.GASHEATINGCOIL))
        elif node[1]['ifc_type'] == 'HYDRONICCOIL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.HYDRONICCOIL))
        elif node[1]['ifc_type'] == 'STEAMHEATINGCOIL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.STEAMHEATINGCOIL))
        elif node[1]['ifc_type'] == 'WATERCOOLINGCOIL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WATERCOOLINGCOIL))
        elif node[1]['ifc_type'] == 'WATERHEATINGCOIL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WATERHEATINGCOIL))
        elif node[1]['ifc_type'] == 'AIRCOOLED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.AIRCOOLED))
        elif node[1]['ifc_type'] == 'EVAPORATIVECOOLED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.EVAPORATIVECOOLED))
        elif node[1]['ifc_type'] == 'WATERCOOLED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WATERCOOLED))
        elif node[1]['ifc_type'] == 'WATERCOOLEDBRAZEDPLATE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WATERCOOLEDBRAZEDPLATE))
        elif node[1]['ifc_type'] == 'WATERCOOLEDSHELLCOIL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WATERCOOLEDSHELLCOIL))
        elif node[1]['ifc_type'] == 'WATERCOOLEDSHELLTUBE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WATERCOOLEDSHELLTUBE))
        elif node[1]['ifc_type'] == 'WATERCOOLEDTUBEINTUBE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WATERCOOLEDTUBEINTUBE))

    elif node[1]['ifc_class'] in {'IfcCooledBeam', 'IfcCoolingTower', 'IfcElectricGenerator', 'IfcEngine', 'IfcEvaporativeCooler', 'IfcEvaporator'}:
        if node[1]['ifc_type'] == 'ACTIVE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ACTIVE))
        elif node[1]['ifc_type'] == 'NOTDEFINED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.NOTDEFINED))
        elif node[1]['ifc_type'] == 'PASSIVE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.PASSIVE))
        elif node[1]['ifc_type'] == 'NATURALDRAFT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.NATURALDRAFT))
        elif node[1]['ifc_type'] == 'MECHANICALINDUCEDDRAFT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.MECHANICALINDUCEDDRAFT))
        elif node[1]['ifc_type'] == 'MECHANICALFORCEDDRAFT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.MECHANICALFORCEDDRAFT))
        elif node[1]['ifc_type'] == 'CHP':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CHP))
        elif node[1]['ifc_type'] == 'ENGINEGENERATOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ENGINEGENERATOR))
        elif node[1]['ifc_type'] == 'STANDALONE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.STANDALONE))
        elif node[1]['ifc_type'] == 'DC':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DC))
        elif node[1]['ifc_type'] == 'INDUCTION':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.INDUCTION))
        elif node[1]['ifc_type'] == 'POLYPHASE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.POLYPHASE))
        elif node[1]['ifc_type'] == 'RELUCTANCESYNCHRONOUS':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.RELUCTANCESYNCHRONOUS))
        elif node[1]['ifc_type'] == 'SYNCHRONOUS':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SYNCHRONOUS))
        elif node[1]['ifc_type'] == 'EXTERNALCOMBUSTION':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.EXTERNALCOMBUSTION))
        elif node[1]['ifc_type'] == 'INTERNALCOMBUSTION':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.INTERNALCOMBUSTION))
        elif node[1]['ifc_type'] == 'DIRECTEVAPORATIVERANDOMMEDIAAIRCOOLER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DIRECTEVAPORATIVERANDOMMEDIAAIRCOOLER))
        elif node[1]['ifc_type'] == 'DIRECTEVAPORATIVERIGIDMEDIAAIRCOOLER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DIRECTEVAPORATIVERIGIDMEDIAAIRCOOLER))
        elif node[1]['ifc_type'] == 'DIRECTEVAPORATIVESLINGERSPACKAGEDAIRCOOLER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DIRECTEVAPORATIVESLINGERSPACKAGEDAIRCOOLER))
        elif node[1]['ifc_type'] == 'DIRECTEVAPORATIVEPACKAGEDROTARYAIRCOOLER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DIRECTEVAPORATIVEPACKAGEDROTARYAIRCOOLER))
        elif node[1]['ifc_type'] == 'DIRECTEVAPORATIVEAIRWASHER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DIRECTEVAPORATIVEAIRWASHER))
        elif node[1]['ifc_type'] == 'INDIRECTEVAPORATIVEPACKAGEAIRCOOLER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.INDIRECTEVAPORATIVEPACKAGEAIRCOOLER))
        elif node[1]['ifc_type'] == 'INDIRECTEVAPORATIVEWETCOIL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.INDIRECTEVAPORATIVEWETCOIL))
        elif node[1]['ifc_type'] == 'INDIRECTEVAPORATIVECOOLINGTOWERORCOILCOOLER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.INDIRECTEVAPORATIVECOOLINGTOWERORCOILCOOLER))
        elif node[1]['ifc_type'] == 'INDIRECTDIRECTCOMBINATION':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.INDIRECTDIRECTCOMBINATION))
        elif node[1]['ifc_type'] == 'DIRECTEXPANSION':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DIRECTEXPANSION))
        elif node[1]['ifc_type'] == 'DIRECTEXPANSIONSHELLANDTUBE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DIRECTEXPANSIONSHELLANDTUBE))
        elif node[1]['ifc_type'] == 'DIRECTEXPANSIONTUBEINTUBE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DIRECTEXPANSIONTUBEINTUBE))
        elif node[1]['ifc_type'] == 'DIRECTEXPANSIONBRAZEDPLATE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DIRECTEXPANSIONBRAZEDPLATE))
        elif node[1]['ifc_type'] == 'FLOODEDSHELLANDTUBE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FLOODEDSHELLANDTUBE))
        elif node[1]['ifc_type'] == 'SHELLANDCOIL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SHELLANDCOIL))

    elif node[1]['ifc_class'] in {'IfcHeatExchanger', 'IfcHumidifier', 'IfcMotorConnection', 'IfcSolarDevice', 'IfcTransformer', 'IfcTubeBundle', 'IfcUnitaryEquipment'}:
        if node[1]['ifc_type'] == 'PLATE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.PLATE))
        elif node[1]['ifc_type'] == 'NOTDEFINED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.NOTDEFINED))
        elif node[1]['ifc_type'] == 'SHELLANDTUBE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SHELLANDTUBE))
        elif node[1]['ifc_type'] == 'STEAMINJECTION':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.STEAMINJECTION))
        elif node[1]['ifc_type'] == 'ADIABATICAIRWASHER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ADIABATICAIRWASHER))
        elif node[1]['ifc_type'] == 'ADIABATICPAN':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ADIABATICPAN))
        elif node[1]['ifc_type'] == 'ADIABATICWETTEDELEMENT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ADIABATICWETTEDELEMENT))
        elif node[1]['ifc_type'] == 'ADIABATICATOMIZING':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ADIABATICATOMIZING))
        elif node[1]['ifc_type'] == 'ADIABATICULTRASONIC':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ADIABATICULTRASONIC))
        elif node[1]['ifc_type'] == 'ADIABATICRIGIDMEDIA':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ADIABATICRIGIDMEDIA))
        elif node[1]['ifc_type'] == 'ADIABATICCOMPRESSEDAIRNOZZLE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ADIABATICCOMPRESSEDAIRNOZZLE))
        elif node[1]['ifc_type'] == 'ASSISTEDELECTRIC':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ASSISTEDELECTRIC))
        elif node[1]['ifc_type'] == 'ASSISTEDNATURALGAS':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ASSISTEDNATURALGAS))
        elif node[1]['ifc_type'] == 'ASSISTEDPROPANE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ASSISTEDPROPANE))
        elif node[1]['ifc_type'] == 'ASSISTEDBUTANE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ASSISTEDBUTANE))
        elif node[1]['ifc_type'] == 'ASSISTEDSTEAM':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ASSISTEDSTEAM))
        elif node[1]['ifc_type'] == 'SOLARCOLLECTOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SOLARCOLLECTOR))
        elif node[1]['ifc_type'] == 'SOLARPANEL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SOLARPANEL))
        elif node[1]['ifc_type'] == 'CURRENT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CURRENT))
        elif node[1]['ifc_type'] == 'FREQUENCY':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FREQUENCY))
        elif node[1]['ifc_type'] == 'INVERTER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.INVERTER))
        elif node[1]['ifc_type'] == 'RECTIFIER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.RECTIFIER))
        elif node[1]['ifc_type'] == 'VOLTAGE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.VOLTAGE))
        elif node[1]['ifc_type'] == 'FINNED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FINNED))
        elif node[1]['ifc_type'] == 'AIRHANDLER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.AIRHANDLER))
        elif node[1]['ifc_type'] == 'AIRCONDITIONINGUNIT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.AIRCONDITIONINGUNIT))
        elif node[1]['ifc_type'] == 'DEHUMIDIFIER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.DEHUMIDIFIER))
        elif node[1]['ifc_type'] == 'SPLITSYSTEM':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SPLITSYSTEM))
        elif node[1]['ifc_type'] == 'ROOFTOPUNIT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ROOFTOPUNIT))

    # Distribution Control Element
    elif node[1]['ifc_class'] in {'IfcActuator', 'IfcAlarm'}:
        if node[1]['ifc_type'] == 'ELECTRICACTUATOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ELECTRICACTUATOR))
        elif node[1]['ifc_type'] == 'NOTDEFINED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.NOTDEFINED))
        elif node[1]['ifc_type'] == 'HANDOPERATEDACTUATOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.HANDOPERATEDACTUATOR))
        elif node[1]['ifc_type'] == 'HYDRAULICACTUATOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.HYDRAULICACTUATOR))
        elif node[1]['ifc_type'] == 'PNEUMATICACTUATOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.PNEUMATICACTUATOR))
        elif node[1]['ifc_type'] == 'THERMOSTATICACTUATOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.THERMOSTATICACTUATOR))
        elif node[1]['ifc_type'] == 'BELL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.BELL))
        elif node[1]['ifc_type'] == 'BREAKGLASSBUTTON':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.BREAKGLASSBUTTON))
        elif node[1]['ifc_type'] == 'LIGHT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.LIGHT))
        elif node[1]['ifc_type'] == 'MANUALPULLBOX':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.MANUALPULLBOX))
        elif node[1]['ifc_type'] == 'SIREN':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SIREN))
        elif node[1]['ifc_type'] == 'WHISTLE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WHISTLE))

    elif node[1]['ifc_class'] in {'IfcController', 'IfcFlowInstrument'}:
        if node[1]['ifc_type'] == 'FLOATING':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FLOATING))
        elif node[1]['ifc_type'] == 'NOTDEFINED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.NOTDEFINED))
        elif node[1]['ifc_type'] == 'PROGRAMMABLE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.PROGRAMMABLE))
        elif node[1]['ifc_type'] == 'PROPORTIONAL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.PROPORTIONAL))
        elif node[1]['ifc_type'] == 'MULTIPOSITION':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.MULTIPOSITION))
        elif node[1]['ifc_type'] == 'TWOPOSITION':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.TWOPOSITION))
        elif node[1]['ifc_type'] == 'PRESSUREGAUGE':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.PRESSUREGAUGE))
        elif node[1]['ifc_type'] == 'THERMOMETER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.THERMOMETER))
        elif node[1]['ifc_type'] == 'AMMETER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.AMMETER))
        elif node[1]['ifc_type'] == 'FREQUENCYMETER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FREQUENCYMETER))
        elif node[1]['ifc_type'] == 'POWERFACTORMETER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.POWERFACTORMETER))
        elif node[1]['ifc_type'] == 'PHASEANGLEMETER':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.PHASEANGLEMETER))
        elif node[1]['ifc_type'] == 'VOLTMETER_PEAK':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.VOLTMETER_PEAK))
        elif node[1]['ifc_type'] == 'VOLTMETER_RMS':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.VOLTMETER_RMS))

    elif node[1]['ifc_class'] in {'IfcProtectiveDeviceTrippingUnit', 'IfcUnitaryControlElement'}:
        if node[1]['ifc_type'] == 'ELECTRONIC':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ELECTRONIC))
        elif node[1]['ifc_type'] == 'NOTDEFINED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.NOTDEFINED))
        elif node[1]['ifc_type'] == 'ELECTROMAGNETIC':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ELECTROMAGNETIC))
        elif node[1]['ifc_type'] == 'RESIDUALCURRENT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.RESIDUALCURRENT))
        elif node[1]['ifc_type'] == 'THERMAL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.THERMAL))
        elif node[1]['ifc_type'] == 'ALARMPANEL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.ALARMPANEL))
        elif node[1]['ifc_type'] == 'CONTROLPANEL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CONTROLPANEL))
        elif node[1]['ifc_type'] == 'GASDETECTIONPANEL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.GASDETECTIONPANEL))
        elif node[1]['ifc_type'] == 'INDICATORPANEL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.INDICATORPANEL))
        elif node[1]['ifc_type'] == 'MIMICPANEL':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.MIMICPANEL))
        elif node[1]['ifc_type'] == 'HUMIDISTAT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.HUMIDISTAT))
        elif node[1]['ifc_type'] == 'THERMOSTAT':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.THERMOSTAT))
        elif node[1]['ifc_type'] == 'WEATHERSTATION':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WEATHERSTATION))

    elif node[1]['ifc_class'] in {'IfcSensor'}:
        if node[1]['ifc_type'] == 'COSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.COSENSOR))
        elif node[1]['ifc_type'] == 'NOTDEFINED':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.NOTDEFINED))
        elif node[1]['ifc_type'] == 'CO2SENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CO2SENSOR))
        elif node[1]['ifc_type'] == 'CONDUCTANCESENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CONDUCTANCESENSOR))
        elif node[1]['ifc_type'] == 'CONTACTSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.CONTACTSENSOR))
        elif node[1]['ifc_type'] == 'FIRESENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FIRESENSOR))
        elif node[1]['ifc_type'] == 'FLOWSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FLOWSENSOR))
        elif node[1]['ifc_type'] == 'FROSTSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.FROSTSENSOR))
        elif node[1]['ifc_type'] == 'GASSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.GASSENSOR))
        elif node[1]['ifc_type'] == 'HEATSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.HEATSENSOR))
        elif node[1]['ifc_type'] == 'HUMIDITYSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.HUMIDITYSENSOR))
        elif node[1]['ifc_type'] == 'IDENTIFIERSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.IDENTIFIERSENSOR))
        elif node[1]['ifc_type'] == 'IONCONCENTRATIONSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.IONCONCENTRATIONSENSOR))
        elif node[1]['ifc_type'] == 'LEVELSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.LEVELSENSOR))
        elif node[1]['ifc_type'] == 'LIGHTSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.LIGHTSENSOR))
        elif node[1]['ifc_type'] == 'MOISTURESENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.MOISTURESENSOR))
        elif node[1]['ifc_type'] == 'MOVEMENTSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.MOVEMENTSENSOR))
        elif node[1]['ifc_type'] == 'PHSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.PHSENSOR))
        elif node[1]['ifc_type'] == 'PRESSURESENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.PRESSURESENSOR))
        elif node[1]['ifc_type'] == 'RADIATIONSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.RADIATIONSENSOR))
        elif node[1]['ifc_type'] == 'RADIOACTIVITYSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.RADIOACTIVITYSENSOR))
        elif node[1]['ifc_type'] == 'SMOKESENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SMOKESENSOR))
        elif node[1]['ifc_type'] == 'SOUNDSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.SOUNDSENSOR))
        elif node[1]['ifc_type'] == 'TEMPERATURESENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.TEMPERATURESENSOR))
        elif node[1]['ifc_type'] == 'WINDSENSOR':
            g_ld.add((INST[quote(node[0])], IFC.PredefinedType, IFC.WINDSENSOR))

    return g_ld


def get_system_comp_by_key(hierarchie_dict, key):

    for x, value in hierarchie_dict.items():
        for system_key, system_value in value.items():
            if system_key == key:
                return set(system_value['Components'])

    return None

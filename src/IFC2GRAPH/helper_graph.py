import networkx as nx
import random


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


def get_topo_info(model, args, info_dict, position_dict):
    # Vorbereiten der Informationen für die Überführung in einen Graph
    # Kontrolle der verwendeten Beziehungsklasse
    global NESTS
    tmp_dict, NESTS = check_for_relationships(model)

    # Entitäten der Klassen vom Typ DistributionElement und BEP mit mindestens einem Port
    important_classes = ['IfcDistributionElement', 'IfcBuildingElementProxy']
    elem_dict = {}
    classes_without_ports_set = set(info_dict['Elements without ports']['GlobalIds'])
    for ifc_class in important_classes:
        tmp_list = model.by_type(ifc_class)
        for i in tmp_list:
            if i.GlobalId not in classes_without_ports_set:
                elem_dict[i.GlobalId] = i

    # Interation über alle wichtigen Elemente
    result_dict = dict()
    additional_data_dict = dict()
    for element_key, element_value in elem_dict.items():  # IfcElement
        result_dict[(element_key, element_value)] = {}
        result_dict[(element_key, element_value)]['OUT'] = []
        result_dict[(element_key, element_value)]['IN'] = []
        result_dict[(element_key, element_value)]['Position'] = [None, None, None]

        # Metadaten der Elemente analysieren (Name, Klasse, Typ, System, Beschreibung, RDS)
        system = get_system(element_value)
        result_dict[(element_key, element_value)]['System'] = system
        result_dict[(element_key, element_value)]['Name'] = element_value.Name
        result_dict[(element_key, element_value)]['Class'] = element_value.is_a()
        try:
            result_dict[(element_key, element_value)]['Subtype'] = element_value.PredefinedType
        except AttributeError:
            result_dict[(element_key, element_value)]['Subtype'] = 'NOTDEFINED'
        result_dict[(element_key, element_value)]['Description'] = element_value.Description

        # Ablage des RDS, wenn ein entsprechender Bezeichner gegeben ist
        if args.rds:
            property_name = args.rds
            property_value = get_property_value_by_name(property_name, element_value)
            result_dict[(element_key, element_value)]['AKS'] = property_value
        else:
            result_dict[(element_key, element_value)]['AKS'] = None

        # Ablage aller inversen Attribute wenn der optionale Parameter gesetzt ist
        if args.data:
            additional_data_dict[element_key] = get_all_properties_of_entity(element_value)

        # Zugeordnete Ports der Elemente auslesen
        ports = None
        if NESTS:
            test = element_value.IsNestedBy
            if test:
                for i in test:
                    ports = i.RelatedObjects
        else:
            try:
                test = element_value.HasPorts
                if test:
                    for i in test:
                        port = i.RelatingPort
                        ports = [port]
            except AttributeError:
                pass

        if ports:
            # Position des Elements anhand der Ports bestimmen
            certain_port = random.choice(ports)
            try:
                position = list(position_dict['IfcDistributionPort'][certain_port.GlobalId])
                position = [str(x) for x in position]
            except KeyError:
                position = [None, None, None]

            result_dict[(element_key, element_value)]['Position'] = position

            # Topologisch verbundene Elemente entsprechend der Flussrichtung der Ports zuordnen
            for j in ports:
                if j.FlowDirection == 'SOURCE':
                    tmp = j.ConnectedFrom
                    tmp_list = get_connected_elements(j, tmp)
                    result_dict[(element_value.GlobalId, element_value)]['OUT'].extend(tmp_list)
                if j.FlowDirection == 'SINK':
                    tmp = j.ConnectedTo
                    tmp_list = get_connected_elements(j, tmp)
                    result_dict[(element_value.GlobalId, element_value)]['IN'].extend(tmp_list)
                if j.FlowDirection == 'SOURCEANDSINK':
                    tmp_from = j.ConnectedFrom
                    tmp_list_from = get_connected_elements(j, tmp_from)
                    tmp_to = j.ConnectedTo
                    tmp_list_to = get_connected_elements(j, tmp_to)
                    tmp = tmp_list_to + tmp_list_from
                    result_dict[(element_value.GlobalId, element_value)]['OUT'].extend(tmp)
                    result_dict[(element_value.GlobalId, element_value)]['IN'].extend(tmp)

    return result_dict, additional_data_dict


def get_all_properties_of_entity(entity):
    # Analyse aller inversen Eigenschaften und Rückgabe dieser
    result_dict = {}
    for relDefinesByProperties in entity.IsDefinedBy:
        for prop in relDefinesByProperties.RelatingPropertyDefinition.HasProperties:
            try:
                result_dict[prop.Name] = prop.NominalValue.wrappedValue
            except AttributeError:
                continue
    return result_dict


def get_property_value_by_name(search_name, entity):
    # Suche nach einem bestimmen Eigenschaftsbezeichern und Rückgabe des Werts
    for relDefinesByProperties in entity.IsDefinedBy:
        for prop in relDefinesByProperties.RelatingPropertyDefinition.HasProperties:
            if prop.Name == search_name.strip():
                return prop.NominalValue.wrappedValue
    return None


def get_system(element):
    # Analyse des zugeordneten Systems und Rückgabe von dessen Name und Typ
    assignements = element.HasAssignments
    if assignements:
        for assignement in assignements:
            system = assignement.RelatingGroup
            if system:
                try:
                    system_type = system.PredefinedType
                except AttributeError:
                    system_type = 'NOTDEFINED'

                return_tuple = (system.Name, system_type)
                return return_tuple

    return None


def get_connected_elements(origin_port, rel_ports):
    # Analsyse der topologischen Verbindung und Rückgabe der angebundenen Elemente
    tmp_list = []
    if rel_ports:
        for rel_port in rel_ports:
            tmp_port = rel_port.RelatingPort
            if tmp_port.GlobalId == origin_port.GlobalId:
                tmp_port = rel_port.RelatedPort
            if tmp_port:
                if NESTS:
                    connected_elements_nests = tmp_port.Nests
                    if connected_elements_nests:
                        for l in connected_elements_nests:
                            conn_elements = l.RelatingObject
                            tmp_list.append((conn_elements.GlobalId, conn_elements))
                else:
                    connected_elements_nests = tmp_port.ContainedIn
                    if connected_elements_nests:
                        for l in connected_elements_nests:
                            conn_elements = l.RelatedElement
                            tmp_list.append((conn_elements.GlobalId, conn_elements))

    return tmp_list


def create_directed_graph(input_dict, additional_data_dict, args):
    # Konzeption eines gerichteten Graphs und Integation der aufbereiteten topologischen Informationen des IFC-Modells
    # Konzeptions des Graphs
    directed_graph = nx.DiGraph()

    # Integration der Knoten und Kanten
    for entity in input_dict:
        if args.data:
            data_entity = additional_data_dict[entity[0]]
        else:
            data_entity = None

        # Wenn Knoten nicht im Graph vorhanden ist wird dieser mit entsprehenden Metadaten hinzugefügt
        if entity[0] not in directed_graph:
            directed_graph.add_node(entity[0], ifc_id=entity[0], ifc_class=input_dict[entity]['Class'], ifc_type=input_dict[entity]['Subtype'],
                                    ifc_name=input_dict[entity]['Name'], ifc_description=input_dict[entity]['Description'],
                                    ifc_system=input_dict[entity]['System'], ifc_position=input_dict[entity]['Position'], elem_rds=input_dict[entity]['AKS'],
                                    additional_data=data_entity)

        # Für alle nachfolgenden Elemente wird ein Knoten angelegt und eine Kante wird hinzugefügt
        for element in input_dict[entity]['OUT']:
            if args.data:
                data_elem = additional_data_dict[element[0]]
            else:
                data_elem = None

            if not directed_graph.has_node(element[0]):
                directed_graph.add_node(element[0], ifc_id=element[0], ifc_class=input_dict[element]['Class'], ifc_type=input_dict[element]['Subtype'],
                                        ifc_name=input_dict[element]['Name'], ifc_description=input_dict[element]['Description'],
                                        ifc_system=input_dict[element]['System'], ifc_position=input_dict[element]['Position'], elem_rds=input_dict[element]['AKS'],
                                        additional_data=data_elem)

            if not directed_graph.has_edge(entity[0], element[0]):
                directed_graph.add_edge(entity[0], element[0])

        # Für alle zuvorkommenden Elemente wird ein Knoten angelegt und eine Kante wird hinzugefügt
        for element in input_dict[entity]['IN']:
            if args.data:
                data_elem = additional_data_dict[element[0]]
            else:
                data_elem = None

            if not directed_graph.has_node(element[0]):
                directed_graph.add_node(element[0], ifc_id=element[0], ifc_class=input_dict[element]['Class'], ifc_type=input_dict[element]['Subtype'],
                                        ifc_name=input_dict[element]['Name'], ifc_description=input_dict[element]['Description'],
                                        ifc_system=input_dict[element]['System'], ifc_position=input_dict[element]['Position'], elem_rds=input_dict[element]['AKS'],
                                        additional_data=data_elem)

            if not directed_graph.has_edge(element[0], entity[0]):
                directed_graph.add_edge(element[0], entity[0])

    return directed_graph


def add_edges_based_on_spatial_tree(directed_graph, pm_list, model, args):
    # Erweiterung der topologischen Verbindungen auf Basis der Prozesse der Anreicherung
    for possible_match in pm_list:
        possible_match_elements = [possible_match['source_elem_id'], possible_match['sink_elem_id']]
        for elem_id in possible_match_elements:
            if not directed_graph.has_node(elem_id):
                element_value = model.by_guid(elem_id)
                try:
                    subtype = element_value.PredefinedType
                except AttributeError:
                    subtype = 'NOTDEFINED'

                # Ablage des RDS, wenn ein entsprechender Bezeichner gegeben ist
                if args.rds:
                    property_name = args.rds
                    property_value = get_property_value_by_name(property_name, element_value)
                    aks = property_value
                else:
                    aks = None

                # Ablage aller inversen Attribute wenn der optionale Parameter gesetzt ist
                if args.data:
                    data_entity = get_all_properties_of_entity(element_value)
                else:
                    data_entity = None

                directed_graph.add_node(elem_id, ifc_id=elem_id, ifc_class=element_value.is_a(), ifc_type=subtype,
                                        ifc_name=element_value.Name, ifc_description=element_value.Description,
                                        ifc_system=get_system(element_value), elem_rds=aks, additional_data=data_entity)

        # Festlegung der Fließrichtung der Kante und Integration in den Graph
        first_port = model.by_guid(possible_match['source_port_id'])
        first_port_flowdirection = first_port.FlowDirection
        second_port = model.by_guid(possible_match['sink_port_id'])
        second_port_flowdirection = second_port.FlowDirection
        if first_port_flowdirection == 'SOURCE' and second_port_flowdirection == 'SINK':
            if not directed_graph.has_edge(possible_match_elements[0], possible_match_elements[1]):
                directed_graph.add_edge(possible_match_elements[0], possible_match_elements[1])
        elif first_port_flowdirection == 'SINK' and second_port_flowdirection == 'SOURCE':
            if not directed_graph.has_edge(possible_match_elements[1], possible_match_elements[0]):
                directed_graph.add_edge(possible_match_elements[1], possible_match_elements[0])
        else:
            if not directed_graph.has_edge(possible_match_elements[0], possible_match_elements[1]):
                directed_graph.add_edge(possible_match_elements[0], possible_match_elements[1])

            if not directed_graph.has_edge(possible_match_elements[1], possible_match_elements[0]):
                directed_graph.add_edge(possible_match_elements[1], possible_match_elements[0])

    return directed_graph

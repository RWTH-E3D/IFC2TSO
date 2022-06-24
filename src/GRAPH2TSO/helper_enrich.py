import networkx as nx
from ifcopenshell import geom
import numpy as np
import trimesh
from trimesh import proximity


def enrich_flow_directions(fd_json, import_graph):
    edge_set = set()
    undirected_graph = import_graph.to_undirected()
    for search_info in fd_json:
        search_edges = dfs_undirected(search_info, undirected_graph)
        edge_set.update(search_edges)

    return list(edge_set)


def dfs_undirected(search_info, undirected_graph):
    start = search_info['Source']
    if not start:
        edges = set()
        for new_edge in search_info['Add_Edge']:
            edges.add((new_edge[0], new_edge[1]))
        return edges
    targets = search_info['Target']
    no_edge = set()
    for edge in search_info['No_Edge']:
        no_edge.add((edge[0], edge[1]))

    path = set()
    edges = set()

    stack = [(None, start)]
    while stack:
        vertex = stack.pop()

        if vertex[1] in targets:
            continue

        path.add(vertex[1])

        if vertex[1] in undirected_graph:
            neigbhors = undirected_graph.neighbors(vertex[1])

            for neighbor in neigbhors:
                if (vertex[1], neighbor) not in no_edge:
                    if neighbor not in path:
                        edges.add((vertex[1], neighbor))
                        stack.append((vertex[1], neighbor))

    if search_info["Reverse"]:
        reverse_edges = set()
        for edge in edges:
            reverse_edges.add((edge[1], edge[0]))

        for new_edge in search_info['Add_Edge']:
            reverse_edges.add((new_edge[0], new_edge[1]))
        return reverse_edges
    else:

        for new_edge in search_info['Add_Edge']:
            edges.add((new_edge[0], new_edge[1]))

        return edges


def dfs_directed(search_info, directed_graph):
    start = search_info['Source']
    targets = search_info['Target']
    no_edge = set()
    for edge in search_info['No_Edge']:
        no_edge.add((edge[0], edge[1]))

    path = set()
    edges = set()

    stack = [(None, start)]
    while stack:
        vertex = stack.pop()

        if vertex[1] in targets:
            continue

        path.add(vertex[1])

        if vertex[1] in directed_graph:
            neigbhors = directed_graph.successors(vertex[1])

            for neighbor in neigbhors:
                if (vertex[1], neighbor) not in no_edge:
                    if neighbor not in path:
                        edges.add((vertex[1], neighbor))
                        stack.append((vertex[1], neighbor))

    if search_info["Reverse"]:
        reverse_edges = set()
        for edge in edges:
            reverse_edges.add((edge[1], edge[0]))

        for new_edge in search_info['Add_Edge']:
            reverse_edges.add((new_edge[0], new_edge[1]))
        return reverse_edges
    else:

        for new_edge in search_info['Add_Edge']:
            edges.add((new_edge[0], new_edge[1]))

        return edges


def create_enriched_directed_graph(direction_list, import_graph):
    enriched_graph = nx.DiGraph()

    for node in import_graph.nodes(data=True):
        enriched_graph.add_node(node[0], ifc_id=node[1]['ifc_id'], ifc_class=node[1]['ifc_class'], ifc_type=node[1]['ifc_type'], ifc_name=node[1]['ifc_name'],
                                ifc_description=node[1]['ifc_description'], ifc_system=node[1]['ifc_system'], ifc_position=node[1]['ifc_position'], elem_rds=node[1]['elem_rds'],
                                integrated_systems=node[1]['integrated_systems'], functional_systems=node[1]['functional_systems'], technical_systems=node[1]['technical_systems'],
                                additional_data=node[1]['additional_data'])

    if direction_list:
        for edge in direction_list:
            enriched_graph.add_edge(edge[0], edge[1])
    else:
        for edge in import_graph.edges():
            enriched_graph.add_edge(edge[0], edge[1])

    return enriched_graph


def calculate_spatial_representation(model):
    # Berechnung des Meshes der räumlichen Elemente
    rep_dict = dict()
    spatial_elements_list = model.by_type('IfcSpatialElement')

    settings = geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)

    for spatial_elem in spatial_elements_list:
        rep_dict[spatial_elem.GlobalId] = None
        if spatial_elem.Representation:

            shape = geom.create_shape(settings, spatial_elem)
            vertices = np.array(shape.geometry.verts).reshape(-1, 3)
            faces = np.array(shape.geometry.faces).reshape(-1, 3)
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            rep_dict[spatial_elem.GlobalId] = mesh

    return rep_dict


def analyse_spatial_structure(model, rep_dict):
    # Analyse der topologischen Struktur der räumlichen Entitäten
    spatial_info = []
    spatial_dict = dict()
    spatial_dict['All'] = dict()
    spatial_dict['IfcSite'] = dict()
    spatial_dict['IfcBuilding'] = dict()
    spatial_dict['IfcBuildingStorey'] = dict()
    spatial_dict['IfcSpace'] = dict()
    spatial_dict['Structure'] = dict()
    list_site = model.by_type('IfcSite')
    for ifc_site in list_site:
        tmp_dict = dict()
        site_globalid = ifc_site.GlobalId
        site_class = ifc_site.is_a()
        site_rep = rep_dict[site_globalid]
        tmp_dict[site_globalid] = dict()
        tmp_dict[site_globalid]['GlobalId'] = site_globalid
        tmp_dict[site_globalid]['Classification'] = site_class
        tmp_dict[site_globalid]['Mesh'] = site_rep
        tmp_dict[site_globalid]['Children'] = []

        spatial_dict['IfcSite'][site_globalid] = tmp_dict[site_globalid]
        spatial_dict['All'][site_globalid] = tmp_dict[site_globalid]

        list_aggregates_site = ifc_site.IsDecomposedBy
        list_building = []
        list_building_ids = []
        for aggregates_site in list_aggregates_site:
            tmp_list = aggregates_site.RelatedObjects
            for tmp in tmp_list:
                list_building.append(tmp)
                list_building_ids.append(tmp.GlobalId)

        spatial_dict['Structure'][site_globalid] = list_building_ids

        for ifc_building in list_building:
            tmp_dict_2 = dict()
            building_globalid = ifc_building.GlobalId
            building_class = ifc_building.is_a()
            building_rep = rep_dict[building_globalid]
            tmp_dict_2[building_globalid] = dict()
            tmp_dict_2[building_globalid]['GlobalId'] = building_globalid
            tmp_dict_2[building_globalid]['Classification'] = building_class
            tmp_dict_2[building_globalid]['Mesh'] = building_rep
            tmp_dict_2[building_globalid]['Children'] = []

            spatial_dict['IfcBuilding'][building_globalid] = tmp_dict_2[building_globalid]
            spatial_dict['All'][building_globalid] = tmp_dict_2[building_globalid]

            list_aggregates_building = ifc_building.IsDecomposedBy
            list_storey = []
            list_storey_ids = []
            for aggregates_building in list_aggregates_building:
                tmp_list = aggregates_building.RelatedObjects
                for tmp in tmp_list:
                    list_storey.append(tmp)
                    list_storey_ids.append(tmp.GlobalId)

            spatial_dict['Structure'][building_globalid] = list_storey_ids

            for ifc_storey in list_storey:
                tmp_dict_3 = dict()
                storey_globalid = ifc_storey.GlobalId
                storey_class = ifc_storey.is_a()
                storey_rep = rep_dict[storey_globalid]
                tmp_dict_3[storey_globalid] = dict()
                tmp_dict_3[storey_globalid]['GlobalId'] = storey_globalid
                tmp_dict_3[storey_globalid]['Classification'] = storey_class
                tmp_dict_3[storey_globalid]['Mesh'] = storey_rep
                tmp_dict_3[storey_globalid]['Children'] = []

                spatial_dict['IfcBuildingStorey'][storey_globalid] = tmp_dict_3[storey_globalid]
                spatial_dict['All'][storey_globalid] = tmp_dict_3[storey_globalid]

                list_aggregates_storeys = ifc_storey.IsDecomposedBy
                list_spaces = []
                list_spaces_ids = []
                for aggregates_storeys in list_aggregates_storeys:
                    tmp_list = aggregates_storeys.RelatedObjects
                    for tmp in tmp_list:
                        list_spaces.append(tmp)
                        list_spaces_ids.append(tmp.GlobalId)

                spatial_dict['Structure'][storey_globalid] = list_spaces_ids

                for ifc_space in list_spaces:
                    tmp_dict_4 = dict()
                    space_globalid = ifc_space.GlobalId
                    space_class = ifc_space.is_a()
                    space_rep = rep_dict[space_globalid]
                    tmp_dict_4[space_globalid] = dict()
                    tmp_dict_4[space_globalid]['GlobalId'] = space_globalid
                    tmp_dict_4[space_globalid]['Classification'] = space_class
                    tmp_dict_4[space_globalid]['Mesh'] = space_rep
                    tmp_dict_4[space_globalid]['Children'] = []

                    spatial_dict['IfcSpace'][space_globalid] = tmp_dict_4[space_globalid]
                    spatial_dict['All'][space_globalid] = tmp_dict_4[space_globalid]

                    spatial_dict['Structure'][space_globalid] = []

                    tmp_dict_3[storey_globalid]['Children'].append(tmp_dict_4)

                tmp_dict_2[building_globalid]['Children'].append(tmp_dict_3)

            tmp_dict[site_globalid]['Children'].append(tmp_dict_2)

        spatial_info.append(tmp_dict)

    return spatial_dict

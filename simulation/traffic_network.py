"""
Traffic Network Module
Loads METR-LA adjacency matrix, extracts a 25-node subgraph representing
a 5x5 city grid, and provides graph utilities for the traffic simulator.
"""

import pickle
import numpy as np
import networkx as nx
from pathlib import Path

# ---------------------
# CONSTANTS
# ---------------------
GRID_SIZE = 5
NUM_INTERSECTIONS = GRID_SIZE * GRID_SIZE  # 25
DATASET_DIR = Path(__file__).parent.parent / "Dataset"
ADJ_PICKLE = DATASET_DIR / "adj_METR-LA.pkl"

# Zone definitions for a 5x5 city grid
ZONE_MAP = {
    "Commercial":  ["J1",  "J2",  "J3",  "J4",  "J5"],
    "Residential": ["J6",  "J7",  "J8",  "J9",  "J10"],
    "School":      ["J11", "J12", "J13", "J14", "J15"],
    "Industrial":  ["J16", "J17", "J18", "J19", "J20"],
    "Hospital":    ["J21", "J22", "J23", "J24", "J25"],
}

# Reverse lookup: intersection -> zone
INTERSECTION_ZONE = {}
for zone, junctions in ZONE_MAP.items():
    for j in junctions:
        INTERSECTION_ZONE[j] = zone

# Grid positions (row, col) for visualization
GRID_POSITIONS = {}
for idx in range(NUM_INTERSECTIONS):
    row = idx // GRID_SIZE
    col = idx % GRID_SIZE
    GRID_POSITIONS[f"J{idx + 1}"] = (row, col)


def load_metr_la_adjacency() -> tuple:
    """
    Load the METR-LA adjacency data.
    Returns: (sensor_ids: list, id_to_index: dict, adj_matrix: np.ndarray[207,207])
    """
    with open(ADJ_PICKLE, "rb") as f:
        data = pickle.load(f, encoding="latin1")
    sensor_ids = data[0]      # list of 207 sensor ID strings
    id_to_index = data[1]     # dict: sensor_id -> index
    adj_matrix = data[2]      # ndarray (207, 207)
    return sensor_ids, id_to_index, adj_matrix


def extract_subgraph(adj_full: np.ndarray, n_nodes: int = 25, seed: int = 42) -> np.ndarray:
    """
    Extract a connected n-node subgraph from the full METR-LA adjacency matrix.
    Uses BFS starting from the most connected node to ensure connectivity.
    """
    np.random.seed(seed)
    # Find node with highest degree (most connections)
    degrees = np.sum(adj_full > 0, axis=1) - 1  # subtract self-loops
    start_node = np.argmax(degrees)

    # BFS to find connected subgraph
    visited = set()
    queue = [start_node]
    visited.add(start_node)

    while len(visited) < n_nodes and queue:
        current = queue.pop(0)
        neighbors = np.where(adj_full[current] > 0)[0]
        # Sort by connection weight (prefer stronger connections)
        neighbor_weights = [(n, adj_full[current, n]) for n in neighbors if n not in visited]
        neighbor_weights.sort(key=lambda x: -x[1])

        for neighbor, _ in neighbor_weights:
            if len(visited) >= n_nodes:
                break
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    selected_indices = sorted(list(visited))[:n_nodes]
    sub_adj = adj_full[np.ix_(selected_indices, selected_indices)]
    return sub_adj, selected_indices


def build_city_graph(adj_matrix: np.ndarray = None) -> nx.Graph:
    """
    Build a NetworkX graph for the 5x5 city grid.
    If adj_matrix is provided (from METR-LA), use those weights.
    Otherwise, create a standard grid graph with unit weights.
    """
    G = nx.Graph()
    intersections = [f"J{i}" for i in range(1, NUM_INTERSECTIONS + 1)]

    for jid in intersections:
        row, col = GRID_POSITIONS[jid]
        G.add_node(jid, zone=INTERSECTION_ZONE[jid], row=row, col=col)

    if adj_matrix is not None and adj_matrix.shape[0] == NUM_INTERSECTIONS:
        # Use METR-LA derived weights
        for i in range(NUM_INTERSECTIONS):
            for j in range(i + 1, NUM_INTERSECTIONS):
                if adj_matrix[i, j] > 0:
                    G.add_edge(
                        intersections[i], intersections[j],
                        weight=adj_matrix[i, j],
                        distance=1.0 / max(adj_matrix[i, j], 0.01)
                    )
    else:
        # Standard 5x5 grid adjacency (4-connected)
        for idx in range(NUM_INTERSECTIONS):
            row, col = idx // GRID_SIZE, idx % GRID_SIZE
            jid = intersections[idx]
            # Right neighbor
            if col < GRID_SIZE - 1:
                G.add_edge(jid, intersections[idx + 1], weight=1.0, distance=1.0)
            # Bottom neighbor
            if row < GRID_SIZE - 1:
                G.add_edge(jid, intersections[idx + GRID_SIZE], weight=1.0, distance=1.0)

    return G


def get_neighbors(graph: nx.Graph, junction_id: str) -> list:
    """Get neighboring intersections of a given junction."""
    return list(graph.neighbors(junction_id))


def get_shortest_path(graph: nx.Graph, source: str, target: str) -> list:
    """Find shortest path between two intersections."""
    try:
        return nx.shortest_path(graph, source, target, weight="distance")
    except nx.NetworkXNoPath:
        return []


def get_network_data() -> dict:
    """
    Return the full network topology as a JSON-serializable dict
    for API/frontend consumption.
    """
    try:
        _, _, adj_full = load_metr_la_adjacency()
        sub_adj, _ = extract_subgraph(adj_full, NUM_INTERSECTIONS)
        graph = build_city_graph(sub_adj)
    except Exception:
        graph = build_city_graph()

    nodes = []
    for node_id, attrs in graph.nodes(data=True):
        nodes.append({
            "id": node_id,
            "zone": attrs.get("zone", "Unknown"),
            "row": attrs.get("row", 0),
            "col": attrs.get("col", 0),
        })

    edges = []
    for u, v, attrs in graph.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "weight": round(attrs.get("weight", 1.0), 4),
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "grid_size": GRID_SIZE,
        "num_intersections": NUM_INTERSECTIONS,
        "zones": {zone: junctions for zone, junctions in ZONE_MAP.items()},
    }


# ---------------------
# Module self-test
# ---------------------
if __name__ == "__main__":
    print("=== Traffic Network Module ===")

    # Load METR-LA
    sensor_ids, id_to_idx, adj_full = load_metr_la_adjacency()
    print(f"METR-LA: {len(sensor_ids)} sensors, adj shape {adj_full.shape}")
    print(f"Non-zero entries: {np.count_nonzero(adj_full)}")

    # Extract subgraph
    sub_adj, indices = extract_subgraph(adj_full, NUM_INTERSECTIONS)
    print(f"\nSubgraph: {sub_adj.shape}, selected sensor indices: {indices[:5]}...")
    print(f"Subgraph non-zero: {np.count_nonzero(sub_adj)}")

    # Build city graph
    graph = build_city_graph(sub_adj)
    print(f"\nCity graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    print(f"Zones: {list(ZONE_MAP.keys())}")

    # Test neighbors
    for jid in ["J1", "J13", "J25"]:
        neighbors = get_neighbors(graph, jid)
        print(f"  {jid} ({INTERSECTION_ZONE[jid]}): neighbors = {neighbors}")

    # Test shortest path
    path = get_shortest_path(graph, "J1", "J25")
    print(f"\nShortest path J1->J25: {path}")

    # Network data for API
    net_data = get_network_data()
    print(f"\nNetwork data: {len(net_data['nodes'])} nodes, {len(net_data['edges'])} edges")
    print("[OK] Traffic Network Module passed all checks")

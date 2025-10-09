import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import json


def main():
    # Load data using pandas
    with open('electron_cascade_data.json', 'r') as f:
        data = json.load(f)

    # Extract network data
    network_data = data['network_topology']
    positions = network_data['node_positions']
    edges = network_data['edges']
    node_count = network_data['node_count']
    connectivity = network_data['connectivity']

    # Convert positions to DataFrame
    pos_df = pd.DataFrame.from_dict(positions, orient='index', columns=['x', 'y'])
    pos_df.index = pos_df.index.astype(int)

    # Convert edges to DataFrame
    edges_df = pd.DataFrame(edges, columns=['source', 'target'])

    # Create NetworkX graph
    G = nx.Graph()
    G.add_nodes_from(range(node_count))
    G.add_edges_from(edges)

    # Convert positions for networkx
    pos_dict = {i: [pos_df.loc[i, 'x'], pos_df.loc[i, 'y']] for i in range(node_count)}

    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: Full network topology
    nx.draw_networkx_nodes(G, pos_dict, node_color='lightblue',
                           node_size=30, alpha=0.7, ax=ax1)
    nx.draw_networkx_edges(G, pos_dict, edge_color='gray',
                           alpha=0.5, width=0.5, ax=ax1)
    ax1.set_title(f'Network Topology (N={node_count}, avg degree={connectivity:.1f})')
    ax1.set_aspect('equal')

    # Plot 2: Degree distribution
    degrees = pd.Series([G.degree(n) for n in G.nodes()])
    degrees.hist(bins=range(degrees.min(), degrees.max() + 2),
                 alpha=0.7, color='skyblue', edgecolor='black', ax=ax2)
    ax2.set_xlabel('Node Degree')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Degree Distribution')
    ax2.grid(True, alpha=0.3)

    # Plot 3: Node positions scatter with degree coloring
    scatter = ax3.scatter(pos_df['x'], pos_df['y'], c=degrees, cmap='viridis',
                          s=50, alpha=0.7)
    ax3.set_xlabel('X Position')
    ax3.set_ylabel('Y Position')
    ax3.set_title('Node Positions Colored by Degree')
    plt.colorbar(scatter, ax=ax3, label='Node Degree')

    # Plot 4: Distance vs connectivity analysis
    distances = []
    connected = []
    for i in range(node_count):
        for j in range(i + 1, node_count):
            dist = np.sqrt((pos_df.loc[i, 'x'] - pos_df.loc[j, 'x']) ** 2 +
                           (pos_df.loc[i, 'y'] - pos_df.loc[j, 'y']) ** 2)
            distances.append(dist)
            connected.append(1 if G.has_edge(i, j) else 0)

    # Create DataFrame for analysis
    dist_conn_df = pd.DataFrame({'distance': distances, 'connected': connected})

    # Bin the data for visualization
    dist_conn_df['distance_bin'] = pd.cut(dist_conn_df['distance'], bins=20)
    connectivity_prob = dist_conn_df.groupby('distance_bin')['connected'].mean()
    bin_centers = [interval.mid for interval in connectivity_prob.index]

    ax4.plot(bin_centers, connectivity_prob.values, 'ro-', linewidth=2, markersize=6)
    ax4.set_xlabel('Distance')
    ax4.set_ylabel('Connection Probability')
    ax4.set_title('Connection Probability vs Distance')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('network_topology_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Print network statistics
    print("Network Statistics:")
    print(f"Nodes: {node_count}")
    print(f"Edges: {G.number_of_edges()}")
    print(f"Average degree: {connectivity:.2f}")
    print(f"Density: {nx.density(G):.4f}")
    print(f"Is connected: {nx.is_connected(G)}")
    if nx.is_connected(G):
        print(f"Average shortest path: {nx.average_shortest_path_length(G):.2f}")


if __name__ == "__main__":
    main()

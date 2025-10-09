# Generate comprehensive biological analysis report with visualizations
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import numpy as np
import pandas as pd
from typing import Dict, List, Any
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

def generate_biological_report(oscillatory_network_analysis: Dict,
                             pathway_optimizations: Dict,
                             multi_scale_integration: Dict,
                             coordinate_visualizations: Dict,
                             biological_predictions: Dict,
                             validation_metrics: Dict) -> Dict:
    """
    Generate comprehensive biological analysis report with visualizations
    """
    print("Generating comprehensive biological analysis report...")
    
    # Initialize report generator
    report_generator = BiologicalReportGenerator()
    
    # Generate visualizations
    network_visualizations = report_generator.create_network_visualizations(oscillatory_network_analysis)
    optimization_visualizations = report_generator.create_optimization_visualizations(pathway_optimizations)
    coordinate_visualizations_enhanced = report_generator.enhance_coordinate_visualizations(coordinate_visualizations)
    validation_visualizations = report_generator.create_validation_visualizations(validation_metrics)
    
    # Generate summary statistics
    summary_statistics = report_generator.generate_summary_statistics(
        oscillatory_network_analysis, pathway_optimizations, multi_scale_integration,
        biological_predictions, validation_metrics
    )
    
    # Create interactive dashboard
    interactive_dashboard = report_generator.create_interactive_dashboard(
        network_visualizations, optimization_visualizations, 
        coordinate_visualizations_enhanced, validation_visualizations
    )
    
    # Generate written report
    written_report = report_generator.generate_written_report(
        summary_statistics, oscillatory_network_analysis, pathway_optimizations,
        multi_scale_integration, biological_predictions, validation_metrics
    )
    
    analysis_report = {
        'report_generator': report_generator,
        'network_visualizations': network_visualizations,
        'optimization_visualizations': optimization_visualizations,
        'coordinate_visualizations': coordinate_visualizations_enhanced,
        'validation_visualizations': validation_visualizations,
        'summary_statistics': summary_statistics,
        'interactive_dashboard': interactive_dashboard,
        'written_report': written_report,
        'report_metadata': {
            'generation_timestamp': pd.Timestamp.now(),
            'total_visualizations_created': (len(network_visualizations) + 
                                           len(optimization_visualizations) + 
                                           len(coordinate_visualizations_enhanced) + 
                                           len(validation_visualizations)),
            'report_completeness_score': report_generator.calculate_completeness_score(
                oscillatory_network_analysis, pathway_optimizations, validation_metrics
            )
        }
    }
    
    print(f"Biological analysis report complete:")
    print(f"  Total visualizations: {analysis_report['report_metadata']['total_visualizations_created']}")
    print(f"  Report completeness: {analysis_report['report_metadata']['report_completeness_score']:.3f}")
    
    return analysis_report

class BiologicalReportGenerator:
    """
    Comprehensive biological analysis report generator with visualizations
    """
    
    def __init__(self):
        self.figure_counter = 0
        self.color_palette = sns.color_palette("husl", 12)
        
    def create_network_visualizations(self, oscillatory_network_analysis: Dict) -> Dict:
        """Create network topology and oscillatory analysis visualizations"""
        visualizations = {}
        
        if 'bayesian_network' in oscillatory_network_analysis:
            # Bayesian network topology
            bayesian_net_fig = self.visualize_bayesian_network(
                oscillatory_network_analysis['bayesian_network']
            )
            visualizations['bayesian_network_topology'] = bayesian_net_fig
        
        if 'oscillatory_frequencies' in oscillatory_network_analysis:
            # Frequency distribution
            freq_dist_fig = self.visualize_frequency_distribution(
                oscillatory_network_analysis['oscillatory_frequencies']
            )
            visualizations['frequency_distribution'] = freq_dist_fig
        
        if 's_entropy_clusters' in oscillatory_network_analysis:
            # S-entropy clustering
            cluster_fig = self.visualize_s_entropy_clusters(
                oscillatory_network_analysis['s_entropy_clusters']
            )
            visualizations['s_entropy_clusters'] = cluster_fig
        
        if 'oscillatory_holes' in oscillatory_network_analysis:
            # Oscillatory holes analysis
            holes_fig = self.visualize_oscillatory_holes(
                oscillatory_network_analysis['oscillatory_holes']
            )
            visualizations['oscillatory_holes'] = holes_fig
        
        return visualizations
    
    def create_optimization_visualizations(self, pathway_optimizations: Dict) -> Dict:
        """Create pathway optimization visualizations"""
        visualizations = {}
        
        if 'optimization_results' in pathway_optimizations:
            # Optimization comparison
            opt_comparison_fig = self.visualize_optimization_comparison(
                pathway_optimizations['optimization_results']
            )
            visualizations['optimization_comparison'] = opt_comparison_fig
        
        if 'combined_optimization' in pathway_optimizations:
            # Combined optimization results
            combined_opt_fig = self.visualize_combined_optimization(
                pathway_optimizations['combined_optimization']
            )
            visualizations['combined_optimization'] = combined_opt_fig
        
        if 'pathway_recommendations' in pathway_optimizations:
            # Pathway recommendations
            recommendations_fig = self.visualize_pathway_recommendations(
                pathway_optimizations['pathway_recommendations']
            )
            visualizations['pathway_recommendations'] = recommendations_fig
        
        return visualizations
    
    def enhance_coordinate_visualizations(self, coordinate_visualizations: Dict) -> Dict:
        """Enhance coordinate space visualizations"""
        enhanced_visualizations = coordinate_visualizations.copy()
        
        # Add 3D S-entropy space visualization
        if 's_coordinates' in coordinate_visualizations:
            s_space_3d_fig = self.create_3d_s_entropy_visualization(
                coordinate_visualizations['s_coordinates']
            )
            enhanced_visualizations['s_entropy_3d_space'] = s_space_3d_fig
        
        # Add coordinate distribution analysis
        coord_dist_fig = self.visualize_coordinate_distributions(coordinate_visualizations)
        enhanced_visualizations['coordinate_distributions'] = coord_dist_fig
        
        return enhanced_visualizations
    
    def create_validation_visualizations(self, validation_metrics: Dict) -> Dict:
        """Create validation results visualizations"""
        visualizations = {}
        
        if 'consistency_analysis' in validation_metrics:
            # Cross-modal consistency
            consistency_fig = self.visualize_cross_modal_consistency(
                validation_metrics['consistency_analysis']
            )
            visualizations['cross_modal_consistency'] = consistency_fig
        
        if 'validation_report' in validation_metrics:
            # Overall validation summary
            validation_summary_fig = self.visualize_validation_summary(
                validation_metrics['validation_report']
            )
            visualizations['validation_summary'] = validation_summary_fig
        
        return visualizations
    
    def visualize_bayesian_network(self, bayesian_network: nx.DiGraph) -> plt.Figure:
        """Visualize Bayesian network topology"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Calculate layout
        try:
            pos = nx.spring_layout(bayesian_network, k=1, iterations=50)
        except:
            pos = nx.random_layout(bayesian_network)
        
        # Draw network
        nx.draw_networkx_nodes(bayesian_network, pos, ax=ax, 
                              node_color=self.color_palette[0], 
                              node_size=300, alpha=0.7)
        nx.draw_networkx_edges(bayesian_network, pos, ax=ax,
                              edge_color='gray', alpha=0.5, arrows=True)
        nx.draw_networkx_labels(bayesian_network, pos, ax=ax, font_size=8)
        
        ax.set_title('Oscillatory Bayesian Network Topology', fontsize=14, fontweight='bold')
        ax.axis('off')
        
        plt.tight_layout()
        return fig
    
    def visualize_frequency_distribution(self, frequencies: Dict) -> plt.Figure:
        """Visualize oscillatory frequency distribution"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        freq_values = list(frequencies.values())
        species_names = list(frequencies.keys())
        
        # Histogram of frequencies
        ax1.hist(freq_values, bins=20, color=self.color_palette[1], alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Oscillatory Frequency')
        ax1.set_ylabel('Count')
        ax1.set_title('Distribution of Oscillatory Frequencies')
        ax1.grid(True, alpha=0.3)
        
        # Top frequencies bar plot
        top_indices = np.argsort(freq_values)[-10:]
        top_species = [species_names[i] for i in top_indices]
        top_frequencies = [freq_values[i] for i in top_indices]
        
        y_pos = np.arange(len(top_species))
        ax2.barh(y_pos, top_frequencies, color=self.color_palette[2], alpha=0.7)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(top_species, fontsize=8)
        ax2.set_xlabel('Frequency')
        ax2.set_title('Top 10 Oscillatory Frequencies')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def visualize_s_entropy_clusters(self, s_entropy_clusters: List[List[str]]) -> plt.Figure:
        """Visualize S-entropy clustering results"""
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        
        # Cluster size distribution
        cluster_sizes = [len(cluster) for cluster in s_entropy_clusters]
        
        if cluster_sizes:
            ax.hist(cluster_sizes, bins=max(1, len(set(cluster_sizes))), 
                   color=self.color_palette[3], alpha=0.7, edgecolor='black')
            ax.set_xlabel('Cluster Size')
            ax.set_ylabel('Number of Clusters')
            ax.set_title(f'S-Entropy Cluster Size Distribution\n({len(s_entropy_clusters)} clusters total)')
            ax.grid(True, alpha=0.3)
            
            # Add statistics text
            stats_text = f"Mean size: {np.mean(cluster_sizes):.1f}\n"
            stats_text += f"Largest cluster: {max(cluster_sizes)}\n"
            stats_text += f"Total species clustered: {sum(cluster_sizes)}"
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        else:
            ax.text(0.5, 0.5, 'No clusters found', transform=ax.transAxes, 
                   ha='center', va='center', fontsize=16)
            ax.set_title('S-Entropy Clustering Results')
        
        plt.tight_layout()
        return fig
    
    def visualize_oscillatory_holes(self, oscillatory_holes: List[Dict]) -> plt.Figure:
        """Visualize oscillatory holes analysis"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        if oscillatory_holes:
            # Hole frequency distribution
            hole_frequencies = [hole['frequency'] for hole in oscillatory_holes]
            hole_strengths = [hole['hole_strength'] for hole in oscillatory_holes]
            
            ax1.scatter(hole_frequencies, hole_strengths, 
                       c=self.color_palette[4], alpha=0.6, s=50)
            ax1.set_xlabel('Frequency')
            ax1.set_ylabel('Hole Strength')
            ax1.set_title('Oscillatory Holes: Frequency vs Strength')
            ax1.grid(True, alpha=0.3)
            
            # Hole strength distribution
            ax2.hist(hole_strengths, bins=15, color=self.color_palette[5], 
                    alpha=0.7, edgecolor='black')
            ax2.set_xlabel('Hole Strength')
            ax2.set_ylabel('Count')
            ax2.set_title('Distribution of Oscillatory Hole Strengths')
            ax2.grid(True, alpha=0.3)
        else:
            for ax in [ax1, ax2]:
                ax.text(0.5, 0.5, 'No oscillatory holes data', 
                       transform=ax.transAxes, ha='center', va='center', fontsize=14)
        
        plt.tight_layout()
        return fig
    
    def visualize_optimization_comparison(self, optimization_results: Dict) -> plt.Figure:
        """Visualize optimization results comparison"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        if optimization_results:
            targets = list(optimization_results.keys())
            improvement_factors = [result.get('improvement_factor', 0) 
                                 for result in optimization_results.values()]
            optimization_scores = [result.get('optimization_score', 0) 
                                 for result in optimization_results.values()]
            
            # Improvement factors
            y_pos = np.arange(len(targets))
            ax1.barh(y_pos, improvement_factors, color=self.color_palette[6], alpha=0.7)
            ax1.set_yticks(y_pos)
            ax1.set_yticklabels(targets)
            ax1.set_xlabel('Improvement Factor')
            ax1.set_title('Optimization Improvement Factors')
            ax1.grid(True, alpha=0.3)
            
            # Optimization scores
            ax2.barh(y_pos, optimization_scores, color=self.color_palette[7], alpha=0.7)
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(targets)
            ax2.set_xlabel('Optimization Score')
            ax2.set_title('Optimization Scores')
            ax2.grid(True, alpha=0.3)
        else:
            for ax in [ax1, ax2]:
                ax.text(0.5, 0.5, 'No optimization results', 
                       transform=ax.transAxes, ha='center', va='center', fontsize=14)
        
        plt.tight_layout()
        return fig
    
    def visualize_combined_optimization(self, combined_optimization: Dict) -> plt.Figure:
        """Visualize combined optimization results"""
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        if 'optimization_balance' in combined_optimization:
            balance = combined_optimization['optimization_balance']
            
            # Pie chart of optimization balance
            labels = list(balance.keys())
            sizes = list(balance.values())
            colors = self.color_palette[:len(labels)]
            
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                             autopct='%1.1f%%', startangle=90)
            ax.set_title('Combined Optimization Balance')
            
            # Equal aspect ratio ensures that pie is drawn as a circle
            ax.axis('equal')
        else:
            ax.text(0.5, 0.5, 'No combined optimization data', 
                   transform=ax.transAxes, ha='center', va='center', fontsize=14)
        
        plt.tight_layout()
        return fig
    
    def visualize_pathway_recommendations(self, recommendations: List[Dict]) -> plt.Figure:
        """Visualize pathway recommendations"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        if recommendations:
            # Count recommendation types
            rec_types = [rec['type'] for rec in recommendations]
            type_counts = {}
            for rec_type in rec_types:
                type_counts[rec_type] = type_counts.get(rec_type, 0) + 1
            
            # Bar plot of recommendation types
            types = list(type_counts.keys())
            counts = list(type_counts.values())
            
            bars = ax.bar(types, counts, color=self.color_palette[8], alpha=0.7)
            ax.set_ylabel('Number of Recommendations')
            ax.set_title('Pathway Recommendations by Type')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}', ha='center', va='bottom')
        else:
            ax.text(0.5, 0.5, 'No pathway recommendations', 
                   transform=ax.transAxes, ha='center', va='center', fontsize=14)
        
        plt.tight_layout()
        return fig
    
    def create_3d_s_entropy_visualization(self, s_coordinates: Dict) -> go.Figure:
        """Create 3D S-entropy space visualization using Plotly"""
        if not s_coordinates:
            return go.Figure()
        
        # Extract coordinates
        species_names = list(s_coordinates.keys())
        coordinates = np.array(list(s_coordinates.values()))
        
        if coordinates.shape[1] >= 3:
            x = coordinates[:, 0]  # S_knowledge
            y = coordinates[:, 1]  # S_time
            z = coordinates[:, 2]  # S_entropy
            
            fig = go.Figure(data=[go.Scatter3d(
                x=x, y=y, z=z,
                mode='markers+text',
                marker=dict(
                    size=8,
                    color=z,  # Color by S_entropy
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="S_entropy")
                ),
                text=species_names[:20],  # Limit labels for readability
                textposition="top center",
                hovertemplate='<b>%{text}</b><br>' +
                             'S_knowledge: %{x:.3f}<br>' +
                             'S_time: %{y:.3f}<br>' +
                             'S_entropy: %{z:.3f}<br>' +
                             '<extra></extra>'
            )])
            
            fig.update_layout(
                title='3D S-Entropy Coordinate Space',
                scene=dict(
                    xaxis_title='S_knowledge',
                    yaxis_title='S_time',
                    zaxis_title='S_entropy'
                ),
                font=dict(size=12)
            )
        else:
            fig = go.Figure()
            fig.add_annotation(
                text="Insufficient dimensions for 3D visualization",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        return fig
    
    def visualize_coordinate_distributions(self, coordinate_visualizations: Dict) -> plt.Figure:
        """Visualize coordinate distributions across dimensions"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        axes = axes.ravel()
        
        coord_systems = ['genomic_coordinates', 'protein_coordinates', 
                        'metabolic_coordinates', 'circuit_coordinates']
        
        for i, coord_system in enumerate(coord_systems):
            ax = axes[i]
            
            if coord_system in coordinate_visualizations:
                coords = coordinate_visualizations[coord_system]
                if coords:
                    # Extract all coordinate values
                    all_values = []
                    for coord in coords.values():
                        if isinstance(coord, (list, np.ndarray)):
                            all_values.extend(coord)
                        else:
                            all_values.append(coord)
                    
                    if all_values:
                        ax.hist(all_values, bins=20, color=self.color_palette[i], 
                               alpha=0.7, edgecolor='black')
                        ax.set_xlabel('Coordinate Value')
                        ax.set_ylabel('Frequency')
                        ax.set_title(f'{coord_system.replace("_", " ").title()} Distribution')
                        ax.grid(True, alpha=0.3)
                    else:
                        ax.text(0.5, 0.5, 'No coordinate data', 
                               transform=ax.transAxes, ha='center', va='center')
                else:
                    ax.text(0.5, 0.5, 'No coordinate data', 
                           transform=ax.transAxes, ha='center', va='center')
            else:
                ax.text(0.5, 0.5, f'{coord_system} not available', 
                       transform=ax.transAxes, ha='center', va='center')
            
            ax.set_title(coord_system.replace('_', ' ').title())
        
        plt.tight_layout()
        return fig
    
    def visualize_cross_modal_consistency(self, consistency_analysis: Dict) -> plt.Figure:
        """Visualize cross-modal consistency analysis"""
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        
        if 'pairwise_consistency' in consistency_analysis:
            pairwise = consistency_analysis['pairwise_consistency']
            
            # Create heatmap
            pairs = list(pairwise.keys())
            values = list(pairwise.values())
            
            # Reshape for heatmap (simplified)
            coord_types = ['genomic', 'protein', 'metabolic', 'circuit']
            n_types = len(coord_types)
            consistency_matrix = np.zeros((n_types, n_types))
            
            for pair, value in pairwise.items():
                parts = pair.split('_')
                if len(parts) >= 2:
                    try:
                        i = coord_types.index(parts[0])
                        j = coord_types.index(parts[1])
                        consistency_matrix[i, j] = value
                        consistency_matrix[j, i] = value  # Symmetric
                    except ValueError:
                        continue
            
            # Fill diagonal with 1.0 (self-consistency)
            np.fill_diagonal(consistency_matrix, 1.0)
            
            im = ax.imshow(consistency_matrix, cmap='RdYlGn', vmin=0, vmax=1)
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Consistency Score')
            
            # Set ticks and labels
            ax.set_xticks(range(n_types))
            ax.set_yticks(range(n_types))
            ax.set_xticklabels(coord_types)
            ax.set_yticklabels(coord_types)
            
            # Add text annotations
            for i in range(n_types):
                for j in range(n_types):
                    text = ax.text(j, i, f'{consistency_matrix[i, j]:.2f}',
                                 ha="center", va="center", color="black", fontweight='bold')
            
            ax.set_title('Cross-Modal Consistency Matrix')
        else:
            ax.text(0.5, 0.5, 'No consistency analysis data', 
                   transform=ax.transAxes, ha='center', va='center', fontsize=14)
        
        plt.tight_layout()
        return fig
    
    def visualize_validation_summary(self, validation_report: Dict) -> plt.Figure:
        """Visualize validation summary"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        if 'component_scores' in validation_report:
            scores = validation_report['component_scores']
            
            # Bar plot of component scores
            components = list(scores.keys())
            score_values = list(scores.values())
            
            bars = ax1.bar(components, score_values, color=self.color_palette[9], alpha=0.7)
            ax1.set_ylabel('Score')
            ax1.set_title('Validation Component Scores')
            ax1.set_ylim(0, 1)
            ax1.tick_params(axis='x', rotation=45)
            ax1.grid(True, alpha=0.3)
            
            # Add threshold line
            ax1.axhline(y=0.8, color='red', linestyle='--', alpha=0.7, label='Threshold')
            ax1.legend()
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.2f}', ha='center', va='bottom')
        
        # Validation status pie chart
        if 'validation_summary' in validation_report:
            summary = validation_report['validation_summary']
            passed = summary.get('validations_passed', 0)
            total = summary.get('total_validations_performed', 4)
            failed = total - passed
            
            sizes = [passed, failed]
            labels = ['Passed', 'Failed']
            colors = ['lightgreen', 'lightcoral']
            
            ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.0f', startangle=90)
            ax2.set_title('Validation Status')
            ax2.axis('equal')
        
        plt.tight_layout()
        return fig
    
    def create_interactive_dashboard(self, network_vis: Dict, optimization_vis: Dict,
                                   coordinate_vis: Dict, validation_vis: Dict) -> Dict:
        """Create interactive dashboard combining all visualizations"""
        dashboard = {
            'network_visualizations': network_vis,
            'optimization_visualizations': optimization_vis,
            'coordinate_visualizations': coordinate_vis,
            'validation_visualizations': validation_vis,
            'dashboard_metadata': {
                'total_figures': (len(network_vis) + len(optimization_vis) + 
                                len(coordinate_vis) + len(validation_vis)),
                'interactive_figures': len([fig for fig in coordinate_vis.values() 
                                          if hasattr(fig, 'to_html')]),
                'static_figures': len([fig for fig in network_vis.values() 
                                     if hasattr(fig, 'savefig')])
            }
        }
        
        return dashboard
    
    def generate_summary_statistics(self, oscillatory_network: Dict, pathway_opt: Dict,
                                  multi_scale: Dict, predictions: Dict, validation: Dict) -> Dict:
        """Generate comprehensive summary statistics"""
        summary = {
            'network_analysis': {
                'total_species': oscillatory_network.get('summary', {}).get('species_analyzed', 0),
                'bayesian_edges': oscillatory_network.get('network_properties', {}).get('num_edges', 0),
                'oscillatory_clusters': oscillatory_network.get('summary', {}).get('num_s_entropy_clusters', 0),
                'pathway_coherence': oscillatory_network.get('pathway_coherence', 0.0)
            },
            'optimization_analysis': {
                'targets_optimized': len(pathway_opt.get('optimization_results', {})),
                'avg_improvement': pathway_opt.get('optimization_summary', {}).get('avg_optimization_score', 0.0),
                'viability_maintained': pathway_opt.get('optimization_summary', {}).get('viability_maintained', False)
            },
            'validation_analysis': {
                'overall_validity': validation.get('summary', {}).get('consistency_score', 0.0),
                'validation_passed': validation.get('overall_validity', False),
                'critical_issues': validation.get('validation_report', {}).get('validation_summary', {}).get('critical_issues', 0)
            }
        }
        
        return summary
    
    def generate_written_report(self, summary_stats: Dict, *analysis_components) -> str:
        """Generate written analysis report"""
        report = []
        report.append("# Comprehensive Biological Analysis Report\n")
        report.append("## Executive Summary\n")
        
        # Network analysis summary
        network_stats = summary_stats.get('network_analysis', {})
        report.append(f"### Network Analysis")
        report.append(f"- Total species analyzed: {network_stats.get('total_species', 0)}")
        report.append(f"- Bayesian network edges: {network_stats.get('bayesian_edges', 0)}")
        report.append(f"- S-entropy clusters identified: {network_stats.get('oscillatory_clusters', 0)}")
        report.append(f"- Pathway coherence score: {network_stats.get('pathway_coherence', 0.0):.3f}\n")
        
        # Optimization summary
        opt_stats = summary_stats.get('optimization_analysis', {})
        report.append(f"### Pathway Optimization")
        report.append(f"- Optimization targets: {opt_stats.get('targets_optimized', 0)}")
        report.append(f"- Average improvement score: {opt_stats.get('avg_improvement', 0.0):.3f}")
        report.append(f"- System viability maintained: {opt_stats.get('viability_maintained', False)}\n")
        
        # Validation summary
        val_stats = summary_stats.get('validation_analysis', {})
        report.append(f"### Validation Results")
        report.append(f"- Overall validity score: {val_stats.get('overall_validity', 0.0):.3f}")
        report.append(f"- Validation status: {'PASSED' if val_stats.get('validation_passed', False) else 'FAILED'}")
        report.append(f"- Critical issues identified: {val_stats.get('critical_issues', 0)}\n")
        
        report.append("## Detailed Analysis\n")
        report.append("Please refer to the generated visualizations for detailed analysis of:")
        report.append("- Oscillatory Bayesian network topology")
        report.append("- S-entropy coordinate clustering")
        report.append("- Pathway optimization results")
        report.append("- Cross-modal validation consistency")
        report.append("- Biological interpretability assessment\n")
        
        report.append("## Recommendations\n")
        if val_stats.get('validation_passed', False):
            report.append("✓ Analysis validation passed - results are reliable for biological interpretation")
        else:
            report.append("⚠ Analysis validation issues detected - review coordinate systems and data quality")
        
        if opt_stats.get('viability_maintained', False):
            report.append("✓ Pathway optimization maintained system viability")
        else:
            report.append("⚠ Pathway optimization may compromise system viability - validate carefully")
        
        return "\n".join(report)
    
    def calculate_completeness_score(self, *analysis_components) -> float:
        """Calculate report completeness score"""
        total_components = len(analysis_components)
        present_components = sum(1 for component in analysis_components if component)
        
        completeness = present_components / total_components if total_components > 0 else 0.0
        
        return completeness

# Usage example
if __name__ == "__main__":
    print("Biological Analysis Report Generator ready for use")
    print("Use generate_biological_report() to create comprehensive analysis reports")
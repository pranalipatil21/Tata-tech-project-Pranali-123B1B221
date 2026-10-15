"""Architecture Dependency Graph Visualization using NetworkX and Plotly."""
from typing import List, Optional
import networkx as nx
import plotly.graph_objects as go
from models.schemas import Dependency, SoftwareComponent

class DependencyGraphBuilder:
    """Constructs NetworkX directed graph and renders interactive Plotly visualizations."""

    def build_figure(
        self,
        components: List[SoftwareComponent],
        dependencies: List[Dependency]
    ) -> go.Figure:
        """
        Builds an interactive Plotly figure representing the AUTOSAR component dependency graph.
        Handles candidate vs reviewed statuses, node attributes, and empty states.
        """
        # Handle empty case gracefully
        if not components and not dependencies:
            fig = go.Figure()
            fig.update_layout(
                title="AUTOSAR Component Dependency Graph",
                annotations=[{
                    "text": "No Software Components or Dependencies extracted yet.<br>Upload an AUTOSAR HLD PDF and run Architecture Analysis.",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 15, "color": "#888888"}
                }],
                xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
                yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                height=500
            )
            return fig

        # Build NetworkX DiGraph
        G = nx.DiGraph()

        # Add component nodes
        for c in components:
            G.add_node(c.name, description=c.description, page=c.source_page)

        # Add dependency edges
        for d in dependencies:
            if d.source_component and d.target_component:
                # Add nodes if not already registered
                if d.source_component not in G:
                    G.add_node(d.source_component, description="Discovered in dependency", page=d.source_page)
                if d.target_component not in G:
                    G.add_node(d.target_component, description="Discovered in dependency", page=d.source_page)

                G.add_edge(
                    d.source_component,
                    d.target_component,
                    description=d.description,
                    dep_type=d.dependency_type,
                    status=d.status,
                    evidence=d.evidence,
                    page=d.source_page
                )

        if len(G.nodes) == 0:
            fig = go.Figure()
            fig.update_layout(title="AUTOSAR Component Dependency Graph (Empty)")
            return fig

        # Compute layout positions using spring layout
        pos = nx.spring_layout(G, k=1.2, iterations=60, seed=42)

        # 1. Edge traces (distinguish Candidate vs Reviewed)
        candidate_edge_x = []
        candidate_edge_y = []
        reviewed_edge_x = []
        reviewed_edge_y = []

        edge_mid_x = []
        edge_mid_y = []
        edge_hover_text = []

        for u, v, data in G.edges(data=True):
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            status = data.get("status", "Candidate")

            if status == "Reviewed":
                reviewed_edge_x.extend([x0, x1, None])
                reviewed_edge_y.extend([y0, y1, None])
            else:
                candidate_edge_x.extend([x0, x1, None])
                candidate_edge_y.extend([y0, y1, None])

            # Edge midpoint for hover tooltip
            mx = (x0 + x1) / 2.0
            my = (y0 + y1) / 2.0
            edge_mid_x.append(mx)
            edge_mid_y.append(my)
            edge_hover_text.append(
                f"<b>{u} → {v}</b><br>"
                f"Type: {data.get('dep_type', 'Functional')}<br>"
                f"Status: {status}<br>"
                f"Description: {data.get('description', '')}<br>"
                f"Evidence: {data.get('evidence', '')[:100]}... (p.{data.get('page', '?')})"
            )

        candidate_trace = go.Scatter(
            x=candidate_edge_x,
            y=candidate_edge_y,
            line=dict(width=1.8, color="#F59E0B", dash="dot"),
            hoverinfo="none",
            mode="lines",
            name="Candidate Dependency"
        )

        reviewed_trace = go.Scatter(
            x=reviewed_edge_x,
            y=reviewed_edge_y,
            line=dict(width=2.5, color="#10B981"),
            hoverinfo="none",
            mode="lines",
            name="Reviewed Dependency"
        )

        edge_midpoint_trace = go.Scatter(
            x=edge_mid_x,
            y=edge_mid_y,
            mode="markers",
            marker=dict(size=8, color="#64748B", symbol="arrow-bar-down"),
            text=edge_hover_text,
            hoverinfo="text",
            showlegend=False
        )

        # 2. Node trace
        node_x = []
        node_y = []
        node_labels = []
        node_hover = []

        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_labels.append(node)
            deg_in = G.in_degree(node)
            deg_out = G.out_degree(node)
            desc = G.nodes[node].get("description", "Not specified")
            node_hover.append(
                f"<b>SWC: {node}</b><br>"
                f"Incoming Dependencies: {deg_in}<br>"
                f"Outgoing Dependencies: {deg_out}<br>"
                f"Description: {desc[:120]}..."
            )

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=node_labels,
            textposition="top center",
            hoverinfo="text",
            hovertext=node_hover,
            marker=dict(
                size=24,
                color="#2563EB",
                line=dict(width=2, color="#1E40AF")
            ),
            name="Software Component"
        )

        fig = go.Figure(
            data=[candidate_trace, reviewed_trace, edge_midpoint_trace, node_trace],
            layout=go.Layout(
                title="AUTOSAR Component Dependency Architecture Graph",
                title_x=0.5,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode="closest",
                margin=dict(b=20, l=20, r=20, t=50),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor="#F8FAFC",
                paper_bgcolor="#FFFFFF",
                height=560
            )
        )

        return fig

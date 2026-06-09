use serde::{Deserialize, Serialize};

const RT: f64 = 2.478; // kJ/mol at 298K

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Node {
    pub id: usize,
    pub name: String,
    pub species_id: String,
    pub compartment: String,
    pub concentration: f64,
    pub mu0: f64,
    pub mu: f64,
    pub boundary: bool,
}

impl Node {
    pub fn new(name: &str, mu: f64, concentration: f64) -> Self {
        let mu_actual = mu + RT * concentration.max(1e-10).ln();
        Self {
            id: 0,
            name: name.to_string(),
            species_id: name.to_string(),
            compartment: "cytoplasm".to_string(),
            concentration,
            mu0: mu,
            mu: mu_actual,
            boundary: false,
        }
    }

    pub fn with_compartment(mut self, compartment: &str) -> Self {
        self.compartment = compartment.to_string();
        self
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Edge {
    pub id: usize,
    pub name: String,
    pub reaction_id: String,
    pub src: usize,
    pub dst: usize,
    pub rate: f64,
    pub conductance: f64,
    pub delta_g: f64,
}

impl Edge {
    pub fn new(src: usize, dst: usize, conductance: f64) -> Self {
        Self {
            id: 0,
            name: format!("e{}_{}", src, dst),
            reaction_id: format!("r{}_{}", src, dst),
            src,
            dst,
            rate: conductance,
            conductance,
            delta_g: 0.0,
        }
    }

    pub fn with_rate(mut self, rate: f64, src_concentration: f64) -> Self {
        self.rate = rate;
        self.conductance = rate * src_concentration / RT;
        self
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Circuit {
    pub nodes: Vec<Node>,
    pub edges: Vec<Edge>,
    pub compartments: Vec<String>,
    pub model_id: String,
}

impl Circuit {
    pub fn new() -> Self {
        Self {
            nodes: Vec::new(),
            edges: Vec::new(),
            compartments: Vec::new(),
            model_id: String::new(),
        }
    }

    pub fn add_node(&mut self, mut node: Node) -> usize {
        let id = self.nodes.len();
        node.id = id;
        if !self.compartments.contains(&node.compartment) {
            self.compartments.push(node.compartment.clone());
        }
        self.nodes.push(node);
        id
    }

    pub fn add_edge(&mut self, mut edge: Edge) -> usize {
        let id = self.edges.len();
        edge.id = id;
        edge.delta_g = self.nodes[edge.src].mu - self.nodes[edge.dst].mu;
        self.edges.push(edge);
        id
    }

    pub fn num_nodes(&self) -> usize {
        self.nodes.len()
    }

    pub fn num_edges(&self) -> usize {
        self.edges.len()
    }

    pub fn demo_glycolysis() -> Self {
        let mut c = Circuit::new();
        c.model_id = "demo-glycolysis".to_string();

        let glucose = c.add_node(Node::new("Glucose", -917.0, 5.0));
        let g6p = c.add_node(Node::new("G6P", -1760.0, 0.083));
        let f6p = c.add_node(Node::new("F6P", -1755.0, 0.014));
        let fbp = c.add_node(Node::new("FBP", -2600.0, 0.031));
        let g3p = c.add_node(Node::new("G3P", -1290.0, 0.14));
        let bpg13 = c.add_node(Node::new("BPG13", -2356.0, 0.001));
        let pg3 = c.add_node(Node::new("PG3", -1515.0, 0.1));
        let pg2 = c.add_node(Node::new("PG2", -1510.0, 0.03));
        let pep = c.add_node(Node::new("PEP", -1263.0, 0.023));
        let pyruvate = c.add_node(Node::new("Pyruvate", -472.0, 0.051));

        c.add_edge(Edge::new(glucose, g6p, 464.1));
        c.add_edge(Edge::new(g6p, f6p, 3.35));
        c.add_edge(Edge::new(f6p, fbp, 0.85));
        c.add_edge(Edge::new(fbp, g3p, 1.0));
        c.add_edge(Edge::new(g3p, bpg13, 11.3));
        c.add_edge(Edge::new(bpg13, pg3, 0.12));
        c.add_edge(Edge::new(pg3, pg2, 7.27));
        c.add_edge(Edge::new(pg2, pep, 1.21));
        c.add_edge(Edge::new(pep, pyruvate, 4.64));

        c.add_edge(Edge::new(g6p, glucose, 0.67));
        c.add_edge(Edge::new(f6p, g6p, 0.45));
        c.add_edge(Edge::new(g3p, fbp, 1.69));
        c.add_edge(Edge::new(pg3, bpg13, 10.1));
        c.add_edge(Edge::new(pg2, pg3, 1.82));
        c.add_edge(Edge::new(pep, pg2, 0.65));

        c
    }
}

impl Default for Circuit {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Perturbation {
    pub edge_idx: usize,
    pub factor: f64,
}

impl Perturbation {
    pub fn new(edge_idx: usize, factor: f64) -> Self {
        Self { edge_idx, factor }
    }
}

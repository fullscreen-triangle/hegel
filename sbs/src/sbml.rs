use quick_xml::events::Event;
use quick_xml::Reader;

use crate::circuit::{Circuit, Edge, Node};

const RT: f64 = 2.478;

#[derive(Debug, Clone)]
struct SbmlSpecies {
    id: String,
    name: String,
    compartment: String,
    initial_concentration: f64,
    boundary: bool,
}

#[derive(Debug, Clone)]
struct SbmlReaction {
    id: String,
    name: String,
    reactants: Vec<String>,
    products: Vec<String>,
    reversible: bool,
}

pub fn parse_sbml(xml: &str) -> Result<Circuit, String> {
    let mut reader = Reader::from_str(xml);
    reader.config_mut().trim_text(true);

    let mut species: Vec<SbmlSpecies> = Vec::new();
    let mut reactions: Vec<SbmlReaction> = Vec::new();
    let mut current_reaction: Option<SbmlReaction> = None;
    let mut in_list_of_reactants = false;
    let mut in_list_of_products = false;
    let mut model_id = String::new();

    let mut buf = Vec::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(ref e)) | Ok(Event::Empty(ref e)) => {
                let local_name = String::from_utf8_lossy(e.local_name().as_ref()).to_string();
                match local_name.as_str() {
                    "model" => {
                        for attr in e.attributes().flatten() {
                            if attr.key.as_ref() == b"id" {
                                model_id =
                                    String::from_utf8_lossy(&attr.value).to_string();
                            }
                        }
                    }
                    "species" => {
                        let mut sp = SbmlSpecies {
                            id: String::new(),
                            name: String::new(),
                            compartment: "default".to_string(),
                            initial_concentration: 1.0,
                            boundary: false,
                        };
                        for attr in e.attributes().flatten() {
                            let key = String::from_utf8_lossy(attr.key.as_ref()).to_string();
                            let val = String::from_utf8_lossy(&attr.value).to_string();
                            match key.as_str() {
                                "id" => sp.id = val,
                                "name" => sp.name = val,
                                "compartment" => sp.compartment = val,
                                "initialConcentration" => {
                                    sp.initial_concentration =
                                        val.parse().unwrap_or(1.0);
                                }
                                "boundaryCondition" => {
                                    sp.boundary = val == "true";
                                }
                                _ => {}
                            }
                        }
                        if sp.name.is_empty() {
                            sp.name = sp.id.clone();
                        }
                        species.push(sp);
                    }
                    "reaction" => {
                        let mut rx = SbmlReaction {
                            id: String::new(),
                            name: String::new(),
                            reactants: Vec::new(),
                            products: Vec::new(),
                            reversible: false,
                        };
                        for attr in e.attributes().flatten() {
                            let key = String::from_utf8_lossy(attr.key.as_ref()).to_string();
                            let val = String::from_utf8_lossy(&attr.value).to_string();
                            match key.as_str() {
                                "id" => rx.id = val,
                                "name" => rx.name = val,
                                "reversible" => rx.reversible = val == "true",
                                _ => {}
                            }
                        }
                        current_reaction = Some(rx);
                    }
                    "listOfReactants" => in_list_of_reactants = true,
                    "listOfProducts" => in_list_of_products = true,
                    "speciesReference" => {
                        if let Some(ref mut rx) = current_reaction {
                            for attr in e.attributes().flatten() {
                                if attr.key.as_ref() == b"species" {
                                    let sp_ref =
                                        String::from_utf8_lossy(&attr.value).to_string();
                                    if in_list_of_reactants {
                                        rx.reactants.push(sp_ref);
                                    } else if in_list_of_products {
                                        rx.products.push(sp_ref);
                                    }
                                }
                            }
                        }
                    }
                    _ => {}
                }
            }
            Ok(Event::End(ref e)) => {
                let local_name = String::from_utf8_lossy(e.local_name().as_ref()).to_string();
                match local_name.as_str() {
                    "reaction" => {
                        if let Some(rx) = current_reaction.take() {
                            reactions.push(rx);
                        }
                    }
                    "listOfReactants" => in_list_of_reactants = false,
                    "listOfProducts" => in_list_of_products = false,
                    _ => {}
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => return Err(format!("XML parse error: {}", e)),
            _ => {}
        }
        buf.clear();
    }

    let mut circuit = Circuit::new();
    circuit.model_id = model_id;

    let mut species_idx = std::collections::HashMap::new();
    for sp in &species {
        let node = Node::new(&sp.name, 0.0, sp.initial_concentration)
            .with_compartment(&sp.compartment);
        let idx = circuit.add_node(node);
        species_idx.insert(sp.id.clone(), idx);
    }

    for rx in &reactions {
        for reactant_id in &rx.reactants {
            for product_id in &rx.products {
                if let (Some(&src), Some(&dst)) =
                    (species_idx.get(reactant_id), species_idx.get(product_id))
                {
                    let src_conc = circuit.nodes[src].concentration;
                    let conductance = 1.0 * src_conc / RT;
                    circuit.add_edge(Edge::new(src, dst, conductance));

                    if rx.reversible {
                        let dst_conc = circuit.nodes[dst].concentration;
                        let rev_conductance = 1.0 * dst_conc / RT;
                        circuit.add_edge(Edge::new(dst, src, rev_conductance));
                    }
                }
            }
        }
    }

    Ok(circuit)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_minimal_sbml() {
        let xml = r#"<?xml version="1.0" encoding="UTF-8"?>
        <sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" version="1">
          <model id="test">
            <listOfSpecies>
              <species id="A" name="A" compartment="c" initialConcentration="1.0"/>
              <species id="B" name="B" compartment="c" initialConcentration="0.5"/>
            </listOfSpecies>
            <listOfReactions>
              <reaction id="r1" reversible="false">
                <listOfReactants><speciesReference species="A"/></listOfReactants>
                <listOfProducts><speciesReference species="B"/></listOfProducts>
              </reaction>
            </listOfReactions>
          </model>
        </sbml>"#;

        let circuit = parse_sbml(xml).unwrap();
        assert_eq!(circuit.num_nodes(), 2);
        assert_eq!(circuit.num_edges(), 1);
    }
}

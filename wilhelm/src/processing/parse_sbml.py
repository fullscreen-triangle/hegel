# Parse SBML to extract core biological network components
import libsbml
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET

def extract_molecular_species(sbml_file: str) -> Dict[str, Dict]:
    """Extract all molecular species from SBML file"""
    try:
        document = libsbml.readSBMLFromFile(sbml_file)
        if document.getNumErrors() > 0:
            print(f"SBML parsing errors: {document.getNumErrors()}")
            
        model = document.getModel()
        if not model:
            raise ValueError("No model found in SBML file")
            
        species_data = {}
        
        for species in model.getListOfSpecies():
            species_id = species.getId()
            species_data[species_id] = {
                'id': species_id,
                'name': species.getName() if species.getName() else species_id,
                'compartment': species.getCompartment(),
                'initial_concentration': species.getInitialConcentration(),
                'initial_amount': species.getInitialAmount(),
                'substance_units': species.getSubstanceUnits(),
                'has_only_substance_units': species.getHasOnlySubstanceUnits(),
                'boundary_condition': species.getBoundaryCondition(),
                'constant': species.getConstant(),
                'conversion_factor': species.getConversionFactor()
            }
            
        return species_data
        
    except Exception as e:
        print(f"Error extracting species: {e}")
        return {}

def extract_reaction_networks(sbml_file: str) -> Dict[str, Dict]:
    """Extract reaction networks and kinetic information"""
    try:
        document = libsbml.readSBMLFromFile(sbml_file)
        model = document.getModel()
        
        reaction_data = {}
        
        for reaction in model.getListOfReactions():
            reaction_id = reaction.getId()
            
            # Extract reactants
            reactants = []
            for reactant in reaction.getListOfReactants():
                reactants.append({
                    'species': reactant.getSpecies(),
                    'stoichiometry': reactant.getStoichiometry(),
                    'constant': reactant.getConstant()
                })
            
            # Extract products
            products = []
            for product in reaction.getListOfProducts():
                products.append({
                    'species': product.getSpecies(),
                    'stoichiometry': product.getStoichiometry(),
                    'constant': product.getConstant()
                })
            
            # Extract modifiers
            modifiers = []
            for modifier in reaction.getListOfModifiers():
                modifiers.append({
                    'species': modifier.getSpecies()
                })
            
            # Extract kinetic law
            kinetic_law = None
            if reaction.getKineticLaw():
                klaw = reaction.getKineticLaw()
                kinetic_law = {
                    'formula': klaw.getFormula() if klaw.getFormula() else None,
                    'parameters': {}
                }
                
                # Extract local parameters
                for param in klaw.getListOfParameters():
                    kinetic_law['parameters'][param.getId()] = {
                        'value': param.getValue(),
                        'units': param.getUnits()
                    }
            
            reaction_data[reaction_id] = {
                'id': reaction_id,
                'name': reaction.getName() if reaction.getName() else reaction_id,
                'reversible': reaction.getReversible(),
                'fast': reaction.getFast(),
                'reactants': reactants,
                'products': products,
                'modifiers': modifiers,
                'kinetic_law': kinetic_law,
                'compartment': reaction.getCompartment()
            }
            
        return reaction_data
        
    except Exception as e:
        print(f"Error extracting reactions: {e}")
        return {}

def extract_kinetic_parameters(sbml_file: str) -> Dict[str, Dict]:
    """Extract global kinetic parameters"""
    try:
        document = libsbml.readSBMLFromFile(sbml_file)
        model = document.getModel()
        
        parameter_data = {}
        
        for parameter in model.getListOfParameters():
            param_id = parameter.getId()
            parameter_data[param_id] = {
                'id': param_id,
                'name': parameter.getName() if parameter.getName() else param_id,
                'value': parameter.getValue(),
                'units': parameter.getUnits(),
                'constant': parameter.getConstant()
            }
            
        return parameter_data
        
    except Exception as e:
        print(f"Error extracting parameters: {e}")
        return {}

def extract_cellular_compartments(sbml_file: str) -> Dict[str, Dict]:
    """Extract cellular compartments"""
    try:
        document = libsbml.readSBMLFromFile(sbml_file)
        model = document.getModel()
        
        compartment_data = {}
        
        for compartment in model.getListOfCompartments():
            comp_id = compartment.getId()
            compartment_data[comp_id] = {
                'id': comp_id,
                'name': compartment.getName() if compartment.getName() else comp_id,
                'spatial_dimensions': compartment.getSpatialDimensions(),
                'size': compartment.getSize(),
                'units': compartment.getUnits(),
                'outside': compartment.getOutside(),
                'constant': compartment.getConstant()
            }
            
        return compartment_data
        
    except Exception as e:
        print(f"Error extracting compartments: {e}")
        return {}

def extract_regulatory_rules(sbml_file: str) -> Dict[str, Dict]:
    """Extract regulatory rules (assignment rules, rate rules, algebraic rules)"""
    try:
        document = libsbml.readSBMLFromFile(sbml_file)
        model = document.getModel()
        
        rules_data = {
            'assignment_rules': {},
            'rate_rules': {},
            'algebraic_rules': {}
        }
        
        # Extract assignment rules
        for rule in model.getListOfRules():
            if rule.getTypeCode() == libsbml.SBML_ASSIGNMENT_RULE:
                rule_id = f"assignment_{rule.getVariable()}"
                rules_data['assignment_rules'][rule_id] = {
                    'variable': rule.getVariable(),
                    'formula': rule.getFormula(),
                    'units': rule.getUnits() if hasattr(rule, 'getUnits') else None
                }
            elif rule.getTypeCode() == libsbml.SBML_RATE_RULE:
                rule_id = f"rate_{rule.getVariable()}"
                rules_data['rate_rules'][rule_id] = {
                    'variable': rule.getVariable(),
                    'formula': rule.getFormula(),
                    'units': rule.getUnits() if hasattr(rule, 'getUnits') else None
                }
            elif rule.getTypeCode() == libsbml.SBML_ALGEBRAIC_RULE:
                rule_id = f"algebraic_{len(rules_data['algebraic_rules'])}"
                rules_data['algebraic_rules'][rule_id] = {
                    'formula': rule.getFormula(),
                    'units': rule.getUnits() if hasattr(rule, 'getUnits') else None
                }
                
        return rules_data
        
    except Exception as e:
        print(f"Error extracting rules: {e}")
        return {'assignment_rules': {}, 'rate_rules': {}, 'algebraic_rules': {}}

def parse_sbml_file(sbml_file: str) -> Dict[str, Any]:
    """
    Main function to parse SBML file and extract all components
    Returns the sbml_components dictionary structure
    """
    print(f"Parsing SBML file: {sbml_file}")
    
    sbml_components = {
        'species': extract_molecular_species(sbml_file),
        'reactions': extract_reaction_networks(sbml_file), 
        'parameters': extract_kinetic_parameters(sbml_file),
        'compartments': extract_cellular_compartments(sbml_file),
        'rules': extract_regulatory_rules(sbml_file)
    }
    
    # Add summary statistics
    sbml_components['summary'] = {
        'num_species': len(sbml_components['species']),
        'num_reactions': len(sbml_components['reactions']),
        'num_parameters': len(sbml_components['parameters']),
        'num_compartments': len(sbml_components['compartments']),
        'num_assignment_rules': len(sbml_components['rules']['assignment_rules']),
        'num_rate_rules': len(sbml_components['rules']['rate_rules']),
        'num_algebraic_rules': len(sbml_components['rules']['algebraic_rules'])
    }
    
    print(f"SBML parsing complete:")
    print(f"  Species: {sbml_components['summary']['num_species']}")
    print(f"  Reactions: {sbml_components['summary']['num_reactions']}")
    print(f"  Parameters: {sbml_components['summary']['num_parameters']}")
    print(f"  Compartments: {sbml_components['summary']['num_compartments']}")
    
    return sbml_components

def calculate_molecular_properties(sbml_components: Dict) -> Dict:
    """Calculate additional molecular properties for analysis"""
    properties = {}
    
    # Calculate molecular connectivity
    species_connectivity = {}
    for species_id in sbml_components['species']:
        connections = 0
        for reaction_id, reaction in sbml_components['reactions'].items():
            # Count as reactant
            for reactant in reaction['reactants']:
                if reactant['species'] == species_id:
                    connections += 1
            # Count as product  
            for product in reaction['products']:
                if product['species'] == species_id:
                    connections += 1
            # Count as modifier
            for modifier in reaction['modifiers']:
                if modifier['species'] == species_id:
                    connections += 1
        
        species_connectivity[species_id] = connections
    
    properties['species_connectivity'] = species_connectivity
    
    # Calculate reaction complexity
    reaction_complexity = {}
    for reaction_id, reaction in sbml_components['reactions'].items():
        complexity = (
            len(reaction['reactants']) + 
            len(reaction['products']) + 
            len(reaction['modifiers'])
        )
        reaction_complexity[reaction_id] = complexity
    
    properties['reaction_complexity'] = reaction_complexity
    
    # Calculate network density
    total_species = len(sbml_components['species'])
    total_reactions = len(sbml_components['reactions'])
    
    if total_species > 0:
        properties['network_density'] = total_reactions / total_species
    else:
        properties['network_density'] = 0.0
    
    return properties

def validate_sbml_components(sbml_components: Dict) -> Dict:
    """Validate parsed SBML components for consistency"""
    validation_results = {
        'is_valid': True,
        'warnings': [],
        'errors': []
    }
    
    # Check for missing species referenced in reactions
    all_species_ids = set(sbml_components['species'].keys())
    
    for reaction_id, reaction in sbml_components['reactions'].items():
        # Check reactants
        for reactant in reaction['reactants']:
            if reactant['species'] not in all_species_ids:
                validation_results['errors'].append(
                    f"Reaction {reaction_id} references unknown species: {reactant['species']}"
                )
                validation_results['is_valid'] = False
        
        # Check products
        for product in reaction['products']:
            if product['species'] not in all_species_ids:
                validation_results['errors'].append(
                    f"Reaction {reaction_id} references unknown species: {product['species']}"
                )
                validation_results['is_valid'] = False
        
        # Check modifiers
        for modifier in reaction['modifiers']:
            if modifier['species'] not in all_species_ids:
                validation_results['errors'].append(
                    f"Reaction {reaction_id} references unknown species: {modifier['species']}"
                )
                validation_results['is_valid'] = False
    
    # Check for orphaned species (not involved in any reaction)
    involved_species = set()
    for reaction in sbml_components['reactions'].values():
        for reactant in reaction['reactants']:
            involved_species.add(reactant['species'])
        for product in reaction['products']:
            involved_species.add(product['species'])
        for modifier in reaction['modifiers']:
            involved_species.add(modifier['species'])
    
    orphaned_species = all_species_ids - involved_species
    if orphaned_species:
        validation_results['warnings'].append(
            f"Found {len(orphaned_species)} orphaned species not involved in reactions"
        )
    
    return validation_results

# Usage example and testing function
if __name__ == "__main__":
    # Example usage (would need actual SBML file)
    # sbml_components = parse_sbml_file("example_model.xml")
    # properties = calculate_molecular_properties(sbml_components)
    # validation = validate_sbml_components(sbml_components)
    print("SBML parser module ready for use")
    print("Use parse_sbml_file(filename) to parse SBML files")
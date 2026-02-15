//! Cellular Partition Framework Demo
//!
//! Demonstrates the core concepts:
//! - S-entropy coordinates
//! - Ternary encoding (position = trajectory)
//! - Constraint satisfaction
//! - Backward completion
//! - Categorical apertures

use cellular_partition::apertures::{
    analyze_traversal, carbonic_anhydrase_ii, atp_synthase, k_channel, EnzymeLibrary,
};
use cellular_partition::completion::BackwardCompletion;
use cellular_partition::constraints::{
    enzymatic_constraints, ApertureConstraint, ChargeNeutrality,
    CategoricalCoherence, ConstraintSet, Constraint,
};
use cellular_partition::primitives::{compose, project, rotate, reflect, reverse};
use cellular_partition::s_entropy::SEntropyCoordinate;
use cellular_partition::ternary::{TritString, TernaryTree};

fn main() {
    println!("{}", "=".repeat(70));
    println!("CELLULAR PARTITION FRAMEWORK DEMO");
    println!("Observation = Computation = Process");
    println!("{}", "=".repeat(70));

    demo_s_entropy();
    demo_ternary();
    demo_constraints();
    demo_completion();
    demo_apertures();
    demo_primitives();

    println!("\n{}", "=".repeat(70));
    println!("DEMO COMPLETE");
    println!("{}", "=".repeat(70));
}

fn demo_s_entropy() {
    println!("\n[1] S-ENTROPY COORDINATES");
    println!("{}", "-".repeat(50));

    let origin = SEntropyCoordinate::origin();
    let center = SEntropyCoordinate::center();
    let max = SEntropyCoordinate::max_entropy();

    println!("Origin: {}", origin);
    println!("Center: {}", center);
    println!("Maximum entropy: {}", max);

    // Distance calculations
    let d1 = origin.categorical_distance(&max);
    let d2 = center.categorical_distance(&max);

    println!("\nCategorical distances (independent of spatial position):");
    println!("  d(origin, max) = {:.2}", d1);
    println!("  d(center, max) = {:.2}", d2);

    // Trit conversion
    let k_dominant = SEntropyCoordinate::new(0.8, 0.1, 0.1);
    let t_dominant = SEntropyCoordinate::new(0.1, 0.8, 0.1);
    let e_dominant = SEntropyCoordinate::new(0.1, 0.1, 0.8);

    println!("\nAxis-dominant coordinates -> trits:");
    println!("  {} -> trit {}", k_dominant, k_dominant.to_trit());
    println!("  {} -> trit {}", t_dominant, t_dominant.to_trit());
    println!("  {} -> trit {}", e_dominant, e_dominant.to_trit());
}

fn demo_ternary() {
    println!("\n[2] TERNARY ENCODING (Position = Trajectory)");
    println!("{}", "-".repeat(50));

    let trit = TritString::new("012012012").unwrap();
    println!("TritString: {}", trit);
    println!("Length: {}", trit.len());
    println!("Trit counts: {:?}", trit.trit_counts());
    println!("Is balanced: {}", trit.is_balanced(0.1));
    println!("Coherence: {:.3}", trit.coherence());

    // Pattern search
    println!("\nPattern search for '012':");
    println!("  Contains: {}", trit.contains_pattern("012"));
    println!("  Count: {}", trit.count_pattern("012"));

    // Categorical distance
    let a = TritString::new("000").unwrap();
    let b = TritString::new("222").unwrap();
    println!("\nCategorical distance:");
    println!("  d({}, {}) = {}", a, b, a.categorical_distance(&b));

    // Enumeration
    let all_2 = TernaryTree::enumerate_all(2);
    println!("\nAll 2-trit strings: {:?}",
        all_2.iter().map(|t| t.to_string_repr()).collect::<Vec<_>>());
}

fn demo_constraints() {
    println!("\n[3] CONSTRAINT SATISFACTION");
    println!("{}", "-".repeat(50));

    let good = TritString::new("012012012012").unwrap();
    let bad = TritString::new("000222000222").unwrap();

    println!("Good trajectory: {}", good);
    println!("Bad trajectory:  {}", bad);

    // Individual constraints
    let cn = ChargeNeutrality::default();
    let cc = CategoricalCoherence::default();

    println!("\nCharge Neutrality:");
    println!("  Good: {}", cn.satisfied(&good));
    println!("  Bad:  {}", cn.satisfied(&bad));

    println!("\nCategorical Coherence (R > 0.7):");
    println!("  Good: {} (R = {:.3})", cc.satisfied(&good), good.coherence());
    println!("  Bad:  {} (R = {:.3})", cc.satisfied(&bad), bad.coherence());

    // Enzymatic constraints
    let enzyme_cs = enzymatic_constraints("012");
    println!("\nEnzymatic constraints (with aperture '012'):");
    println!("  Good: {}", enzyme_cs.satisfied(&good));
    for (name, satisfied) in enzyme_cs.satisfaction_report(&good) {
        println!("    {}: {}", name, satisfied);
    }
}

fn demo_completion() {
    println!("\n[4] BACKWARD COMPLETION (O(k*m) complexity)");
    println!("{}", "-".repeat(50));

    let mut constraints = ConstraintSet::new();
    constraints.add(ApertureConstraint::new("012"));

    let mut completer = BackwardCompletion::new(constraints, 12);

    let initial = TritString::new("000").unwrap();
    let final_state = TritString::new("222").unwrap();

    println!("Initial: {}", initial);
    println!("Final:   {}", final_state);
    println!("Aperture: 012");
    println!("Target length: 12");

    let results = completer.complete_through_aperture(
        &initial,
        &final_state,
        "012",
        Some(12),
    );

    let stats = completer.stats();

    println!("\nResults:");
    println!("  Valid trajectories: {}", results.len());
    println!("  Trajectories explored: {}", stats.total_trajectories_explored);
    println!("  Constraint checks: {}", stats.constraint_checks);
    println!("  Pruned branches: {}", stats.pruned_branches);
    println!("  Time: {:.3} ms", stats.computation_time_ns as f64 / 1e6);

    if let Some(first) = results.first() {
        println!("\nFirst valid trajectory: {}", first.trajectory);
    }
}

fn demo_apertures() {
    println!("\n[5] CATEGORICAL APERTURES (Enzymes)");
    println!("{}", "-".repeat(50));

    // Carbonic Anhydrase II
    let ca2 = carbonic_anhydrase_ii();
    println!("{}:", ca2.name);
    println!("  Center: {}", ca2.center);
    println!("  Width: {}", ca2.width);
    println!("  Pattern: {}", ca2.pattern);
    println!("  Selectivity: {:.0}", ca2.selectivity());

    // Trajectory through CA II
    let trajectory = TritString::new("000012222").unwrap();
    if let Some(result) = analyze_traversal(&trajectory, &ca2) {
        println!("\nTraversal analysis for {}:", trajectory);
        println!("  Position: {}", result.traversal_position);
        println!("  Categorical distance: {}", result.categorical_distance);
        println!("  Direct distance: {}", result.direct_distance);
        println!("  Catalytic efficiency: {:.2}x", result.catalytic_efficiency);
    }

    // K+ channel
    let kch = k_channel();
    println!("\n{}:", kch.name);
    println!("  Selectivity: {:.0} (K+ over Na+)", kch.selectivity());
    println!("  Pattern: {} (frequency matching)", kch.pattern);

    // ATP synthase
    let atps = atp_synthase();
    println!("\n{}:", atps.name);
    println!("  Pattern: {} (three 120-degree rotations)", atps.pattern);
    println!("  Geometry: {:?}", atps.geometry);

    // Enzyme library
    let lib = EnzymeLibrary::standard();
    println!("\nEnzyme library: {} enzymes", lib.len());
}

fn demo_primitives() {
    println!("\n[6] CATEGORICAL PRIMITIVES");
    println!("{}", "-".repeat(50));

    // Project
    let coord = SEntropyCoordinate::new(0.8, 0.2, 0.1);
    let projected = project(&coord, 6);
    println!("Project {} depth 6 -> {}", coord, projected);

    // Compose
    let first = TritString::new("012").unwrap();
    let second = TritString::new("120").unwrap();
    let composed = compose(&first, &second);
    println!("\nCompose {} + {} -> {}", first, second, composed);

    // Transformations
    let traj = TritString::new("012").unwrap();
    println!("\nTransformations on {}:", traj);
    println!("  Reverse: {}", reverse(&traj));
    println!("  Rotate:  {}", rotate(&traj));
    println!("  Reflect: {}", reflect(&traj));
}

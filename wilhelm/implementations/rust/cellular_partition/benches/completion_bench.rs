//! Benchmarks for backward completion algorithm

use cellular_partition::completion::BackwardCompletion;
use cellular_partition::constraints::{ApertureConstraint, ConstraintSet};
use cellular_partition::ternary::TritString;
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};

fn bench_completion(c: &mut Criterion) {
    let mut group = c.benchmark_group("backward_completion");

    let substrate = TritString::new("000").unwrap();
    let product = TritString::new("222").unwrap();

    for length in [9, 12, 15].iter() {
        group.bench_with_input(
            BenchmarkId::new("aperture_012", length),
            length,
            |b, &length| {
                let mut constraints = ConstraintSet::new();
                constraints.add(ApertureConstraint::new("012"));

                b.iter(|| {
                    let mut completer = BackwardCompletion::new(constraints.clone(), 20);
                    completer.complete_through_aperture(
                        black_box(&substrate),
                        black_box(&product),
                        "012",
                        Some(length),
                    )
                });
            },
        );
    }

    group.finish();
}

fn bench_trit_operations(c: &mut Criterion) {
    let mut group = c.benchmark_group("trit_operations");

    let traj = TritString::new("012012012012").unwrap();

    group.bench_function("categorical_distance", |b| {
        let other = TritString::new("222000111222").unwrap();
        b.iter(|| {
            black_box(&traj).categorical_distance(black_box(&other))
        });
    });

    group.bench_function("coherence", |b| {
        b.iter(|| {
            black_box(&traj).coherence()
        });
    });

    group.bench_function("pattern_count", |b| {
        b.iter(|| {
            black_box(&traj).count_pattern("012")
        });
    });

    group.finish();
}

fn bench_constraint_checking(c: &mut Criterion) {
    let mut group = c.benchmark_group("constraints");

    use cellular_partition::constraints::{
        ChargeNeutrality, EnergyConservation, CategoricalCoherence,
    };

    let traj = TritString::new("012012012012").unwrap();

    group.bench_function("charge_neutrality", |b| {
        let cn = ChargeNeutrality::default();
        b.iter(|| {
            cn.satisfied(black_box(&traj))
        });
    });

    group.bench_function("energy_conservation", |b| {
        let ec = EnergyConservation::default();
        b.iter(|| {
            ec.satisfied(black_box(&traj))
        });
    });

    group.bench_function("categorical_coherence", |b| {
        let cc = CategoricalCoherence::default();
        b.iter(|| {
            cc.satisfied(black_box(&traj))
        });
    });

    group.finish();
}

criterion_group!(
    benches,
    bench_completion,
    bench_trit_operations,
    bench_constraint_checking
);

criterion_main!(benches);

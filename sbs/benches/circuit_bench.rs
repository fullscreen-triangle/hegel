use criterion::{black_box, criterion_group, criterion_main, Criterion};
use sbs::circuit::{Circuit, Perturbation};
use sbs::entropy::compute_s_entropy;
use sbs::metrics::extract_metrics;
use sbs::solver::Solver;

fn bench_glycolysis_solve(c: &mut Criterion) {
    let circuit = Circuit::demo_glycolysis();
    c.bench_function("glycolysis_solve", |b| {
        b.iter(|| {
            let solver = Solver::new(black_box(circuit.clone()));
            solver.solve()
        })
    });
}

fn bench_glycolysis_perturbed(c: &mut Criterion) {
    let circuit = Circuit::demo_glycolysis();
    let pert = vec![Perturbation::new(0, 0.1)];
    c.bench_function("glycolysis_perturbed", |b| {
        b.iter(|| {
            let solver = Solver::new(black_box(circuit.clone()))
                .with_perturbations(black_box(pert.clone()));
            solver.solve()
        })
    });
}

fn bench_s_entropy_computation(c: &mut Criterion) {
    let circuit = Circuit::demo_glycolysis();
    c.bench_function("s_entropy_compute", |b| {
        b.iter(|| compute_s_entropy(black_box(&circuit), black_box(&[])))
    });
}

fn bench_metrics_extraction(c: &mut Criterion) {
    let circuit = Circuit::demo_glycolysis();
    c.bench_function("metrics_extract", |b| {
        b.iter(|| extract_metrics(black_box(&circuit), black_box(&[])))
    });
}

criterion_group!(
    benches,
    bench_glycolysis_solve,
    bench_glycolysis_perturbed,
    bench_s_entropy_computation,
    bench_metrics_extraction,
);
criterion_main!(benches);

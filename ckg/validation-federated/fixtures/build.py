"""Local fixtures. Nothing here touches the network.

The datasets are small and hand-checkable on purpose: every figure the
validation reports can be recomputed by reading the fixture, which is what
makes a disagreement between the code and the paper visible rather than
arguable.

Several fixtures are built to realise a specific counterexample:

  cardinality_pair()      prop:cardinality-uninformative -- equal output size,
                          retentions differing by a predicted factor
  pairwise_families()     prop:pairwise-insufficient -- identical pairwise
                          retentions, differing end-to-end surviving fractions
  budget_trap()           prop:necessary-not-sufficient -- Bud >= sum c_i and
                          still a refusal
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from hfq import (GraphPatternAdapter, LookupAdapter, MapAdapter,
                 OntologyAdapter, Registry, TranslationMap, featureset)

SNAPSHOT = "fixture-v3"


# ---------------------------------------------------------------------------
# A small chemistry-shaped world
# ---------------------------------------------------------------------------

#: A class hierarchy. CHEBI:1 is the root; two levels beneath it.
PARENTS: Dict[str, List[str]] = {
    "CHEBI:2": ["CHEBI:1"],
    "CHEBI:3": ["CHEBI:1"],
    "CHEBI:4": ["CHEBI:1"],
    "CHEBI:5": ["CHEBI:2"],
    "CHEBI:6": ["CHEBI:2"],
    "CHEBI:7": ["CHEBI:3"],
    "CHEBI:8": ["CHEBI:4"],
    "CHEBI:9": ["CHEBI:4"],
    "CHEBI:10": ["CHEBI:9"],
}

LABELS = {k: "compound-" + k.split(":")[1] for k in PARENTS}

#: Reaction triples, keyed on KEGG identifiers.
TRIPLES: List[Tuple[str, str, str]] = [
    ("KEGG:C2", "consumes", "RHEA:100"),
    ("KEGG:C2", "consumes", "RHEA:101"),
    ("KEGG:C5", "consumes", "RHEA:102"),
    ("KEGG:C7", "consumes", "RHEA:103"),
    ("KEGG:C7", "consumes", "RHEA:104"),
    ("KEGG:C9", "consumes", "RHEA:105"),
    ("KEGG:C2", "produces", "RHEA:200"),
    ("KEGG:C5", "produces", "RHEA:201"),
    ("RHEA:100", "catalysed_by", "EC:1.1.1.1"),
    ("RHEA:101", "catalysed_by", "EC:1.1.1.2"),
    ("RHEA:102", "catalysed_by", "EC:2.7.1.1"),
    ("RHEA:103", "catalysed_by", "EC:1.1.1.1"),
    ("RHEA:104", "catalysed_by", "EC:3.1.3.1"),
    ("RHEA:105", "catalysed_by", "EC:2.7.1.1"),
]

PATHS = {
    "reactions_consuming": "consumes",
    "reactions_producing": "produces",
    "enzyme_of": "catalysed_by",
    "participants_of": "consumes",
}

#: Flat records for the lookup adapter.
RECORDS = {
    "EC:1.1.1.1": {"name": "alcohol dehydrogenase", "organisms": 12},
    "EC:1.1.1.2": {"name": "alcohol dehydrogenase (NADP+)", "organisms": 4},
    "EC:2.7.1.1": {"name": "hexokinase", "organisms": 31},
    "EC:3.1.3.1": {"name": "alkaline phosphatase", "organisms": 7},
}

LINKS = {
    "pathway": {
        "EC:1.1.1.1": ["MAP:00010"],
        "EC:2.7.1.1": ["MAP:00010", "MAP:00051"],
        "EC:3.1.3.1": ["MAP:00790"],
    }
}


# ---------------------------------------------------------------------------
# Translation maps
# ---------------------------------------------------------------------------

#: Partial, non-functional, non-injective -- all three, as def:map allows.
#: 7 of the 9 CHEBI descendants have a KEGG counterpart: retention 7/9.
CHEBI_KEGG = TranslationMap(
    "chebi2kegg", "CHEBI", "KEGG",
    {
        "CHEBI:2": ("KEGG:C2",),
        "CHEBI:3": ("KEGG:C3",),
        "CHEBI:4": ("KEGG:C4",),
        "CHEBI:5": ("KEGG:C5",),
        "CHEBI:7": ("KEGG:C7",),
        "CHEBI:9": ("KEGG:C9",),
        "CHEBI:10": ("KEGG:C9", "KEGG:C10"),   # non-functional
        # CHEBI:6 and CHEBI:8 are outside the domain.
    },
)

#: A lossy second stage, so a chain has something to lose.
KEGG_RHEA = TranslationMap(
    "kegg2rhea", "KEGG", "RHEA",
    {
        "KEGG:C2": ("RHEA:100",),
        "KEGG:C5": ("RHEA:102",),
        "KEGG:C9": ("RHEA:105",),
        # C3, C4, C7, C10 are outside the domain.
    },
)

#: Total on the same source set, for the (V11) collapse: making every map
#: total drives the route divergence to zero.
CHEBI_KEGG_TOTAL = TranslationMap(
    "chebi2kegg_total", "CHEBI", "KEGG",
    dict(CHEBI_KEGG.pairs, **{"CHEBI:6": ("KEGG:C6",), "CHEBI:8": ("KEGG:C8",)}),
)


# ---------------------------------------------------------------------------
# prop:cardinality-uninformative
# ---------------------------------------------------------------------------


def cardinality_pair() -> Tuple[TranslationMap, TranslationMap, List[str]]:
    """Two maps with equal output cardinality and unequal retention.

    Over S = {a1..a8}:
      mu_hi keeps 8 of 8 and sends each to one image  -> r = 1.00, a = 1.0
      mu_lo keeps 2 of 8 and sends each to four       -> r = 0.25, a = 4.0
    Both produce |mu(S)| = 8. The product r*a agrees; neither factor does.
    """
    s = ["X:a%d" % i for i in range(1, 9)]
    hi = TranslationMap("mu_hi", "X", "Y",
                        {u: ("Y:h%d" % i,) for i, u in enumerate(s, 1)})
    lo = TranslationMap(
        "mu_lo", "X", "Y",
        {s[0]: tuple("Y:l%d" % i for i in range(1, 5)),
         s[1]: tuple("Y:l%d" % i for i in range(5, 9))},
    )
    return hi, lo, s


# ---------------------------------------------------------------------------
# prop:pairwise-insufficient
# ---------------------------------------------------------------------------


def pairwise_families() -> Tuple[
        Tuple[TranslationMap, TranslationMap],
        Tuple[TranslationMap, TranslationMap],
        List[str]]:
    """Two chains with identical pairwise retentions, different coverage.

    Over S = {u1..u4}, both chains have r_1 = r_2 = 1/2.

      aligned:   mu keeps {u1,u2}; nu keeps the images of BOTH  -> rho = 1/2
      staggered: mu keeps {u1,u2}; nu keeps the image of u1 and
                 an element that is not an image at all          -> rho = 1/4

    The pairwise figures cannot distinguish them, which is the proposition.
    """
    s = ["U:u%d" % i for i in range(1, 5)]

    mu = TranslationMap("mu", "U", "V",
                        {s[0]: ("V:v1",), s[1]: ("V:v2",)})

    # domain {v1,v2}: 2 of the 4 V-elements the chain could present
    nu_aligned = TranslationMap("nu_aligned", "V", "W",
                                {"V:v1": ("W:w1",), "V:v2": ("W:w2",)})
    # domain {v1,v3}: still 2 of 4, but v3 is never produced by mu
    nu_stagger = TranslationMap("nu_stagger", "V", "W",
                                {"V:v1": ("W:w1",), "V:v3": ("W:w3",)})
    return (mu, nu_aligned), (mu, nu_stagger), s


# ---------------------------------------------------------------------------
# prop:necessary-not-sufficient
# ---------------------------------------------------------------------------


def budget_trap() -> Registry:
    """Two steps, c_1 = c_2 = 1, Bud = 2, and a refusal all the same.

    Step 1 costs 1 and returns a payload of cardinality 3; step 2's cost is
    linear in its input, so it needs 3 and only 1 remains. The obstruction is
    that c_2 is a minimum over inputs and the realised input is not the
    minimising one.
    """
    reg = Registry()
    reg.register(OntologyAdapter(
        name="tiny_onto", namespace="CHEBI", capabilities=frozenset(),
        parents={"CHEBI:2": ["CHEBI:1"], "CHEBI:3": ["CHEBI:1"],
                 "CHEBI:4": ["CHEBI:1"]},
        labels={}, snapshot=SNAPSHOT))
    reg.register(GraphPatternAdapter(
        name="tiny_graph", namespace="RHEA", capabilities=frozenset(),
        triples=[("CHEBI:2", "consumes", "RHEA:1")],
        paths={"reactions_consuming": "consumes"}, snapshot=SNAPSHOT))
    return reg


# ---------------------------------------------------------------------------
# Registry assembly
# ---------------------------------------------------------------------------


def build_registry(batch: bool = False) -> Registry:
    """The main registry: four adapter kinds over the world above."""
    reg = Registry()

    reg.register(OntologyAdapter(
        name="chebi", namespace="CHEBI", capabilities=frozenset(),
        parents=dict(PARENTS), labels=dict(LABELS), snapshot=SNAPSHOT))

    reg.register(GraphPatternAdapter(
        name="rhea", namespace="RHEA", capabilities=frozenset(),
        triples=list(TRIPLES), paths=dict(PATHS),
        prefixes={"rh": "http://example.invalid/rhea/"}, snapshot=SNAPSHOT))

    # Declares {lookup, link} and NOT pattern. That restriction is what makes
    # thm:static fire on a plan asking it for a join.
    cap = featureset("lookup", "link", "batch") if batch else frozenset()
    reg.register(LookupAdapter(
        name="enzdb", namespace="EC", capabilities=cap,
        records=dict(RECORDS), links={k: dict(v) for k, v in LINKS.items()},
        snapshot=SNAPSHOT))

    return reg


def build_maps() -> MapAdapter:
    m = MapAdapter(name="maps", namespace="map", capabilities=frozenset(),
                   maps={
                       "chebi2kegg": CHEBI_KEGG,
                       "kegg2rhea": KEGG_RHEA,
                       "chebi2kegg_total": CHEBI_KEGG_TOTAL,
                   })
    m.snapshot = SNAPSHOT
    return m


# ---------------------------------------------------------------------------
# The paper's two listings, run verbatim
# ---------------------------------------------------------------------------
#
# lst:plan and lst:routes name sources CHEBI/RHEA/KEGG and maps ec_to_kegg,
# chebi_to_kegg, chebi_to_inchikey, inchikey_to_kegg. Those names are part of
# the printed text, so the fixture supplies them rather than the plans being
# edited to match the fixture -- the point of running them is that the listings
# execute as written.

#: EC -> KEGG. 3 of 4 enzymes have a counterpart: retention 0.75, above the
#: 0.6 that lst:plan declares, so the plan runs to completion.
EC_KEGG = TranslationMap(
    "ec_to_kegg", "EC", "KEGG",
    {
        "EC:1.1.1.1": ("KEGG:E1",),
        "EC:2.7.1.1": ("KEGG:E2",),
        "EC:3.1.3.1": ("KEGG:E3",),
        # EC:1.1.1.2 is outside the domain.
    },
)

#: The two routes of lst:routes. The direct route keeps 7 of 9; the indirect
#: route loses a different element at each of its two stages, so the routes
#: diverge without either being wrong -- thm:route-extent(b).
CHEBI_INCHI = TranslationMap(
    "chebi_to_inchikey", "CHEBI", "INCHI",
    {k: ("INCHI:" + k.split(":")[1],) for k in PARENTS if k != "CHEBI:3"},
)

INCHI_KEGG = TranslationMap(
    "inchikey_to_kegg", "INCHI", "KEGG",
    {
        "INCHI:2": ("KEGG:C2",),
        "INCHI:4": ("KEGG:C4",),
        "INCHI:5": ("KEGG:C5",),
        "INCHI:6": ("KEGG:C6",),   # the direct route misses this one
        "INCHI:7": ("KEGG:C7",),
        "INCHI:9": ("KEGG:C9",),
        # INCHI:8 and INCHI:10 are outside the domain.
    },
)

#: The KEGG side of lst:plan: a lookup source keyed on the EC->KEGG images.
KEGG_RECORDS = {
    "KEGG:E1": {"name": "adh"},
    "KEGG:E2": {"name": "hk"},
    "KEGG:E3": {"name": "alp"},
}

KEGG_LINKS = {
    "pathway": {
        "KEGG:E1": ["MAP:00010"],
        "KEGG:E2": ["MAP:00010", "MAP:00051"],
        "KEGG:E3": ["MAP:00790"],
    }
}


def build_paper_registry() -> Tuple[Registry, MapAdapter]:
    """Sources and maps under the names the paper's listings use."""
    reg = Registry()

    # CHEBI:35238 is the root lst:plan asks for; it sits above the acids.
    parents = dict(PARENTS)
    parents["CHEBI:1"] = ["CHEBI:35238"]

    reg.register(OntologyAdapter(
        name="CHEBI", namespace="CHEBI", capabilities=frozenset(),
        parents=parents, labels=dict(LABELS), snapshot=SNAPSHOT))

    # lst:plan passes ChEBI identifiers straight to RHEA -- no translation step
    # intervenes -- so this fixture is keyed on ChEBI, as a real reaction store
    # cross-referencing ChEBI would be. TRIPLES above is keyed on KEGG and
    # serves the plans that translate first; both keyings are needed, and
    # which one a step meets is exactly what the plan's step order decides.
    chebi_triples = [(s.replace("KEGG:C", "CHEBI:"), p, o)
                     for s, p, o in TRIPLES if s.startswith("KEGG:C")]
    chebi_triples += [(s, p, o) for s, p, o in TRIPLES
                      if s.startswith("RHEA:")]
    reg.register(GraphPatternAdapter(
        name="RHEA", namespace="RHEA", capabilities=frozenset(),
        triples=chebi_triples, paths=dict(PATHS), snapshot=SNAPSHOT))

    # lst:plan supplies a bound set to this step, so def:wellcap requires both
    # `bind` and (the step being a from-step with non-empty beta) `batch`. A
    # source that cannot accept a bound set cannot serve that plan at all;
    # declaring them here is the adapter author asserting the REST endpoint
    # takes a key list, which rem:honesty-assumption leaves unverified.
    reg.register(LookupAdapter(
        name="KEGG", namespace="KEGG",
        capabilities=featureset("lookup", "link", "bind", "batch"),
        records=dict(KEGG_RECORDS),
        links={k: dict(v) for k, v in KEGG_LINKS.items()},
        snapshot=SNAPSHOT))

    maps = MapAdapter(name="maps", namespace="map", capabilities=frozenset(),
                      maps={
                          "ec_to_kegg": EC_KEGG,
                          "chebi_to_kegg": CHEBI_KEGG,
                          "chebi_to_inchikey": CHEBI_INCHI,
                          "inchikey_to_kegg": INCHI_KEGG,
                      })
    maps.snapshot = SNAPSHOT
    return reg, maps
